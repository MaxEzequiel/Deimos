from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from classes.models import Course, Inscription
from memberships.models import Membership
from memberships.services import membership_coverage
from plans.models import Plan
from .services import register_member_payment, reverse_payment


class ClassPaymentTests(TestCase):
	def setUp(self):
		self.operator = get_user_model().objects.create_superuser(username="operator")
		self.member = get_user_model().objects.create_user(username="member")
		self.plan = Plan.objects.create(name="Mensual", base_price=1000)
		Membership.objects.create(user=self.member, plan=self.plan, status="active")
		self.course = Course.objects.create(name="Pilates", description="Clase de pilates", teacher=self.operator, starts_at=timezone.now(), ends_at=timezone.now() + timedelta(hours=1), price=250)
		Inscription.objects.create(course=self.course, participant=self.member)
		self.data = {"period": timezone.localdate().replace(day=1), "paid_on": timezone.localdate(), "method": "cash", "courses": [self.course]}

	def test_three_payment_options(self):
		for index, (kind, amount) in enumerate([("gym", 1000), ("classes", 250), ("both", 1250)], 1):
			self.data.update(kind=kind, amount=Decimal(amount), period=self.data["period"].replace(month=index))
			payment = register_member_payment(self.member, self.data, self.operator)
			self.assertEqual(payment.amount, amount)
			self.assertEqual(payment.kind, kind)
			self.assertEqual(sum(Decimal(item["price"]) for item in payment.items), amount)

	def test_classes_do_not_enable_gym_and_repayment_preserves_price(self):
		self.data.update(kind="classes", amount=Decimal(250))
		payment = register_member_payment(self.member, self.data, self.operator)
		self.assertFalse(membership_coverage(self.member)["active"])
		reverse_payment(payment.movements.get().pk, self.operator)
		self.course.price = 500
		self.course.save()
		payment = register_member_payment(self.member, self.data, self.operator)
		self.assertEqual(payment.amount, 250)
		self.assertEqual(payment.items[0]["price"], "250.00")

	def test_invalid_total_and_full_classes_are_rejected(self):
		self.data.update(kind="both", amount=Decimal(1))
		with self.assertRaises(ValidationError):
			register_member_payment(self.member, self.data, self.operator)
		Inscription.objects.all().delete()
		Inscription.objects.create(course=self.course, participant=self.operator)
		self.data.update(kind="classes", amount=Decimal(250))
		with self.assertRaises(ValidationError):
			register_member_payment(self.member, self.data, self.operator)

	def test_available_classes_can_be_selected_and_enrolled_on_payment(self):
		Inscription.objects.all().delete()
		self.client.force_login(self.operator)
		response = self.client.get(reverse("pay_subscription", args=[self.member.pk]))
		self.assertContains(response, self.course.name)
		self.assertContains(response, "data-payment-courses")
		self.data.update(kind="classes", amount=Decimal(250))
		register_member_payment(self.member, self.data, self.operator)
		self.assertTrue(Inscription.objects.filter(course=self.course, participant=self.member).exists())

	def test_subscription_accepts_classes_without_plan(self):
		Membership.objects.filter(user=self.member).update(plan=None)
		self.client.force_login(self.operator)
		response = self.client.post(reverse("pay_subscription", args=[self.member.pk]), {"period": self.data["period"].strftime("%Y-%m"), "paid_on": self.data["paid_on"].isoformat(), "kind": "classes", "courses": [self.course.pk], "amount": "250", "method": "cash"})
		self.assertRedirects(response, reverse("payment_history"))
