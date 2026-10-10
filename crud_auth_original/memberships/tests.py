from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from checkin.services import member_checkin_status
from memberships.models import Membership
from memberships.services import effective_membership_status
from payments.services import register_member_payment, reverse_payment
from people.models import Person
from plans.models import Plan


class UnifiedCoverageTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user("coverage")
		self.person = Person.objects.create(
			user=self.user, id_number=12345678, name="Ana", surname="Perez"
		)
		self.membership = Membership.objects.create(
			user=self.user,
			status="active",
			plan=Plan.objects.create(name="Mensual", base_price=100),
		)

	def pay(self, period, paid_on):
		with patch("django.utils.timezone.localdate", return_value=paid_on):
			return register_member_payment(
				self.user,
				{"period": period, "paid_on": paid_on, "amount": 100},
				self.user,
			)

	def assert_coverage(self, today, active):
		self.membership.refresh_from_db()
		self.assertEqual(
			effective_membership_status(self.membership, today),
			"active" if active else "inactive",
		)
		indicator = member_checkin_status(self.person, today)
		self.assertEqual(
			indicator["membership_status"] in {"active", "expiring"}, active
		)

	def test_active_without_payment_has_no_coverage(self):
		self.assert_coverage(date(2026, 10, 6), False)

	def test_expiry_is_inclusive_in_both_modules(self):
		self.pay(date(2026, 10, 1), date(2026, 10, 6))
		self.assert_coverage(date(2026, 11, 6), True)
		self.assert_coverage(date(2026, 11, 7), False)
		self.assertEqual(
			member_checkin_status(self.person, date(2026, 11, 6))[
				"membership_detail"
			],
			"Vence hoy",
		)

	def test_payment_does_not_override_manual_deactivation(self):
		self.membership.status = "inactive"
		self.membership.save()
		self.pay(date(2026, 10, 1), date(2026, 10, 6))
		self.assert_coverage(date(2026, 10, 7), False)
		self.assertEqual(self.membership.status, "inactive")

	def test_reversal_falls_back_to_previous_valid_payment(self):
		self.pay(date(2026, 9, 1), date(2026, 9, 20))
		latest = self.pay(date(2026, 10, 1), date(2026, 10, 6))
		reverse_payment(latest.movements.get().pk, self.user)
		self.assert_coverage(date(2026, 10, 10), True)
		self.assertEqual(
			member_checkin_status(self.person, date(2026, 10, 10))[
				"last_paid_on"
			],
			date(2026, 9, 20),
		)
		self.assert_coverage(date(2026, 10, 21), False)
