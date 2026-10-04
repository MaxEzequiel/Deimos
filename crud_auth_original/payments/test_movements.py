from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from memberships.models import Membership
from plans.models import Plan
from .models import MonthlyPayment, PaymentMovement
from .services import register_member_payment, reverse_payment


class PaymentFlowTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(username="operator", password="test")
        self.member = get_user_model().objects.create_user(username="subscriber")
        self.other = get_user_model().objects.create_user(username="other")
        self.plan = Plan.objects.create(name="Plan", base_price=100)
        Membership.objects.create(user=self.member, plan=self.plan, status="active")
        self.data = {"period": timezone.localdate().replace(day=1), "amount": Decimal("100"), "paid_on": timezone.localdate()}
        self.client.force_login(self.admin)

    def pay(self):
        charge = register_member_payment(self.member, self.data, self.admin)
        return charge, charge.movements.get(amount__gt=0, reversal__isnull=True)

    def test_reversal_keeps_original_and_allows_repayment(self):
        charge, original = self.pay()
        reversal = reverse_payment(original.pk, self.admin)
        self.assertEqual(reversal.amount, -original.amount)
        self.assertEqual(reversal.reversal_of_id, original.pk)
        original.refresh_from_db()
        self.assertEqual(original.amount, 100)
        charge.refresh_from_db()
        self.assertIsNone(charge.paid_on)
        with self.assertRaises(ValidationError): reverse_payment(original.pk, self.admin)
        with self.assertRaises(ValidationError): reverse_payment(reversal.pk, self.admin)
        register_member_payment(self.member, self.data, self.admin)
        self.assertEqual(PaymentMovement.objects.count(), 3)
        self.assertEqual(sum(PaymentMovement.objects.values_list("amount", flat=True)), 100)

    def test_subscription_payment_history_filter_and_cancellation(self):
        url = reverse("pay_subscription", args=[self.member.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(MonthlyPayment.objects.exists())
        response = self.client.post(url, {**self.data, "period": self.data["period"].strftime("%Y-%m"), "paid_on": self.data["paid_on"].isoformat()})
        self.assertRedirects(response, reverse("payment_history"))
        movement = PaymentMovement.objects.get()
        response = self.client.get(reverse("payment_history"), {"member_id": self.member.pk, "payment_id": movement.pk})
        self.assertEqual(list(response.context["movements"]), [movement])
        cancel = reverse("cancel_payment", args=[movement.pk])
        self.assertEqual(self.client.get(cancel).status_code, 200)
        self.assertEqual(PaymentMovement.objects.count(), 1)
        self.client.post(cancel)
        self.client.post(cancel)
        self.assertEqual(PaymentMovement.objects.count(), 2)
        self.assertEqual(self.client.get(reverse("payment_history")).context["total"], 0)

    def test_permissions_and_invalid_filters(self):
        charge, movement = self.pay()
        self.client.force_login(self.other)
        self.assertEqual(list(self.client.get(reverse("payment_history")).context["movements"]), [])
        self.assertEqual(self.client.post(reverse("cancel_payment", args=[movement.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("pay_subscription", args=[self.member.pk])).status_code, 403)
        self.client.force_login(self.admin)
        for value in ["abc", "-1", "9" * 100]:
            self.assertEqual(list(self.client.get(reverse("payment_history"), {"payment_id": value}).context["movements"]), [])

    def test_unified_subscriptions_include_members_without_plan(self):
        response = self.client.get(reverse("subscription_list"))
        self.assertEqual(response.templates[0].name, "memberships/member_list.html")
        self.assertContains(response, "Agregar plan")
        member = next(user for user in response.context["page"] if user.pk == self.member.pk)
        self.assertEqual(member.subscription_plan, self.plan)
        self.assertEqual(member.subscription_amount, 100)
        self.assertTrue(member.can_pay_subscription)
        self.client.force_login(self.other)
        response = self.client.get(reverse("subscription_list"))
        self.assertEqual([user.pk for user in response.context["page"]], [self.other.pk])
        self.assertNotContains(response, "Agregar plan")

    def test_removed_module_and_payment_method(self):
        for url in ["/payments/generate/", "/payments/1/record/"]:
            self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.get(reverse("pay_subscription", args=[self.member.pk]))
        self.assertNotIn("method", response.context["form"].fields)
        self.assertNotContains(response, "Medio de pago")
        self.assertNotContains(response, "> Mensualidades</a>")
        self.assertEqual(self.client.get("/payments/").status_code, 200)

    def test_coverage_is_preserved_and_cleared_on_reversal(self):
        from memberships.services import next_month_expiry
        charge, movement = self.pay()
        self.assertEqual(charge.coverage_start, self.data["paid_on"])
        self.assertEqual(charge.coverage_end, next_month_expiry(self.data["paid_on"]))
        reverse_payment(movement.pk, self.admin)
        charge.refresh_from_db()
        self.assertIsNone(charge.coverage_start)
        self.assertIsNone(charge.coverage_end)
