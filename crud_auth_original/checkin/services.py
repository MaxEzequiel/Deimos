from memberships.services import next_month_expiry

from django.utils import timezone

from payments.models import MonthlyPayment


def member_checkin_status(person, today=None):
    """Coverage expires on the payment's day in the following month."""
    today = today or timezone.localdate()
    period = today.replace(day=1)
    context = {
        "member_name": "Socio sin datos asociados",
        "member_initials": "?",
        "member_registered_at": None,
        "current_period": period,
        "last_paid_on": None,
        "membership_expires_at": None,
        "membership_status": "expired",
        "membership_label": "Mensualidad vencida",
        "membership_detail": "Sin pago registrado",
        "days_remaining": None,
        "coverage_remaining_percent": 0,
        "coverage_elapsed_percent": 100,
    }
    if person is None:
        context["membership_detail"] = "Este ingreso no tiene un socio asociado"
        return context
    context.update({
        "member_name": f"{person.name} {person.surname}".strip(),
        "member_initials": "".join(value.strip()[0] for value in (person.name, person.surname) if value and value.strip()).upper() or "?",
        "member_registered_at": person.user.date_joined,
    })
    payment = MonthlyPayment.objects.filter(member_id=person.user_id, paid_on__isnull=False, paid_on__lte=today).order_by("-paid_on", "-period", "-pk").first()
    if payment is None:
        return context
    expiry = payment.coverage_end or next_month_expiry(payment.paid_on)
    days_remaining = (expiry - today).days
    duration = max(1, (expiry - payment.paid_on).days)
    remaining_percent = max(0, min(100, round(days_remaining / duration * 100)))
    context.update({
        "coverage_remaining_percent": remaining_percent,
        "coverage_elapsed_percent": 100 - remaining_percent,
    })
    if days_remaining <= 0:
        context.update({
            "last_paid_on": payment.paid_on,
            "membership_expires_at": expiry,
            "days_remaining": days_remaining,
            "membership_detail": "Vence hoy" if days_remaining == 0 else f"Venció el {expiry:%d/%m/%Y}",
        })
        return context
    expiring = days_remaining <= 5
    context.update({
        "last_paid_on": payment.paid_on,
        "membership_expires_at": expiry,
        "membership_status": "expiring" if expiring else "active",
        "membership_label": "Próxima a vencer" if expiring else "Mensualidad activa",
        "membership_detail": "Vence hoy" if days_remaining == 0 else f"Vence en {days_remaining} días",
        "days_remaining": days_remaining,
    })
    return context
