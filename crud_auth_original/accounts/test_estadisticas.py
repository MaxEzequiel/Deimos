from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from memberships.models import Membership
from payments.services import register_member_payment, reverse_payment
from plans.models import Plan


class EstadisticasReportTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="AdminTest1!"
        )
        self.member = get_user_model().objects.create_user(username="socio")
        self.inactive_member = get_user_model().objects.create_user(username="socio-inactivo")
        self.plan = Plan.objects.create(name="Mensual", base_price=Decimal("100.00"))
        Membership.objects.create(user=self.member, plan=self.plan, status="active")
        Membership.objects.create(user=self.inactive_member, plan=self.plan, status="inactive")
        self.client.force_login(self.admin)

    def test_payment_report_includes_payments_and_reversals_for_selected_period(self):
        today = timezone.localdate()
        payment = register_member_payment(
            self.member,
            {
                "period": today.replace(day=1),
                "amount": Decimal("100.00"),
                "paid_on": today,
            },
            self.admin,
        )
        reversal = reverse_payment(payment.movements.get().pk, self.admin)
        period = {"anio": today.year, "mes": today.month}

        report = self.client.get(reverse("estadisticas_dashboard"), period)
        self.assertEqual(report.status_code, 200)
        self.assertEqual(len(report.context["informe_pagos"]), 2)
        self.assertEqual(report.context["resumen_pagos"]["pagos_cantidad"], 1)
        self.assertEqual(report.context["resumen_pagos"]["anulaciones_cantidad"], 1)
        self.assertEqual(report.context["resumen_pagos"]["pagos_monto"], Decimal("100.00"))
        self.assertEqual(report.context["resumen_pagos"]["anulaciones_monto"], Decimal("100.00"))
        self.assertEqual(reversal.amount, Decimal("-100.00"))

        chart_data = self.client.get(reverse("estadisticas_data"), period).json()
        self.assertEqual(chart_data["pagos_mes"], [
            {"mes": today.month, "pagos": 1, "anulaciones": 1}
        ])

    def test_subscription_report_and_chart_group_by_plan_and_status(self):
        today = timezone.localdate()
        register_member_payment(self.member, {
            "period": today.replace(day=1), "paid_on": today,
            "amount": Decimal("100.00"),
        }, self.admin)
        report = self.client.get(reverse("estadisticas_dashboard"))
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.context["resumen_suscripciones"], {
            "total": 2, "activas": 1, "inactivas": 1
        })
        self.assertEqual(len(report.context["informe_suscripciones"]), 2)

        chart_data = self.client.get(reverse("estadisticas_data")).json()
        self.assertEqual(chart_data["suscripciones_por_plan"], [{
            "plan": "Mensual", "activas": 1, "inactivas": 1, "cantidad": 2
        }])
        self.assertNotIn("por_grupo", chart_data)
        self.assertNotIn("membresias_estado", chart_data)
        self.assertContains(report, "Informe de pagos y anulaciones")
        self.assertContains(report, "Informe de suscripciones")
        self.assertNotContains(report, "graficoGrupo")
        self.assertNotContains(report, "graficoMembresiasEstado")
