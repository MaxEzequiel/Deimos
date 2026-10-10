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
@permission_required(
	["pagos.change_monthlypayment", "pagos.view_monthlypayment"],
	raise_exception=True,
)
@require_http_methods(["GET", "POST"])
def pay_subscription(request, user_id):
	user = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
	membership = getattr(user, "membership", None)
	person = getattr(user, "person", None)
	plan = (membership.plan if membership else None) or (
		person.plan if person else None
	)
	from .forms import MemberPaymentForm
	from .services import register_member_payment

	period = timezone.localdate().replace(day=1)
	charge = MonthlyPayment.objects.filter(member=user, period=period).first()
	form = MemberPaymentForm(
		request.POST if request.method == "POST" else None,
		member=user,
		initial={
			"period": period,
			"kind": charge.kind if charge else "gym",
			"amount": charge.amount if charge else (plan.base_price if plan else 0),
		},
	)
	if request.method == "POST" and form.is_valid():
		try:
			with transaction.atomic():
				payment = register_member_payment(
					user, form.cleaned_data, request.user
				)
				audit(
					request,
					"CREATE",
					f"Cobro de suscripción {payment.pk}: {payment.amount}",
				)
		except ValidationError as error:
			form.add_error(None, error)
		else:
			messages.success(
				request,
				f"Pago registrado. ID para facturación: {payment.reference}.",
			)
			return redirect("payment_history")
	return render(
		request,
		"payments/pay_subscription.html",
		{"form": form, "member": user, "plan": plan, "prices": {str(c.pk): str(c.price) for c in form.fields["courses"].queryset}, "gym_price": str(plan.base_price if plan else 0), "charges": {c.period.strftime("%Y-%m"): {"amount": str(c.amount), "kind": c.kind, "items": c.items} for c in MonthlyPayment.objects.filter(member=user)}},
	)


@login_required
@require_http_methods(["GET"])
def payment_history(request):
	movements = PaymentMovement.objects.select_related(
		"charge__member__person", "recorded_by", "reversal_of", "reversal"
	)
	if not request.user.has_perm("pagos.view_monthlypayment"):
		movements = movements.filter(charge__member=request.user)
	search = request.GET.get("q", "").strip()
	if search:
		if search.isascii() and search.isdigit():
			movements = (
				movements.filter(charge__member__person__id_number=int(search))
				if len(search) <= 10 else movements.none()
			)
		else:
			for word in search.split():
				movements = movements.filter(
					Q(charge__member__person__name__icontains=word)
					| Q(charge__member__person__surname__icontains=word)
					| Q(charge__member__first_name__icontains=word)
					| Q(charge__member__last_name__icontains=word)
					| Q(charge__member__username__icontains=word)
				)
	payment_id = request.GET.get("payment_id", "").strip()
	member_id = request.GET.get("member_id", "").strip()
	for value, field in [(payment_id, "pk"), (member_id, "charge__member_id")]:
		if value:
			movements = (
				movements.filter(**{field: int(value)})
				if value.isascii() and value.isdigit() and len(value) <= 18
				else movements.none()
			)
	totals = movements.aggregate(
		ingresos=Sum("amount", filter=Q(amount__gt=0)),
		egresos=Sum("amount", filter=Q(amount__lt=0)),
		ingresos_cantidad=Count("pk", filter=Q(amount__gt=0)),
		egresos_cantidad=Count("pk", filter=Q(amount__lt=0)),
		neto=Sum("amount"),
	)
	context = {
		"movements": movements,
		"search": search,
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
@require_http_methods(["GET"])
def payment_invoice(request, movement_id):
	movements = PaymentMovement.objects.select_related(
		"charge__member__person__plan",
		"charge__member__membership__plan",
		"recorded_by",
		"reversal_of",
		"reversal",
	)
	if not request.user.has_perm("pagos.view_monthlypayment"):
		movements = movements.filter(charge__member=request.user)
	movement = get_object_or_404(movements, pk=movement_id)
	member = movement.charge.member
	person = getattr(member, "person", None)
	membership = getattr(member, "membership", None)
	plan = (membership.plan if membership else None) or (
		person.plan if person else None
	)
	return render(
		request,
		"payments/invoice.html",
		{
			"movement": movement,
			"member": member,
			"person": person,
			"membership": membership,
			"plan": plan,
		},
	)


@login_required
@permission_required(
	["pagos.change_monthlypayment", "pagos.view_monthlypayment"],
	raise_exception=True,
)
@require_http_methods(["GET", "POST"])
def cancel_payment(request, movement_id):
	movement = get_object_or_404(
		PaymentMovement.objects.select_related("charge__member"), pk=movement_id
	)
	if request.method == "POST":
		try:
			with transaction.atomic():
				reversal = reverse_payment(movement.pk, request.user)
				audit(
					request,
					"CREATE",
					f"Anulación {reversal.pk} del pago {movement.pk}: {reversal.amount}",
				)
		except ValidationError as error:
			messages.error(request, "; ".join(error.messages))
		else:
			messages.success(
				request, "Pago anulado mediante un movimiento negativo."
			)
		return redirect("payment_history")
	return render(request, "payments/cancel.html", {"movement": movement})
