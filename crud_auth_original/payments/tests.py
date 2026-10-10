from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from memberships.models import Membership
from people.models import Person
from plans.models import Plan
from .models import MonthlyPayment
from .services import (
	generate_monthly_payments,
	register_member_payment,
	reverse_payment,
)


class MonthlyPaymentTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.today = timezone.localdate()
		cls.period = cls.today.replace(day=1)
		cls.admin = get_user_model().objects.create_superuser(
			username="cashier", password="TestPassword123!"
		)
		cls.member = get_user_model().objects.create_user(username="member")
		cls.other = get_user_model().objects.create_user(username="other")
		cls.plan = Plan.objects.create(
			name="Mensual", base_price=Decimal("18000.00")
		)
		Person.objects.create(
			user=cls.member,
			plan=cls.plan,
			id_number=12345678,
			name="Ana",
			surname="Perez",
		)
		cls.payment = MonthlyPayment.objects.create(
			member=cls.member,
			period=cls.period,
			amount=cls.plan.base_price,
			due_date=cls.period.replace(day=10),
		)

	def test_generation_is_idempotent_and_preserves_historical_price(self):
		self.plan.base_price = Decimal("22000")
		self.plan.save()
		self.assertEqual(generate_monthly_payments(self.period, 15), (0, 1, 0))
		self.payment.refresh_from_db()
		self.assertEqual(self.payment.amount, Decimal("18000"))
		self.assertEqual(self.payment.due_date.day, 10)

	def test_generation_uses_membership_plan_and_skips_unpriced_members(self):
		Person.objects.create(
			user=self.other, id_number=23456789, name="Luis", surname="Lopez"
		)
		self.assertEqual(generate_monthly_payments(self.period, 10), (0, 1, 1))
		Membership.objects.create(user=self.other, plan=self.plan)
		self.assertEqual(generate_monthly_payments(self.period, 10), (1, 1, 0))
		self.assertEqual(generate_monthly_payments(self.period, 10), (0, 2, 0))

	def test_generation_excludes_inactive_and_later_members(self):
		self.member.is_active = False
		self.member.save()
		self.assertEqual(generate_monthly_payments(self.period, 10), (0, 0, 0))
		earlier_period = (self.period - timedelta(days=1)).replace(day=1)
		self.member.is_active = True
		self.member.save()
		self.assertEqual(
			generate_monthly_payments(earlier_period, 10), (0, 0, 0)
		)

	def test_status_tracks_due_date(self):
		self.payment.due_date = self.today - timedelta(days=1)
		self.assertEqual(self.payment.status, "overdue")
		self.payment.due_date = self.today
		self.assertEqual(self.payment.status, "pending")
		self.payment.paid_on = self.today
		self.assertEqual(self.payment.status, "paid")

	def test_reference_is_generated_and_changes_when_payment_is_recorded_again(
		self,
	):
		data = {
			"period": self.period,
			"amount": self.payment.amount,
			"paid_on": self.today,
			"method": "cash",
			"reference": "MANUAL",
		}
		payment = register_member_payment(self.member, data, self.admin)
		original = payment.movements.get()
		self.assertEqual(payment.reference, f"PAGO-{original.pk:08d}")
		self.assertEqual(original.reference, payment.reference)
		reversal = reverse_payment(original.pk, self.admin)
		self.assertEqual(reversal.reference, original.reference)
		repayment = register_member_payment(self.member, data, self.admin)
		self.assertNotEqual(repayment.reference, original.reference)
		original.refresh_from_db()
		self.assertEqual(original.reference, f"PAGO-{original.pk:08d}")

	def test_subscription_form_uses_generated_reference(self):
		from django.urls import reverse

		self.client.force_login(self.admin)
		url = reverse("pay_subscription", args=[self.member.pk])
		self.assertNotContains(self.client.get(url), 'name="reference"')
		response = self.client.post(
			url,
			{
				"period": self.period.strftime("%Y-%m"),
				"amount": str(self.payment.amount),
				"paid_on": self.today.isoformat(),
				"method": "cash",
				"reference": "MANUAL",
			},
			follow=True,
		)
		self.payment.refresh_from_db()
		self.assertContains(response, self.payment.reference)
		self.assertTrue(self.payment.reference.startswith("PAGO-"))

	def test_model_and_database_guards(self):
		self.payment.period = self.period.replace(day=2)
		with self.assertRaises(ValidationError):
			self.payment.full_clean()
		with self.assertRaises(IntegrityError), transaction.atomic():
			MonthlyPayment.objects.create(
				member=self.member,
				period=self.period,
				amount=100,
				due_date=self.period,
			)
		with self.assertRaises(IntegrityError), transaction.atomic():
			MonthlyPayment.objects.create(
				member=self.other,
				period=self.period,
				amount=-1,
				due_date=self.period,
			)

	def test_new_payment_requires_selected_plan_price(self):
		period = (self.period - timedelta(days=1)).replace(day=1)
		data = {"period": period, "amount": Decimal("1"), "paid_on": self.today}
		with self.assertRaises(ValidationError):
			register_member_payment(self.member, data, self.admin)
		self.assertFalse(
			MonthlyPayment.objects.filter(
				member=self.member, period=period
			).exists()
		)
		data["amount"] = self.plan.base_price
		payment = register_member_payment(self.member, data, self.admin)
		self.assertEqual(payment.amount, self.plan.base_price)
		self.assertEqual(payment.movements.get().amount, self.plan.base_price)
		with self.assertRaises(ValidationError):
			register_member_payment(self.other, data, self.admin)

	def test_management_rejects_modified_plan_amount(self):
		from django.urls import reverse

		self.payment.delete()
		self.client.force_login(self.admin)
		url = reverse("manage_member", args=[self.member.pk])
		response = self.client.get(url)
		self.assertTrue(
			response.context["payment_form"]
			.fields["amount"]
			.widget.attrs["readonly"]
		)
		response = self.client.post(
			url,
			{
				"action": "payment",
				"period": self.period.strftime("%Y-%m"),
				"amount": "1",
				"paid_on": self.today.isoformat(),
				"method": "cash",
			},
		)
		self.assertIn("amount", response.context["payment_form"].errors)
		self.assertFalse(MonthlyPayment.objects.exists())
