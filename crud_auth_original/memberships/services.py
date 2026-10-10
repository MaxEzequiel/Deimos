from calendar import monthrange
from datetime import date

from django.db.models import OuterRef, Subquery
from django.utils import timezone


def next_month_expiry(paid_on):
	year = paid_on.year + (paid_on.month == 12)
	month = paid_on.month % 12 + 1
	return date(year, month, min(paid_on.day, monthrange(year, month)[1]))


def with_last_payment(queryset, user_field="user_id"):
	from payments.models import MonthlyPayment

	payments = MonthlyPayment.objects.filter(
		member_id=OuterRef(user_field), paid_on__lte=timezone.localdate(), kind__in=["gym", "both"]
	).order_by("-paid_on", "-period", "-pk")
	return queryset.annotate(
		last_paid_on=Subquery(payments.values("paid_on")[:1]),
		last_coverage_end=Subquery(payments.values("coverage_end")[:1]),
	)


def membership_coverage(user, today=None, membership=None):
	"""Shared coverage rule: manual activation plus payment, inclusive expiry."""
	today = today or timezone.localdate()
	membership = (
		membership
		if membership is not None
		else getattr(user, "membership", None)
	)
	if (
		membership is not None
		and hasattr(membership, "last_paid_on")
		and today == timezone.localdate()
	):
		paid_on = membership.last_paid_on
		coverage_end = getattr(membership, "last_coverage_end", None)
	else:
		payment = (
			user.monthly_payments.filter(paid_on__lte=today, kind__in=["gym", "both"])
			.order_by("-paid_on", "-period", "-pk")
			.first()
		)
		paid_on = payment.paid_on if payment else None
		coverage_end = payment.coverage_end if payment else None
	expiry = (coverage_end or next_month_expiry(paid_on)) if paid_on else None
	days_remaining = (expiry - today).days if expiry else None
	administratively_active = (
		membership is not None and membership.status == "active"
	)
	active = administratively_active and expiry is not None and expiry >= today
	return {
		"active": active,
		"administratively_active": administratively_active,
		"last_paid_on": paid_on,
		"expires_at": expiry,
		"days_remaining": days_remaining,
	}


def effective_membership_status(membership, today=None):
	coverage = membership_coverage(
		membership.user, today=today, membership=membership
	)
	return "active" if coverage["active"] else "inactive"
