from datetime import date

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from checkin.forms import CheckInForm
from checkin.models import CheckIn
from people.models import Person
from payments.models import MonthlyPayment
from checkin.services import member_checkin_status, next_month_expiry


class CheckInValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = User.objects.create_superuser("reception", "", "Reception1!")
        cls.member = User.objects.create_user("ana")
        cls.person = Person.objects.create(user=cls.member, id_number=12345678, name="Ana", surname="Pérez")

    def setUp(self):
        self.client.force_login(self.operator)

    def test_unknown_dni_is_rejected_without_creating_checkin(self):
        response = self.client.post(reverse("checkin_home"), {"dni": "23456789"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("dni", response.context["form"].errors)
        self.assertFalse(CheckIn.objects.exists())

    def test_existing_dni_is_enough_even_without_membership_or_payment(self):
        response = self.client.post(reverse("checkin_home"), {"dni": " 12345678 "})
        checkin = CheckIn.objects.get()
        self.assertEqual(checkin.person_id, self.person.pk)
        self.assertRedirects(response, reverse("checkin_success", args=[checkin.pk]))

    def test_duplicate_dni_is_rejected_without_guessing_member(self):
        other = User.objects.create_user("other")
        Person.objects.create(user=other, id_number=12345678, name="Otra", surname="Persona")
        self.assertFalse(CheckInForm({"dni": "12345678"}).is_valid())
        self.client.post(reverse("checkin_home"), {"dni": "12345678"})
        self.assertFalse(CheckIn.objects.exists())

    def test_deactivated_account_does_not_add_an_extra_entry_requirement(self):
        self.member.is_active = False
        self.member.save(update_fields=["is_active"])
        self.assertTrue(CheckInForm({"dni": "12345678"}).is_valid())

    def test_operator_with_add_permission_can_see_own_confirmation(self):
        operator = User.objects.create_user("entryonly")
        operator.user_permissions.add(Permission.objects.get(content_type__app_label="checkin", codename="add_checkin"))
        self.client.force_login(operator)
        response = self.client.post(reverse("checkin_home"), {"dni": "12345678"})
        self.assertRedirects(response, reverse("checkin_success", args=[CheckIn.objects.get().pk]))
        other_checkin = CheckIn.objects.create(dni="12345678", person=self.person, registrado_por=self.operator)
        self.assertEqual(self.client.get(reverse("checkin_success", args=[other_checkin.pk])).status_code, 404)


class MembershipIndicatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = User.objects.create_superuser("admin", "", "AdminTest1!")
        cls.member = User.objects.create_user("member")
        cls.person = Person.objects.create(user=cls.member, id_number=12345678, name="Ana María", surname="Pérez")

    def paid_month(self, period=date(2026, 10, 1), paid_on=date(2026, 10, 2)):
        return MonthlyPayment.objects.create(member=self.member, period=period, due_date=period.replace(day=10), amount=200, paid_on=paid_on)

    def test_paid_month_is_green_before_last_five_days(self):
        payment = self.paid_month()
        status = member_checkin_status(self.person, date(2026, 10, 27))
        self.assertEqual(status["membership_status"], "active")
        self.assertEqual(status["days_remaining"], 6)
        self.assertEqual(status["member_initials"], "AP")
        self.assertEqual(status["member_name"], "Ana María Pérez")
        self.assertEqual(status["member_registered_at"], self.member.date_joined)
        self.assertEqual(status["last_paid_on"], payment.paid_on)
        self.assertEqual(status["membership_expires_at"], date(2026, 11, 2))

    def test_orange_includes_five_days_and_expiry_day(self):
        self.paid_month()
        for today in [date(2026, 10, 28), date(2026, 10, 29), date(2026, 10, 30), date(2026, 10, 31), date(2026, 11, 1), date(2026, 11, 2)]:
            with self.subTest(today=today):
                status = member_checkin_status(self.person, today)
                self.assertEqual(status["membership_status"], "expiring")
        self.assertEqual(member_checkin_status(self.person, date(2026, 11, 2))["membership_detail"], "Vence hoy")

    def test_expired_payment_is_red_and_future_payment_date_is_ignored(self):
        self.paid_month(date(2026, 9, 1), date(2026, 9, 5))
        self.paid_month(date(2026, 11, 1), date(2026, 11, 5))
        status = member_checkin_status(self.person, date(2026, 10, 15))
        self.assertEqual(status["membership_status"], "expired")
        self.assertEqual(status["last_paid_on"], date(2026, 9, 5))

    def test_unpaid_fee_is_red_and_does_not_block_checkin(self):
        MonthlyPayment.objects.create(member=self.member, period=date(2026, 10, 1), due_date=date(2026, 10, 10), amount=200)
        self.assertEqual(member_checkin_status(self.person, date(2026, 10, 5))["membership_status"], "expired")

    def test_coverage_continues_in_next_month_until_payment_anniversary(self):
        self.paid_month()
        self.assertEqual(member_checkin_status(self.person, date(2026, 11, 1))["membership_status"], "expiring")
        self.assertEqual(member_checkin_status(self.person, date(2026, 11, 3))["membership_status"], "expired")

    def test_leap_february_expiry(self):
        self.paid_month(date(2028, 1, 1), date(2028, 1, 31))
        status = member_checkin_status(self.person, date(2028, 2, 24))
        self.assertEqual(status["membership_expires_at"], date(2028, 2, 29))
        self.assertEqual(status["membership_status"], "expiring")

    def test_future_payment_date_does_not_activate_month(self):
        self.paid_month(paid_on=date(2026, 10, 20))
        self.assertEqual(member_checkin_status(self.person, date(2026, 10, 15))["membership_status"], "expired")

    def test_confirmation_contains_member_payment_and_indicator(self):
        self.paid_month()
        self.client.force_login(self.operator)
        with patch("checkin.services.timezone.localdate", return_value=date(2026, 10, 28)):
            response = self.client.post(reverse("checkin_home"), {"dni": "12345678"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana María Pérez")
        self.assertContains(response, "AP")
        self.assertContains(response, "02/10/2026")
        self.assertContains(response, "Próxima a vencer")
        self.assertEqual(response.context["membership_status"], "expiring")

    def test_payment_on_fifteenth_expires_on_fifteenth_next_month(self):
        self.assertEqual(next_month_expiry(date(2026, 10, 15)), date(2026, 11, 15))

    def test_short_month_and_year_boundary(self):
        self.assertEqual(next_month_expiry(date(2026, 1, 31)), date(2026, 2, 28))
        self.assertEqual(next_month_expiry(date(2026, 12, 15)), date(2027, 1, 15))

    def test_latest_payment_controls_coverage(self):
        self.paid_month(date(2026, 9, 1), date(2026, 9, 15))
        self.paid_month(date(2026, 10, 1), date(2026, 10, 12))
        status = member_checkin_status(self.person, date(2026, 10, 16))
        self.assertEqual(status["last_paid_on"], date(2026, 10, 12))
        self.assertEqual(status["membership_expires_at"], date(2026, 11, 12))
        self.assertEqual(status["membership_status"], "active")

    def test_legacy_checkin_without_person_renders_safely(self):
        self.client.force_login(self.operator)
        checkin = CheckIn.objects.create(dni="unknown", registrado_por=self.operator)
        response = self.client.get(reverse("checkin_success", args=[checkin.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["member_initials"], "?")
