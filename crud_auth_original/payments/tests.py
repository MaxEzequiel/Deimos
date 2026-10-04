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
from .services import generate_monthly_payments


class MonthlyPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.today = timezone.localdate()
        cls.period = cls.today.replace(day=1)
        cls.admin = get_user_model().objects.create_superuser(username="cashier", password="TestPassword123!")
        cls.member = get_user_model().objects.create_user(username="member")
        cls.other = get_user_model().objects.create_user(username="other")
        cls.plan = Plan.objects.create(name="Mensual", base_price=Decimal("18000.00"))
        Person.objects.create(user=cls.member, plan=cls.plan, id_number=12345678, name="Ana", surname="Perez")
        cls.payment = MonthlyPayment.objects.create(member=cls.member, period=cls.period, amount=cls.plan.base_price, due_date=cls.period.replace(day=10))

    def test_generation_is_idempotent_and_preserves_historical_price(self):
        self.plan.base_price = Decimal("22000")
        self.plan.save()
        self.assertEqual(generate_monthly_payments(self.period, 15), (0, 1, 0))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.amount, Decimal("18000"))
        self.assertEqual(self.payment.due_date.day, 10)

    def test_generation_uses_membership_plan_and_skips_unpriced_members(self):
        Person.objects.create(user=self.other, id_number=23456789, name="Luis", surname="Lopez")
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
        self.assertEqual(generate_monthly_payments(earlier_period, 10), (0, 0, 0))

    def test_status_tracks_due_date(self):
        self.payment.due_date = self.today - timedelta(days=1)
        self.assertEqual(self.payment.status, "overdue")
        self.payment.due_date = self.today
        self.assertEqual(self.payment.status, "pending")
        self.payment.paid_on = self.today
        self.assertEqual(self.payment.status, "paid")

    def test_model_and_database_guards(self):
        self.payment.period = self.period.replace(day=2)
        with self.assertRaises(ValidationError):
            self.payment.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            MonthlyPayment.objects.create(member=self.member, period=self.period, amount=100, due_date=self.period)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MonthlyPayment.objects.create(member=self.other, period=self.period, amount=-1, due_date=self.period)
