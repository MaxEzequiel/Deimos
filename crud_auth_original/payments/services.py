from calendar import monthrange
from datetime import date

from django.db import transaction
from django.core.exceptions import ValidationError

from people.models import Person
from .models import MonthlyPayment, PaymentMovement


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
    payment.reference = data.get('reference', '')
    payment.recorded_by = operator
    payment.full_clean()
    payment.save()
    create_payment_movement(payment)
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


def create_payment_movement(payment):
    """Congela los datos del cobro para que futuras modificaciones no alteren el historial."""
    return PaymentMovement.objects.create(
        charge=payment, amount=payment.amount, paid_on=payment.paid_on,
        reference=payment.reference, recorded_by=payment.recorded_by,
    )


@transaction.atomic
def reverse_payment(movement_id, operator):
    from django.utils import timezone
    # Bloquear la cuota serializa tanto nuevos cobros como anulaciones.
    original = PaymentMovement.objects.get(pk=movement_id)
    charge = MonthlyPayment.objects.select_for_update().get(pk=original.charge_id)
    original = PaymentMovement.objects.select_for_update().get(pk=movement_id)
    if original.amount <= 0 or PaymentMovement.objects.filter(reversal_of=original).exists():
        raise ValidationError("Este movimiento ya fue anulado o es una anulación.")
    reversal = PaymentMovement(
        charge=charge, amount=-original.amount, paid_on=timezone.localdate(),
        reference=original.reference,
        reversal_of=original, recorded_by=operator,
    )
    reversal.full_clean()
    reversal.save()
    charge.paid_on = None
    charge.reference = ""
    charge.recorded_by = None
    charge.save(update_fields=["paid_on", "reference", "recorded_by"])
    return reversal
