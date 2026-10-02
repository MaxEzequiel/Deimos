from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import Group, Permission, User
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.template.loader import get_template
from pathlib import Path
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from accounts.services.estadisticas_service import EstadisticasService
from accounts.services.reportes_service import ReportesService
from checkin.models import CheckIn
from classes.forms import CourseForm
from classes.models import Course, Inscription
from memberships.models import Membership
from people.models import Person
from plans.forms import PlanForm
from plans.models import Plan
from routines.models import Routine
from tutorials.models import Publication


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", "admin@example.com", "AdminTest1!")
        cls.member = User.objects.create_user("member", password="MemberTest1!")
        cls.person = Person.objects.create(user=cls.member, id_number=12345678, name="Ana", surname="Pérez", email="ana@example.com")
        cls.plan = Plan.objects.create(name="Mensual", description="Acceso completo", base_price=200)
        cls.course = Course.objects.create(name="Pilates", description="Clase semanal", teacher=cls.admin, starts_at=timezone.now() + timedelta(days=1), ends_at=timezone.now() + timedelta(days=1, hours=1), max_capacity=1)
        cls.publication = Publication.objects.create(title="Ejercicio", description="Descripción", content="Contenido", image="publications/test.png")
        cls.group = Group.objects.create(name="Socios")
        cls.checkin = CheckIn.objects.create(dni="12345678", registrado_por=cls.admin)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_pages_render_for_admin(self):
        pages = [
            ("home", []), ("list_accounts", []), ("create_account", []),
            ("edit_account", [self.member.pk]), ("edit_account", [self.admin.pk]),
            ("deactivate_account", [self.member.pk]), ("accounts_admin_home", []),
            ("accounts_admin_edit", [self.member.pk]), ("accounts_admin_group_list", []),
            ("accounts_admin_group_create", []), ("accounts_admin_group_edit", [self.group.pk]),
            ("create_plan", []), ("list_plans", []), ("edit_plan", [self.plan.pk]),
            ("delete_plan", [self.plan.pk]), ("create_class", []), ("list_class", []),
            ("edit_class", [self.course.pk]), ("delete_class", [self.course.pk]),
            ("inscription_question", [self.course.pk]), ("list_audit", []),
            ("checkin_home", []), ("checkin_history", []), ("checkin_success", [self.checkin.pk]),
            ("list_publications", []), ("detail_publication", [self.publication.pk]),
            ("create_publication", []), ("edit_publication", [self.publication.pk]),
            ("delete_publication", [self.publication.pk]), ("payment_list", []),
            ("generate_payments", []), ("edit_membership", []), ("password_change", []),
            ("estadisticas_dashboard", []), ("estadisticas_data", []), ("estadisticas_informe", []),
        ]
        for name, args in pages:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_all_project_templates_compile(self):
        root = Path(__file__).resolve().parent.parent
        for folder in root.glob("*/templates"):
            for template in folder.rglob("*.html"):
                with self.subTest(template=str(template)):
                    get_template(template.relative_to(folder).as_posix())

    def test_exports(self):
        for name, prefix in [("plans_pdf", b"%PDF"), ("estadisticas_pdf", b"%PDF"), ("estadisticas_excel", b"PK")]:
            with self.subTest(export=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.content.startswith(prefix))

    def test_members_cannot_manage_administrative_data(self):
        self.client.force_login(self.member)
        for name, args in [
            ("list_accounts", []), ("create_account", []), ("edit_account", [self.admin.pk]),
            ("deactivate_account", [self.admin.pk]), ("accounts_admin_home", []),
            ("accounts_admin_edit", [self.member.pk]), ("accounts_admin_group_list", []),
            ("accounts_admin_group_create", []), ("accounts_admin_group_edit", [self.group.pk]),
            ("list_audit", []), ("estadisticas_data", []), ("estadisticas_excel", []),
            ("checkin_home", []), ("checkin_history", []), ("edit_membership", []),
        ]:
            for method in [self.client.get, self.client.post]:
                with self.subTest(page=name, method=method.__name__):
                    self.assertEqual(method(reverse(name, args=args)).status_code, 403)
        self.assertEqual(self.client.post(reverse("create_account"), {"is_admin": "on"}).status_code, 403)

    def test_anonymous_group_management_redirects_to_login(self):
        self.client.logout()
        for name in ["accounts_admin_group_list", "accounts_admin_group_create"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_creation_preserves_admin_session_and_email(self):
        response = self.client.post(reverse("create_account"), {
            "username": "newmember", "password1": "ComplexPass1!", "password2": "ComplexPass1!",
            "id_number": 23456789, "name": "Luis", "surname": "Pérez", "email": "luis@example.com",
            "birth_date": "2000-01-01",
        })
        self.assertRedirects(response, reverse("list_accounts"))
        user = User.objects.get(username="newmember")
        self.assertEqual(user.email, user.person.email)
        self.assertFalse(user.is_superuser)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.admin.pk)
        self.assertTrue(Membership.objects.filter(user=user).exists())
        self.assertTrue(Routine.objects.filter(client=user.person).exists())

    def test_invalid_creation_shows_both_forms(self):
        response = self.client.post(reverse("create_account"), {})
        self.assertTrue(response.context["user_form"].errors)
        self.assertTrue(response.context["person_form"].errors)

    def test_email_sync_in_both_directions(self):
        person = Person.objects.get(pk=self.person.pk)
        person.email = "changed@example.com"
        person.save(update_fields=["email"])
        user = User.objects.get(pk=self.member.pk)
        self.assertEqual(user.email, person.email)
        user.email = "other@example.com"
        user.save(update_fields=["email"])
        person.refresh_from_db()
        self.assertEqual(person.email, user.email)
        person.email = ""
        person.save(update_fields=["email"])
        user.refresh_from_db()
        self.assertEqual(user.email, "")

    def test_password_reset_uses_profile_email(self):
        self.client.logout()
        response = self.client.post(reverse("password_reset"), {"email": "ana@example.com"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mail.outbox[0].to, ["ana@example.com"])
        self.assertIn("/accounts/reset/", mail.outbox[0].body)

    def test_login_missing_fields_and_safe_next(self):
        self.client.logout()
        self.assertEqual(self.client.post(reverse("login"), {}).status_code, 200)
        response = self.client.post(reverse("login"), {"username": "member", "password": "MemberTest1!", "next": "https://example.com"})
        self.assertRedirects(response, reverse("home"))
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "member", "password": "MemberTest1!", "next": reverse("payment_list")})
        self.assertRedirects(response, reverse("payment_list"))

    def test_logout_requires_post_and_csrf(self):
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse("logout")).status_code, 403)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))

    def test_permission_cache_after_mutations(self):
        user = User.objects.get(pk=self.member.pk)
        perm = Permission.objects.get(content_type__app_label="plans", codename="view_plan")
        self.assertFalse(user.has_perm("plans.view_plan"))
        user.user_permissions.add(perm)
        self.assertTrue(user.has_perm("plans.view_plan"))
        user.user_permissions.clear()
        self.assertFalse(user.has_perm("plans.view_plan"))
        self.group.permissions.add(perm)
        user.groups.add(self.group)
        self.assertTrue(user.has_perm("plans.view_plan"))
        user.groups.clear()
        self.assertFalse(user.has_perm("plans.view_plan"))

    def test_group_permissions_include_payments_and_preserve_other_modules(self):
        retained = Permission.objects.get(content_type__app_label="checkin", codename="view_checkin")
        self.group.permissions.add(retained)
        response = self.client.post(reverse("accounts_admin_group_edit", args=[self.group.pk]), {"name": "Socios", "perm_pagos_view": "on"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.group.permissions.filter(codename="view_monthlypayment").exists())
        self.assertTrue(self.group.permissions.filter(pk=retained.pk).exists())

    def test_invalid_group_selection_keeps_existing_groups(self):
        self.member.groups.add(self.group)
        response = self.client.post(reverse("accounts_admin_edit", args=[self.member.pk]), {"group_id": "bad"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.member.groups.filter(pk=self.group.pk).exists())

    def test_plan_can_be_edited_without_changing_name(self):
        form = PlanForm({"name": self.plan.name, "description": self.plan.description, "base_price": 250}, instance=self.plan)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(PlanForm({"name": self.plan.name, "description": "Otra descripción", "base_price": 250}).is_valid())

    def test_long_plan_description_and_price_precision(self):
        form = PlanForm({"name": "Nuevo plan", "description": "A" * 180, "base_price": 100})
        self.assertTrue(form.is_valid(), form.errors)
        for value in ["100.001", "100000000.00"]:
            self.assertFalse(PlanForm({"name": "Otro", "description": "Descripción diferente", "base_price": value}).is_valid())

    def test_course_validation_errors_are_preserved(self):
        response = self.client.post(reverse("create_class"), {"name": "x"})
        self.assertTrue(response.context["course_form"].errors)
        self.assertEqual(response.context["course_form"].data["name"], "x")

    def test_inscriptions_enforce_capacity_and_unique_members(self):
        self.client.force_login(self.member)
        url = reverse("inscription_question", args=[self.course.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(Inscription.objects.count(), 1)
        other = User.objects.create_user("other")
        self.client.force_login(other)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(Inscription.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Inscription.objects.create(course=self.course, participant=self.member)
        course = Course.objects.get(pk=self.course.pk)
        form = CourseForm({"name": course.name, "description": course.description, "starts_at": course.starts_at, "ends_at": course.ends_at, "max_capacity": 0}, instance=course)
        self.assertFalse(form.is_valid())

    def test_missing_objects_return_404(self):
        for name in ["edit_account", "deactivate_account", "accounts_admin_edit", "accounts_admin_group_edit", "edit_plan", "delete_plan", "edit_class", "delete_class", "inscription_question", "checkin_success", "detail_publication"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name, args=[999999])).status_code, 404)

    def test_invalid_statistics_filters_return_400(self):
        for name in ["estadisticas_dashboard", "estadisticas_data"]:
            for data in [{"anio": "bad"}, {"anio": "10000"}, {"mes": "13"}]:
                self.assertEqual(self.client.get(reverse(name), data).status_code, 400)
        for name in ["estadisticas_informe", "estadisticas_excel", "estadisticas_pdf"]:
            for data in [{"desde": "bad"}, {"hasta": "2026-02-30"}, {"desde": "2026-03-01", "hasta": "2026-01-01"}]:
                self.assertEqual(self.client.get(reverse(name), data).status_code, 400)

    def test_staff_false_filter_and_report_email(self):
        rows = EstadisticasService.informe_filtrado(staff="0")
        self.assertTrue(all(not r["is_staff"] for r in rows))
        self.assertEqual(next(r for r in rows if r["id"] == self.member.pk)["email"], "ana@example.com")

    def test_checkin_validates_dni_and_dates(self):
        initial = CheckIn.objects.count()
        for dni in ["bad", "123", "99999999999999999999"]:
            self.assertEqual(self.client.post(reverse("checkin_home"), {"dni": dni}).status_code, 200)
        self.assertEqual(CheckIn.objects.count(), initial)
        self.assertEqual(self.client.post(reverse("checkin_home"), {"dni": "12345678"}).status_code, 302)
        self.assertEqual(CheckIn.objects.latest("pk").person_id, self.person.pk)
        self.assertEqual(self.client.get(reverse("checkin_history"), {"desde": "bad"}).status_code, 200)

    def test_excel_user_input_is_text(self):
        rows = EstadisticasService.informe_filtrado()
        rows[0]["nombre"] = "=1+1"
        workbook = load_workbook(BytesIO(ReportesService.usuarios_a_excel(rows).getvalue()))
        self.assertEqual(workbook.active["C2"].data_type, "s")
