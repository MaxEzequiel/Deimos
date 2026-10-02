from calendar import monthrange
from datetime import date

from django.db import transaction
from django.core.exceptions import ValidationError

from memberships.services import next_month_expiry
from people.models import Person
from .models import MonthlyPayment


def apply_payment_coverage(payment):
    payment.coverage_start = payment.paid_on
    payment.coverage_end = next_month_expiry(payment.paid_on) if payment.paid_on else None


@transaction.atomic
def register_member_payment(member, data, operator):
    """Settle an existing charge or create one, preserving its recorded price."""
    period = data['period']
    payment, _ = MonthlyPayment.objects.get_or_create(
        member=member, period=period,
        defaults={'amount': data['amount'], 'due_date': period.replace(day=min(data['paid_on'].day, monthrange(period.year, period.month)[1]))},
    )
    payment = MonthlyPayment.objects.select_for_update().get(pk=payment.pk)
    if payment.paid_on:
        raise ValidationError('Esta mensualidad ya está pagada')
    if payment.amount != data['amount']:
        raise ValidationError(f'El importe de la cuota pendiente es ${payment.amount}')
    payment.paid_on = data['paid_on']
    payment.method = data['method']
    payment.reference = data.get('reference', '')
    payment.recorded_by = operator
    apply_payment_coverage(payment)
    payment.full_clean()
    payment.save()
    return payment


@transaction.atomic
def generate_monthly_payments(period, due_day):
    """Snapshot plan prices; repeating generation preserves existing charges."""
    savepoint_id = transaction.savepoint()
    try:
        due_date = date(period.year, period.month, due_day)
        last_day = date(period.year, period.month, monthrange(period.year, period.month)[1])
        members = Person.objects.filter(user__is_active=True, user__date_joined__date__lte=last_day).select_related("user", "plan", "user__membership__plan")
        created = existing = skipped = 0
        for person in members:
            if MonthlyPayment.objects.filter(member=person.user, period=period).exists():
                existing += 1
                continue
            membership = getattr(person.user, "membership", None)
            plan = person.plan or (membership.plan if membership else None)
            if not plan or not plan.base_price or plan.base_price <= 0:
                skipped += 1
                continue
            _, was_created = MonthlyPayment.objects.get_or_create(member=person.user, period=period, defaults={"amount": plan.base_price, "due_date": due_date})
            created += int(was_created)
            existing += int(not was_created)
    except Exception:
        transaction.savepoint_rollback(savepoint_id)
        raise
    transaction.savepoint_commit(savepoint_id)
    return created, existing, skipped
