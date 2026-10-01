from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.audit import audit
from .forms import GeneratePaymentsForm, PeriodForm, RecordPaymentForm
from .models import MonthlyPayment
from .services import generate_monthly_payments


@login_required
@require_http_methods(["GET"])
def payment_list(request):
    payments = MonthlyPayment.objects.select_related("member", "member__person")
    can_view_all = request.user.has_perm("pagos.view_monthlypayment")
    if not can_view_all:
        payments = payments.filter(member=request.user)
    period_form = PeriodForm(request.GET if "period" in request.GET else None)
    if period_form.is_bound and period_form.is_valid():
        payments = payments.filter(period=period_form.cleaned_data["period"])
    search = request.GET.get("q", "").strip()
    if search:
        payments = payments.filter(Q(member__username__icontains=search) | Q(member__person__name__icontains=search) | Q(member__person__surname__icontains=search))
    status = request.GET.get("status", "")
    today = timezone.localdate()
    if status == "paid":
        payments = payments.filter(paid_on__isnull=False)
    elif status == "pending":
        payments = payments.filter(paid_on__isnull=True, due_date__gte=today)
    elif status == "overdue":
        payments = payments.filter(paid_on__isnull=True, due_date__lt=today)
    totals = payments.aggregate(collected=Sum("amount", filter=Q(paid_on__isnull=False)), outstanding=Sum("amount", filter=Q(paid_on__isnull=True)))
    return render(request, "payments/list.html", {"payments": payments, "period_form": period_form, "search": search, "status_filter": status, "can_view_all": can_view_all, "collected": totals["collected"] or Decimal("0"), "outstanding": totals["outstanding"] or Decimal("0")})


@login_required
@permission_required(["pagos.add_monthlypayment", "pagos.view_monthlypayment"], raise_exception=True)
@require_http_methods(["GET", "POST"])
def generate_payments(request):
    form = GeneratePaymentsForm(request.POST if request.method == "POST" else None, initial={"period": timezone.localdate().replace(day=1)})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            created, existing, skipped = generate_monthly_payments(form.cleaned_data["period"], form.cleaned_data["due_day"])
            audit(request, "CREATE", f"Mensualidades {form.cleaned_data['period']:%m/%Y}: {created} creadas")
        messages.success(request, f"{created} cuotas creadas; {existing} ya existían; {skipped} socios omitidos por no tener un plan con precio válido.")
        return redirect("payment_list")
    return render(request, "payments/generate.html", {"form": form})


@login_required
@permission_required(["pagos.change_monthlypayment", "pagos.view_monthlypayment"], raise_exception=True)
@require_http_methods(["GET", "POST"])
def record_payment(request, payment_id):
    with transaction.atomic():
        payment = get_object_or_404(MonthlyPayment.objects.select_for_update().select_related("member"), pk=payment_id)
        if payment.paid_on:
            messages.info(request, "Esta cuota ya está pagada.")
            return redirect("payment_list")
        form = RecordPaymentForm(request.POST if request.method == "POST" else None, instance=payment)
        if request.method == "POST" and form.is_valid():
            payment = form.save(commit=False)
            payment.recorded_by = request.user
            payment.save()
            audit(request, "UPDATE", f"Pago de mensualidad {payment.pk}: {payment.member.username}, {payment.period:%m/%Y}, importe {payment.amount}")
            messages.success(request, "Pago registrado correctamente.")
            return redirect("payment_list")
    return render(request, "payments/record.html", {"form": form, "payment": payment})
