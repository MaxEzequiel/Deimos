from decimal import Decimal

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.audit import audit
from .models import MonthlyPayment, PaymentMovement
from .services import reverse_payment
from memberships.management_views import member_list as subscription_list


@login_required
@permission_required(["pagos.change_monthlypayment", "pagos.view_monthlypayment"], raise_exception=True)
@require_http_methods(["GET", "POST"])
def pay_subscription(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
    membership = getattr(user, "membership", None)
    person = getattr(user, "person", None)
    plan = (membership.plan if membership else None) or (person.plan if person else None)
    if not plan or (membership and membership.status != "active") or not plan.base_price or plan.base_price <= 0:
        messages.error(request, "La suscripción debe tener un plan activo con monto positivo.")
        return redirect("subscription_list")
    from .forms import MemberPaymentForm
    from .services import register_member_payment
    period = timezone.localdate().replace(day=1)
    charge = MonthlyPayment.objects.filter(member=user, period=period).first()
    form = MemberPaymentForm(request.POST if request.method == "POST" else None, member=user,
        initial={"period": period, "amount": charge.amount if charge else plan.base_price})
    if request.method == "POST" and form.is_valid():
        expected = MonthlyPayment.objects.filter(member=user, period=form.cleaned_data["period"]).first()
        expected_amount = expected.amount if expected else plan.base_price
        if form.cleaned_data["amount"] != expected_amount:
            form.add_error("amount", "El monto debe coincidir con el precio de la cuota o del plan.")
            return render(request, "payments/pay_subscription.html", {"form": form, "member": user, "plan": plan})
        try:
            with transaction.atomic():
                payment = register_member_payment(user, form.cleaned_data, request.user)
                audit(request, "CREATE", f"Cobro de suscripción {payment.pk}: {payment.amount}")
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect("payment_history")
    return render(request, "payments/pay_subscription.html", {"form": form, "member": user, "plan": plan})


@login_required
@require_http_methods(["GET"])
def payment_history(request):
    movements = PaymentMovement.objects.select_related(
        "charge__member", "recorded_by", "reversal_of", "reversal"
    )
    if not request.user.has_perm("pagos.view_monthlypayment"):
        movements = movements.filter(charge__member=request.user)
    payment_id = request.GET.get("payment_id", "").strip()
    member_id = request.GET.get("member_id", "").strip()
    for value, field in [(payment_id, "pk"), (member_id, "charge__member_id")]:
        if value:
            movements = movements.filter(**{field: int(value)}) if value.isascii() and value.isdigit() and len(value) <= 18 else movements.none()
    totals = movements.aggregate(
        ingresos=Sum("amount", filter=Q(amount__gt=0)),
        egresos=Sum("amount", filter=Q(amount__lt=0)),
        ingresos_cantidad=Count("pk", filter=Q(amount__gt=0)),
        egresos_cantidad=Count("pk", filter=Q(amount__lt=0)),
        neto=Sum("amount"),
    )
    context = {
        "movements": movements,
        "payment_id": payment_id,
        "member_id": member_id,
        "ingresos": totals["ingresos"] or Decimal("0"),
        "egresos": -(totals["egresos"] or Decimal("0")),
        "ingresos_cantidad": totals["ingresos_cantidad"],
        "egresos_cantidad": totals["egresos_cantidad"],
        "total": totals["neto"] or Decimal("0"),
    }
    return render(request, "payments/history.html", context)


@login_required
@permission_required(["pagos.change_monthlypayment", "pagos.view_monthlypayment"], raise_exception=True)
@require_http_methods(["GET", "POST"])
def cancel_payment(request, movement_id):
    movement = get_object_or_404(PaymentMovement.objects.select_related("charge__member"), pk=movement_id)
    if request.method == "POST":
        try:
            with transaction.atomic():
                reversal = reverse_payment(movement.pk, request.user)
                audit(request, "CREATE", f"Anulación {reversal.pk} del pago {movement.pk}: {reversal.amount}")
        except ValidationError as error:
            messages.error(request, "; ".join(error.messages))
        else:
            messages.success(request, "Pago anulado mediante un movimiento negativo.")
        return redirect("payment_history")
    return render(request, "payments/cancel.html", {"movement": movement})
