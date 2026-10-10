from decimal import Decimal
from datetime import date

from checkin.models import CheckIn
from accounts.services.estadisticas_service import EstadisticasService

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
		self.inactive_member = get_user_model().objects.create_user(
			username="socio-inactivo"
		)
		self.plan = Plan.objects.create(
			name="Mensual", base_price=Decimal("100.00")
		)
		Membership.objects.create(
			user=self.member, plan=self.plan, status="active"
		)
		Membership.objects.create(
			user=self.inactive_member, plan=self.plan, status="inactive"
		)
		self.client.force_login(self.admin)

	def test_payment_report_includes_payments_and_reversals_for_selected_period(
		self,
	):
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
		self.assertEqual(report.context["resumen_pagos"]["pagos_cantidad"], 1)
		self.assertEqual(
			report.context["resumen_pagos"]["anulaciones_cantidad"], 1
		)
		self.assertEqual(
			report.context["resumen_pagos"]["pagos_monto"], Decimal("100.00")
		)
		self.assertEqual(
			report.context["resumen_pagos"]["anulaciones_monto"],
			Decimal("100.00"),
		)
		self.assertEqual(reversal.amount, Decimal("-100.00"))

		chart_data = self.client.get(
			reverse("estadisticas_data"), period
		).json()
		self.assertEqual(
			chart_data["pagos_mes"],
			[{"mes": today.month, "pagos": 1, "anulaciones": 1}],
		)

	def test_subscription_report_and_chart_group_by_plan_and_status(self):
		today = timezone.localdate()
		register_member_payment(
			self.member,
			{
				"period": today.replace(day=1),
				"paid_on": today,
				"amount": Decimal("100.00"),
			},
			self.admin,
		)
		report = self.client.get(reverse("estadisticas_dashboard"))
		self.assertEqual(report.status_code, 200)
		self.assertEqual(
			report.context["resumen_suscripciones"],
			{"total": 2, "activas": 1, "inactivas": 1},
		)

		chart_data = self.client.get(reverse("estadisticas_data")).json()
		self.assertEqual(
			chart_data["suscripciones_por_plan"],
			[{"plan": "Mensual", "activas": 1, "inactivas": 1, "cantidad": 2}],
		)
		self.assertNotIn("por_grupo", chart_data)
		self.assertNotIn("membresias_estado", chart_data)
		self.assertNotContains(report, "Informe de pagos y anulaciones")
		self.assertNotContains(report, "Informe de suscripciones")
		self.assertNotContains(report, "graficoGrupo")
		self.assertNotContains(report, "graficoMembresiasEstado")

	def test_daily_activity_filters_period_and_accounts_for_reversals(self):
		dia = date(2024, 2, 28)
		payment = register_member_payment(
			self.member,
			{"period": dia.replace(day=1), "amount": Decimal("100.00"), "paid_on": dia},
			self.admin,
		)
		reversal = reverse_payment(payment.movements.get().pk, self.admin)
		reversal.paid_on = date(2024, 2, 29)
		reversal.save(update_fields=["paid_on"])
		CheckIn.objects.create(dni="12345678", fecha=dia)
		CheckIn.objects.create(dni="12345678", fecha=dia)
		CheckIn.objects.create(dni="87654321", fecha=date(2024, 3, 1))
		period = {"anio": 2024, "mes": 2}
		data = self.client.get(reverse("estadisticas_data"), period).json()["actividad_diaria"]
		self.assertEqual(len(data), 29)
		self.assertEqual(data[0]["checkins"], 0)
		self.assertEqual(data[27]["checkins"], 2)
		self.assertEqual(Decimal(data[27]["ingresos"]), Decimal("100.00"))
		self.assertEqual(Decimal(data[28]["anulaciones"]), Decimal("100.00"))
		self.assertEqual(Decimal(data[28]["neto"]), Decimal("-100.00"))
		report = self.client.get(reverse("estadisticas_dashboard"), period)
		self.assertEqual(report.context["total_checkins"], 2)
		self.assertEqual(len(report.context["ingresos_diarios"]), 2)
		self.assertEqual(len(report.context["checkins_diarios"]), 1)
		self.assertContains(report, "Registro diario de ingresos")
		self.assertContains(report, "Registro diario de check-ins")
		self.assertNotContains(report, "Registro diario de ingresos y check-ins")
		self.assertContains(report, "graficoIngresosDia")
		self.assertContains(report, "graficoCheckinsDia")
		self.assertEqual(len(EstadisticasService.actividad_por_dia(2024)), 366)

	def test_daily_activity_empty_period_and_checkin_year(self):
		CheckIn.objects.create(dni="12345678", fecha=date(2020, 1, 1))
		self.assertIn(2020, EstadisticasService.anios_disponibles())
		report = self.client.get(reverse("estadisticas_dashboard"), {"anio": 2024, "mes": 2})
		self.assertEqual(report.context["total_checkins"], 0)
		self.assertContains(report, "No hay ingresos ni anulaciones")
		self.assertContains(report, "No hay check-ins")

	def test_checkin_summary_and_detailed_report(self):
		CheckIn.objects.create(dni="12345678", fecha=date(2024, 2, 28))
		CheckIn.objects.create(dni="12345678", fecha=date(2024, 2, 28))
		CheckIn.objects.create(dni="87654321", fecha=date(2023, 1, 1))
		period = {"anio": 2024, "mes": 2}
		dashboard = self.client.get(reverse("estadisticas_dashboard"), period)
		self.assertEqual(dashboard.context["resumen_checkins"], {"total": 2})
		self.assertNotContains(dashboard, "Promedio por")
		self.assertNotContains(dashboard, "Personas distintas")
		report = self.client.get(reverse("estadisticas_checkins"), period)
		self.assertEqual(report.status_code, 200)
		self.assertEqual(len(report.context["checkins"]), 2)
		self.assertContains(report, "12345678", count=2)
		self.assertNotContains(report, "87654321")
		all_report = self.client.get(reverse("estadisticas_checkins"), {"todos": "1"})
		self.assertEqual(len(all_report.context["checkins"]), 3)
		self.assertEqual(all_report.context["resumen_checkins"]["total"], 3)
		self.client.force_login(self.member)
		self.assertEqual(self.client.get(reverse("estadisticas_checkins")).status_code, 403)

	def test_daily_income_date_filter_and_totals(self):
		dia = date(2024, 2, 28)
		payment = register_member_payment(self.member, {"period": dia.replace(day=1), "amount": Decimal("100.00"), "paid_on": dia}, self.admin)
		reversal = reverse_payment(payment.movements.get().pk, self.admin)
		reversal.paid_on = date(2024, 2, 29)
		reversal.save(update_fields=["paid_on"])
		url = reverse("estadisticas_dashboard")
		report = self.client.get(url, {"anio": 2025, "desde": "2024-02-28", "hasta": "2024-02-28"})
		self.assertEqual(report.status_code, 200)
		self.assertEqual(len(report.context["ingresos_diarios"]), 1)
		self.assertEqual(report.context["totales_ingresos"]["neto"], Decimal("100.00"))
		report = self.client.get(url, {"desde": "2024-02-28", "hasta": "2024-02-29"})
		self.assertEqual(report.context["totales_ingresos"], {"ingresos": Decimal("100.00"), "anulaciones": Decimal("100.00"), "neto": Decimal("0.00")})
		self.assertEqual(self.client.get(url, {"desde": "2024-03-01", "hasta": "2024-02-28"}).status_code, 400)
		self.assertEqual(self.client.get(url, {"desde": "invalid"}).status_code, 400)

	def test_checkin_report_filters_name_dni_and_dates(self):
		from people.models import Person
		person = Person.objects.create(user=self.member, id_number=12345678, name="Ana", surname="Perez")
		CheckIn.objects.create(dni="12345678", person=person, fecha=date(2024, 2, 28))
		CheckIn.objects.create(dni="12345678", person=person, fecha=date(2024, 2, 29))
		CheckIn.objects.create(dni="87654321", fecha=date(2024, 2, 28))
		url = reverse("estadisticas_checkins")
		filters = {"todos": "1", "nombre": "ana perez", "dni": "1234", "desde": "2024-02-28", "hasta": "2024-02-28"}
		report = self.client.get(url, filters)
		self.assertEqual(report.status_code, 200)
		self.assertEqual(len(report.context["checkins"]), 1)
		self.assertEqual(report.context["resumen_checkins"]["total"], 1)
		self.assertContains(report, 'value="ana perez"')
		self.assertEqual(self.client.get(url, {"todos": "1", "dni": "8765"}).context["resumen_checkins"]["total"], 1)
		self.assertEqual(self.client.get(url, {"todos": "1", "nombre": "ausente"}).context["resumen_checkins"]["total"], 0)
		self.assertEqual(self.client.get(url, {"desde": "2024-03-01", "hasta": "2024-02-28"}).status_code, 400)
		self.assertEqual(self.client.get(url, {"desde": "invalid"}).status_code, 400)

	def test_checkin_weekday_report_and_filter(self):
		CheckIn.objects.create(dni="12345678", fecha=date(2024, 2, 26))
		CheckIn.objects.create(dni="87654321", fecha=date(2024, 2, 26))
		CheckIn.objects.create(dni="12345678", fecha=date(2024, 2, 27))
		CheckIn.objects.create(dni="12345678", fecha=date(2023, 2, 27))
		url = reverse("estadisticas_checkins")
		params = {"todos": "1", "desde": "2024-02-26", "hasta": "2024-02-27", "dia_semana": "2"}
		report = self.client.get(url, params)
		self.assertEqual(report.status_code, 200)
		self.assertEqual(report.context["resumen_checkins"]["total"], 1)
		self.assertEqual(report.context["dias_mayor_asistencia"][0]["nombre"], "Lunes")
		self.assertEqual([dia["total"] for dia in report.context["asistencia_semana"]], [2, 1, 0, 0, 0, 0, 0])
		params["dni"] = "12345678"
		report = self.client.get(url, params)
		self.assertEqual(len(report.context["dias_mayor_asistencia"]), 2)
		self.assertEqual(self.client.get(url, {"dia_semana": "8"}).status_code, 400)
		self.assertEqual(self.client.get(url, {"anio": 2020}).context["dias_mayor_asistencia"], [])
