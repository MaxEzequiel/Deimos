from calendar import monthrange
from datetime import date
from decimal import Decimal
from classes.models import Course, Inscription

from django.db import transaction
from django.db.models import Count, F, Q
from django.core.exceptions import ValidationError

from memberships.services import next_month_expiry
from people.models import Person
from .models import MonthlyPayment, PaymentMovement


def apply_payment_coverage(payment):
	payment.coverage_start = payment.paid_on
	payment.coverage_end = (
		next_month_expiry(payment.paid_on) if payment.paid_on else None
	)


def member_plan_amount(member):
	membership = getattr(member, "membership", None)
	person = getattr(member, "person", None)
	plan = (membership.plan if membership else None) or (
		person.plan if person else None
	)
	if not plan or not plan.base_price or plan.base_price <= 0:
		raise ValidationError(
			"Seleccioná y guardá un plan con precio positivo antes de generar el pago."
		)
	return plan.base_price


def available_payment_courses(member):
	return Course.objects.annotate(enrolled_count=Count("inscription")).filter(
		Q(enrolled_count__lt=F("max_capacity")) | Q(inscription__participant=member),
		price__gt=0,
	).exclude(teacher=member).distinct().order_by("name", "starts_at")


def payment_quote(member, kind="gym", courses=(), selected_plan=None):
	if kind not in {"gym", "classes", "both"}:
		raise ValidationError("Seleccioná un concepto válido.")
	items = []
	if kind in {"gym", "both"}:
		amount = selected_plan.base_price if selected_plan else member_plan_amount(member)
		if amount <= 0:
			raise ValidationError("El plan debe tener precio positivo.")
		items.append({"name": "Musculación", "price": str(amount)})
	if kind in {"classes", "both"}:
		ids = {course.pk for course in courses}
		selected = list(available_payment_courses(member).filter(pk__in=ids))
		if not ids or len(selected) != len(ids):
			raise ValidationError("Seleccioná al menos una clase disponible con precio y cupo.")
		for course in selected:
			if course.price <= 0:
				raise ValidationError(f"Configurá un precio positivo para {course.name}.")
			items.append({"course_id": course.pk, "name": course.name, "price": str(course.price)})
	return sum((Decimal(item["price"]) for item in items), Decimal("0")), items


@transaction.atomic
def register_member_payment(member, data, operator):
	"""Settle an existing charge or create one, preserving its recorded price."""
	type(member).objects.select_for_update().get(pk=member.pk)
	period = data["period"]
	existing = MonthlyPayment.objects.filter(
		member=member, period=period
	).first()
	kind = data.get("kind") or "gym"
	if existing:
		if kind != existing.kind:
			raise ValidationError("La cuota existente conserva su concepto original.")
		amount, items = existing.amount, existing.items
	else:
		amount, items = payment_quote(member, kind, data.get("courses", ()))
	if data["amount"] != amount:
		raise ValidationError(
			(
				f"El importe del pago debe ser ${amount}, según la cuota pendiente o "
				f"el plan seleccionado."
			)
		)
	payment, _ = MonthlyPayment.objects.get_or_create(
		member=member,
		period=period,
		defaults={
			"amount": amount,
			"kind": kind,
			"items": items,
			"due_date": period.replace(
				day=min(
					data["paid_on"].day,
					monthrange(period.year, period.month)[1],
				)
			),
		},
	)
	payment = MonthlyPayment.objects.select_for_update().get(pk=payment.pk)
	if payment.paid_on:
		raise ValidationError("Esta mensualidad ya está pagada")
	if payment.amount != data["amount"]:
		raise ValidationError(
			f"El importe de la cuota pendiente es ${payment.amount}"
		)
	for item in payment.items:
		if not item.get("course_id"):
			continue
		course = Course.objects.select_for_update().filter(pk=item["course_id"]).first()
		if not course:
			raise ValidationError("Una clase seleccionada ya no está disponible.")
		if not Inscription.objects.filter(course=course, participant=member).exists():
			if course.teacher_id == member.pk or course.inscription_set.count() >= course.max_capacity:
				raise ValidationError(f"La clase {course.name} no tiene cupos disponibles.")
			Inscription.objects.create(course=course, participant=member)
	payment.paid_on = data["paid_on"]
	payment.method = data.get("method", "")
	payment.reference = ""
	payment.recorded_by = operator
	apply_payment_coverage(payment)
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
		last_day = date(
			period.year, period.month, monthrange(period.year, period.month)[1]
		)
		members = Person.objects.filter(
			user__is_active=True, user__date_joined__date__lte=last_day
		).select_related("user", "plan", "user__membership__plan")
		created = existing = skipped = 0
		for person in members:
			if MonthlyPayment.objects.filter(
				member=person.user, period=period
			).exists():
				existing += 1
				continue
			membership = getattr(person.user, "membership", None)
			plan = person.plan or (membership.plan if membership else None)
			if not plan or not plan.base_price or plan.base_price <= 0:
				skipped += 1
				continue
			_, was_created = MonthlyPayment.objects.get_or_create(
				member=person.user,
				period=period,
				defaults={"amount": plan.base_price, "due_date": due_date},
			)
			created += int(was_created)
			existing += int(not was_created)
	except Exception:
		transaction.savepoint_rollback(savepoint_id)
		raise
	transaction.savepoint_commit(savepoint_id)
	return created, existing, skipped


@transaction.atomic
def create_payment_movement(payment):
	"""Congela los datos del cobro para que futuras modificaciones no alteren el historial."""
	movement = PaymentMovement.objects.create(
		charge=payment,
		amount=payment.amount,
		paid_on=payment.paid_on,
		recorded_by=payment.recorded_by,
		method=payment.method,
	)
	movement.reference = f"PAGO-{movement.pk:08d}"
	movement.save(update_fields=["reference"])
	payment.reference = movement.reference
	payment.save(update_fields=["reference"])
	return movement


@transaction.atomic
def reverse_payment(movement_id, operator):
	from django.utils import timezone

	# Bloquear la cuota serializa tanto nuevos cobros como anulaciones.
	original = PaymentMovement.objects.get(pk=movement_id)
	charge = MonthlyPayment.objects.select_for_update().get(
		pk=original.charge_id
	)
	original = PaymentMovement.objects.select_for_update().get(pk=movement_id)
	if (
		original.amount <= 0
		or PaymentMovement.objects.filter(reversal_of=original).exists()
	):
		raise ValidationError(
			"Este movimiento ya fue anulado o es una anulación."
		)
	reversal = PaymentMovement(
		charge=charge,
		amount=-original.amount,
		paid_on=timezone.localdate(),
		reference=original.reference,
		method=original.method,
		reversal_of=original,
		recorded_by=operator,
	)
	reversal.full_clean()
	reversal.save()
	charge.paid_on = None
	charge.reference = ""
	charge.coverage_start = None
	charge.coverage_end = None
	charge.recorded_by = None
	charge.save(
		update_fields=[
			"paid_on",
			"reference",
			"recorded_by",
			"coverage_start",
			"coverage_end",
		]
	)
	return reversal
