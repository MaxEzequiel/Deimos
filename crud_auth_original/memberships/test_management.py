from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.services.estadisticas_service import EstadisticasService
from checkin.models import CheckIn
from checkin.services import member_checkin_status
from core.models import AuditLog
from memberships.models import Membership
from memberships.services import next_month_expiry
from payments.models import MonthlyPayment
from payments.services import generate_monthly_payments
from people.models import Person
from plans.models import Plan


class MemberManagementTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.admin = User.objects.create_superuser("admin", "", "AdminTest1!")
		cls.member = User.objects.create_user("ana")
		cls.person = Person.objects.create(
			user=cls.member, id_number=12345678, name="Ana", surname="Pérez"
		)
		cls.plan = Plan.objects.create(
			name="Completo",
			description="Todas las actividades",
			base_price=18000,
		)
		cls.person.plan = cls.plan
		cls.person.save(update_fields=["plan"])

	def setUp(self):
		self.client.force_login(self.admin)
		self.today = timezone.localdate()
		self.period = self.today.replace(day=1)
		self.url = reverse("manage_member", args=[self.member.pk])

	def payment_data(self, **overrides):
		return {
			"plan": self.plan.pk,
			"status": "active",
			"period": self.period.strftime("%Y-%m"),
			"amount": "18000.00",
			"paid_on": self.today.isoformat(),
			"method": "cash",
			"reference": "REC-123",
			**overrides,
		}

	def test_management_pages_render_without_writing(self):
		for url in [
			reverse("member_list"),
			self.url,
			reverse("manage_member", args=[self.admin.pk]),
		]:
			self.assertEqual(self.client.get(url).status_code, 200)
		self.assertFalse(Membership.objects.exists())
		self.assertFalse(MonthlyPayment.objects.exists())

	def test_selected_plan_and_payment_are_saved_together(self):
		plan = Plan.objects.create(name="Nuevo", base_price=25000)
		response = self.client.post(
			self.url, self.payment_data(plan=plan.pk, amount="25000"),
		)
		self.assertRedirects(response, self.url)
		self.assertEqual(
			Membership.objects.get(user=self.member).plan_id, plan.pk,
		)
		self.person.refresh_from_db()
		self.assertEqual(self.person.plan_id, plan.pk)
		payment = MonthlyPayment.objects.get(member=self.member)
		self.assertEqual(payment.amount, Decimal("25000"))
		self.assertEqual(payment.movements.get().amount, Decimal("25000"))

	def test_plan_cannot_be_saved_without_payment(self):
		response = self.client.post(
			self.url, {"plan": self.plan.pk, "status": "active"},
		)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context["payment_form"].errors)
		self.assertFalse(Membership.objects.exists())
		self.assertFalse(MonthlyPayment.objects.exists())

	def test_payment_failure_rolls_back_selected_plan(self):
		membership = Membership.objects.create(
			user=self.member, plan=self.plan, status="inactive",
		)
		plan = Plan.objects.create(name="Nuevo", base_price=25000)
		from django.core.exceptions import ValidationError

		with patch(
			"memberships.management_views.register_member_payment",
			side_effect=ValidationError("No se pudo registrar el pago"),
		):
			response = self.client.post(
				self.url, self.payment_data(plan=plan.pk, amount="25000"),
			)
		self.assertEqual(response.status_code, 200)
		membership.refresh_from_db()
		self.person.refresh_from_db()
		self.assertEqual(membership.plan_id, self.plan.pk)
		self.assertEqual(membership.status, "inactive")
		self.assertEqual(self.person.plan_id, self.plan.pk)
		self.assertFalse(MonthlyPayment.objects.exists())

	def test_failed_payment_keeps_previous_plan_and_status(self):
		membership = Membership.objects.create(
			user=self.member, plan=self.plan, status="inactive",
		)
		plan = Plan.objects.create(name="Nuevo", base_price=25000)
		response = self.client.post(
			self.url, self.payment_data(plan=plan.pk, amount="1"),
		)
		self.assertEqual(response.status_code, 200)
		membership.refresh_from_db()
		self.person.refresh_from_db()
		self.assertEqual(membership.plan_id, self.plan.pk)
		self.assertEqual(membership.status, "inactive")
		self.assertEqual(self.person.plan_id, self.plan.pk)
		self.assertFalse(MonthlyPayment.objects.exists())

	def test_search_by_dni_and_name(self):
		for q in ["12345678", "Ana", "Pérez"]:
			response = self.client.get(reverse("member_list"), {"q": q})
			self.assertEqual(
				[user.pk for user in response.context["page"]], [self.member.pk]
			)
		self.assertEqual(
			self.client.get(reverse("member_list"), {"q": "nobody"})
			.context["page"]
			.paginator.count,
			0,
		)

	def test_regular_member_cannot_manage_other_or_own_finances(self):
		self.client.force_login(self.member)
		for url in [self.url]:
			self.assertEqual(self.client.get(url).status_code, 403)
			self.assertEqual(
				self.client.post(url, self.payment_data()).status_code, 403
			)
		self.assertFalse(MonthlyPayment.objects.exists())

	def test_guests_redirect_to_login(self):
		self.client.logout()
		self.assertEqual(self.client.get(self.url).status_code, 302)

	def test_unknown_member_returns_404(self):
		self.assertEqual(
			self.client.get(
				reverse("manage_member", args=[999999])
			).status_code,
			404,
		)

	def test_assign_plan_and_membership_synchronizes_person_and_generation(
		self,
	):
		response = self.client.post(
			self.url,
			self.payment_data(),
		)
		self.assertRedirects(response, self.url)
		membership = Membership.objects.get(user=self.member)
		self.person.refresh_from_db()
		self.assertEqual(membership.plan_id, self.plan.pk)
		self.assertEqual(self.person.plan_id, self.plan.pk)
		self.assertEqual(membership.status, "active")
		self.assertEqual(generate_monthly_payments(self.period, 10), (0, 1, 0))
		self.assertEqual(
			MonthlyPayment.objects.get(member=self.member).amount,
			Decimal("18000"),
		)
		response = self.client.get(self.url)
		self.assertEqual(
			response.context["payment_form"].initial["amount"], Decimal("18000")
		)

	def test_invalid_plan_or_status_does_not_save_membership(self):
		for data in [
			{"plan": 999999, "status": "active"},
			{"plan": self.plan.pk, "status": "invalid"},
		]:
			response = self.client.post(
				self.url, {"action": "membership", **data}
			)
			self.assertEqual(response.status_code, 200)
			self.assertTrue(response.context["membership_form"].errors)
		self.assertFalse(Membership.objects.exists())

	def test_payment_creates_charge_and_preserves_active_membership(self):
		response = self.client.post(self.url, self.payment_data())
		self.assertRedirects(response, self.url)
		payment = MonthlyPayment.objects.get(member=self.member)
		self.assertEqual(payment.paid_on, self.today)
		self.assertEqual(payment.recorded_by_id, self.admin.pk)
		self.assertEqual(
			payment.reference, f"PAGO-{payment.movements.get().pk:08d}"
		)
		self.assertEqual(
			Membership.objects.get(user=self.member).status, "active"
		)
		self.assertEqual(
			member_checkin_status(self.person)["membership_status"], "active"
		)
		checkin = CheckIn.objects.create(
			dni="12345678", person=self.person, registrado_por=self.admin
		)
		response = self.client.get(
			reverse("checkin_success", args=[checkin.pk])
		)
		self.assertEqual(response.context["last_paid_on"], self.today)
		self.assertEqual(
			response.context["membership_expires_at"],
			next_month_expiry(self.today),
		)
		self.assertEqual(EstadisticasService.resumen_membresias()["activas"], 1)
		self.client.force_login(self.member)
		home = self.client.get(reverse("home"))
		self.assertEqual(home.context["membership"].plan_id, self.plan.pk)
		self.assertContains(home, "Tu membresía está activa")
		self.assertEqual(
			[
				m.charge_id
				for m in self.client.get(reverse("payment_history")).context[
					"movements"
				]
			],
			[payment.pk],
		)

	def test_existing_pending_charge_is_paid_without_duplicate(self):
		payment = MonthlyPayment.objects.create(
			member=self.member,
			period=self.period,
			amount=18000,
			due_date=self.period,
		)
		response = self.client.post(self.url, self.payment_data())
		self.assertRedirects(response, self.url)
		self.assertEqual(MonthlyPayment.objects.count(), 1)
		payment.refresh_from_db()
		self.assertEqual(payment.paid_on, self.today)
		self.assertEqual(payment.due_date, self.period)

	def test_repeat_payment_preserves_original_receipt(self):
		self.client.post(self.url, self.payment_data())
		response = self.client.post(
			self.url, self.payment_data(reference="DIFFERENT")
		)
		self.assertEqual(response.status_code, 200)
		self.assertIn("period", response.context["payment_form"].errors)
		self.assertEqual(MonthlyPayment.objects.count(), 1)
		payment = MonthlyPayment.objects.get()
		self.assertEqual(
			payment.reference, f"PAGO-{payment.movements.get().pk:08d}"
		)

	def test_price_change_does_not_change_pending_or_paid_charges(self):
		Membership.objects.create(user=self.member, plan=self.plan)
		pending = MonthlyPayment.objects.create(
			member=self.member,
			period=self.period,
			amount=10000,
			due_date=self.period,
		)
		other_plan = Plan.objects.create(
			name="Nuevo", description="Otro plan", base_price=25000
		)
		self.client.post(
			self.url,
			{"action": "membership", "plan": other_plan.pk, "status": "active"},
		)
		self.assertEqual(
			self.client.get(self.url).context["payment_form"].initial["amount"],
			Decimal("10000"),
		)
		response = self.client.post(self.url, self.payment_data(amount="25000"))
		self.assertIn("amount", response.context["payment_form"].errors)
		pending.refresh_from_db()
		self.assertIsNone(pending.paid_on)
		self.assertEqual(pending.amount, Decimal("10000"))

	def test_invalid_payment_does_not_create_records(self):
		for data in [
			self.payment_data(amount="-1"),
			self.payment_data(period="bad"),
			self.payment_data(
				paid_on=(self.today + timedelta(days=1)).isoformat()
			),
		]:
			response = self.client.post(self.url, data)
			self.assertEqual(response.status_code, 200)
			self.assertTrue(response.context["payment_form"].errors)
		self.assertFalse(MonthlyPayment.objects.exists())
		self.assertFalse(Membership.objects.exists())

	def test_failure_in_audit_rolls_back_payment_and_membership(self):
		with patch(
			"memberships.management_views.audit",
			side_effect=IntegrityError("Audit unavailable"),
		):
			with self.assertRaises(IntegrityError):
				self.client.post(self.url, self.payment_data())
		self.assertFalse(MonthlyPayment.objects.exists())
		self.assertFalse(Membership.objects.exists())

	def test_payment_from_subscriptions_preserves_active_membership(self):
		Membership.objects.create(
			user=self.member, plan=self.plan, status="active"
		)
		MonthlyPayment.objects.create(
			member=self.member,
			period=self.period,
			amount=18000,
			due_date=self.period,
		)
		self.client.post(
			reverse("pay_subscription", args=[self.member.pk]),
			self.payment_data(),
		)
		self.assertEqual(
			Membership.objects.get(user=self.member).effective_status, "active"
		)

	def test_profile_plan_is_preserved_when_payment_creates_membership(self):
		self.person.plan = self.plan
		self.person.save(update_fields=["plan"])
		self.client.post(self.url, self.payment_data())
		self.person.refresh_from_db()
		self.assertEqual(self.person.plan_id, self.plan.pk)
		self.assertEqual(
			Membership.objects.get(user=self.member).plan_id, self.plan.pk
		)

	def test_plan_changes_in_either_model_are_synchronized(self):
		membership = Membership.objects.create(user=self.member)
		self.person.plan = self.plan
		self.person.save(update_fields=["plan"])
		membership.refresh_from_db()
		self.assertEqual(membership.plan_id, self.plan.pk)
		membership.plan = None
		membership.save(update_fields=["plan"])
		self.person.refresh_from_db()
		self.assertIsNone(self.person.plan_id)

	def test_expiration_is_reflected_in_home_management_and_statistics(self):
		self.client.post(self.url, self.payment_data())
		after_expiry = next_month_expiry(self.today) + timedelta(days=1)
		with patch(
			"django.utils.timezone.localdate", return_value=after_expiry
		):
			self.assertEqual(
				Membership.objects.get(user=self.member).effective_status,
				"inactive",
			)
			self.assertEqual(
				EstadisticasService.resumen_membresias()["activas"], 0
			)
			response = self.client.get(reverse("member_list"), {"q": "ana"})
			self.assertEqual(
				response.context["page"][0].membership.effective_status,
				"inactive",
			)
			self.client.force_login(self.member)
			self.assertEqual(
				self.client.get(reverse("home")).context["estado"], "inactive"
			)

	def test_account_without_person_can_receive_membership_and_payment(self):
		user = User.objects.create_user("noprofile")
		url = reverse("manage_member", args=[user.pk])
		self.assertContains(self.client.get(url), "Completá su perfil y DNI")
		self.client.post(url, self.payment_data())
		self.assertEqual(
			Membership.objects.get(user=user).effective_status, "active"
		)
		self.assertTrue(MonthlyPayment.objects.filter(member=user).exists())

	def test_completing_person_profile_preserves_previously_assigned_plan(self):
		user = User.objects.create_user("newprofile")
		Membership.objects.create(user=user, plan=self.plan)
		person = Person.objects.create(
			user=user, id_number=23456789, name="Luis", surname="Pérez"
		)
		self.assertEqual(person.plan_id, self.plan.pk)
		self.assertEqual(
			Membership.objects.get(user=user).plan_id, self.plan.pk
		)

	def test_creating_membership_preserves_previously_assigned_person_plan(
		self,
	):
		self.person.plan = self.plan
		self.person.save(update_fields=["plan"])
		membership = Membership.objects.create(user=self.member)
		self.person.refresh_from_db()
		self.assertEqual(membership.plan_id, self.plan.pk)
		self.assertEqual(self.person.plan_id, self.plan.pk)
