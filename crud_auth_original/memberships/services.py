from calendar import monthrange
from datetime import date

from django.db.models import OuterRef, Subquery
from django.utils import timezone


def next_month_expiry(paid_on):
    year = paid_on.year + (paid_on.month == 12)
    month = paid_on.month % 12 + 1
    return date(year, month, min(paid_on.day, monthrange(year, month)[1]))


def with_last_payment(queryset, user_field='user_id'):
    from payments.models import MonthlyPayment
    payments = MonthlyPayment.objects.filter(member_id=OuterRef(user_field), paid_on__lte=timezone.localdate()).order_by('-paid_on', '-period', '-pk')
    return queryset.annotate(last_paid_on=Subquery(payments.values('paid_on')[:1]))


def effective_membership_status(membership, today=None):
    if membership.status != 'active':
        return 'inactive'
    today = today or timezone.localdate()
    if hasattr(membership, 'last_paid_on'):
        paid_on = membership.last_paid_on
    else:
        paid_on = membership.user.monthly_payments.filter(paid_on__lte=today).order_by('-paid_on', '-period', '-pk').values_list('paid_on', flat=True).first()
    return 'inactive' if paid_on and next_month_expiry(paid_on) < today else 'active'
