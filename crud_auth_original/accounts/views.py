from django.contrib import messages
import logging

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import (
	require_GET,
	require_http_methods,
	require_POST,
)

from accounts.forms import UserEditForm
from accounts.signals import clear_permission_cache
from core.audit import audit
from core.decorators import superuser_required
from memberships.models import Membership
from people.forms import PersonForm
from people.models import Person
from routines.models import Routine

logger = logging.getLogger(__name__)


def _create_account_with_rollback(request, user_form, person_form):
	"""Create all user records as one unit and explicitly roll back on failure."""
	with transaction.atomic():
		savepoint_id = transaction.savepoint()
		try:
			user = user_form.save(commit=False)
			user.email = person_form.cleaned_data.get("email") or ""
			user.is_superuser = request.POST.get("is_admin") == "on"
			user.is_staff = user.is_superuser
			user.save()
			person = person_form.save(commit=False)
			person.user = user
			person.save()
			Routine.objects.create(
				client=person,
				name=f"Rutina de {person.name}",
				description="Rutina personalizada",
			)
			Membership.objects.create(user=user)
			audit(request, "CREATE", f"usuario: {user.id} - {user.username}")
		except Exception:
			transaction.savepoint_rollback(savepoint_id)
			raise
		transaction.savepoint_commit(savepoint_id)
		return user


@login_required
@require_GET
def home(request):
	from classes.models import Course
	from checkin.services import member_checkin_status
	from django.db.models import Count
	from django.utils import timezone
	from payments.models import MonthlyPayment

	today = timezone.localdate()
	membership = (
		Membership.objects.select_related("plan")
		.filter(user=request.user)
		.first()
	)
	status = (
		membership.effective_status
		if membership
		else "No se encontró la membresía, por favor adquiera una"
	)
	person = (
		Person.objects.select_related("user").filter(user=request.user).first()
	)
	monthly_status = member_checkin_status(person)
	courses = []
	if request.user.is_superuser or request.user.has_perm(
		"classes.view_course"
	):
		courses = list(
			Course.objects.filter(starts_at__gte=timezone.now())
			.annotate(inscriptions_count=Count("inscription"))
			.order_by("starts_at")[:4]
		)
		for course in courses:
			course.free_spots = max(
				0, course.max_capacity - course.inscriptions_count
			)
			course.has_spots = course.free_spots > 0
	admin_stats = None
	if request.user.is_superuser:
		admin_stats = {
			"active_accounts": User.objects.filter(is_active=True).count(),
			"members": Person.objects.count(),
			"pending_payments": MonthlyPayment.objects.filter(
				paid_on__isnull=True, due_date__gte=today
			).count(),
			"overdue_payments": MonthlyPayment.objects.filter(
				paid_on__isnull=True, due_date__lt=today
			).count(),
		}
	return render(
		request,
		"home.html",
		{
			"estado": status,
			"membership": membership,
			"membership_status": status,
			"is_admin_home": request.user.is_superuser,
			"admin_stats": admin_stats,
			"monthly_status": monthly_status,
			"total_rutinas": Routine.objects.filter(
				client__user=request.user
			).count(),
			"proximas_clases": courses,
		},
	)


@login_required
@superuser_required
@require_http_methods(["GET", "POST"])
def create_account(request):
	data = request.POST if request.method == "POST" else None
	user_form = UserCreationForm(data)
	person_form = PersonForm(data)
	if request.method == "POST":
		user_valid = user_form.is_valid()
		person_valid = person_form.is_valid()
		if user_valid and person_valid:
			try:
				_create_account_with_rollback(request, user_form, person_form)
			except Exception:
				logger.exception(
					"No se pudo crear la cuenta; se ejecuto rollback"
				)
				messages.error(
					request,
					(
						"No se pudo crear el usuario. Se deshicieron los cambios de la "
						"transaccion."
					),
				)
			else:
				messages.success(request, "Usuario creado correctamente")
				return redirect("list_accounts")
	return render(
		request,
		"signup.html",
		{"user_form": user_form, "person_form": person_form},
	)


@require_POST
def singout(request):
	logout(request)
	return redirect("login")


@require_http_methods(["GET", "POST"])
def login_view(request):
	form = AuthenticationForm(
		request, data=request.POST if request.method == "POST" else None
	)
	if request.method == "POST" and form.is_valid():
		login(request, form.get_user())
		destination = request.POST.get("next") or request.GET.get("next")
		if destination and url_has_allowed_host_and_scheme(
			destination, {request.get_host()}, require_https=request.is_secure()
		):
			return redirect(destination)
		return redirect("home")
	return render(
		request,
		"login.html",
		{
			"login_form": form,
			"error": form.non_field_errors(),
			"next": request.GET.get("next", ""),
		},
	)


@login_required
@superuser_required
@require_http_methods(["GET", "POST"])
def deactivate_account(request, account_id):
	user = get_object_or_404(User, pk=account_id)
	if request.method == "POST":
		if user.pk == request.user.pk:
			messages.error(
				request,
				"No podés desactivar tu propia cuenta desde esta pantalla",
			)
		else:
			with transaction.atomic():
				user.is_active = False
				user.save(update_fields=["is_active"])
				audit(
					request,
					"DEACTIVATE",
					f"usuario: {user.id} - {user.username}",
				)
		return redirect("list_accounts")
	return render(request, "deactivate_account.html", {"user": user})


@login_required
@superuser_required
@require_GET
def list_accounts(request):
	users = User.objects.select_related("person").exclude(pk=request.user.pk)
	return render(request, "list_accounts.html", {"accounts": users})


@login_required
@superuser_required
@require_http_methods(["GET", "POST"])
def edit_account(request, account_id):
	user = get_object_or_404(User, pk=account_id)
	person = Person.objects.filter(user=user).first()
	data = request.POST if request.method == "POST" else None
	user_form = UserEditForm(data, instance=user)
	person_form = PersonForm(data, instance=person)
	if request.method == "POST":
		user_valid = user_form.is_valid()
		person_valid = person_form.is_valid()
		if user_valid and person_valid:
			with transaction.atomic():
				user_form.save()
				person = person_form.save(commit=False)
				person.user = user
				person.save()
				audit(
					request, "UPDATE", f"usuario: {user.id} - {user.username}"
				)
			return redirect("list_accounts")
	return render(
		request,
		"edit_account.html",
		{
			"user_form": user_form,
			"person_form": person_form,
			"account_id": account_id,
		},
	)


@login_required
@superuser_required
@require_GET
def accounts_admin_home(request):
	users = User.objects.select_related("person").exclude(pk=request.user.pk)
	return render(request, "accounts_admin_home.html", {"accounts": users})


@login_required
@superuser_required
@require_http_methods(["GET", "POST"])
def accounts_admin_edit(request, account_id):
	user = get_object_or_404(User, pk=account_id)
	if request.method == "POST":
		group_id = request.POST.get("group_id")
		if group_id and not group_id.isdecimal():
			messages.error(request, "El grupo seleccionado no es válido")
			return redirect("accounts_admin_edit", account_id=account_id)
		group = get_object_or_404(Group, pk=group_id) if group_id else None
		with transaction.atomic():
			user.groups.set([group] if group else [])
			if user.pk == request.user.pk:
				clear_permission_cache(request.user)
			audit(
				request,
				"UPDATE",
				f"grupos de usuario: {user.id} - {user.username}",
			)
		return redirect("accounts_admin_home")
	return render(
		request,
		"accounts_admin_edit.html",
		{
			"user": user,
			"groups": Group.objects.all(),
			"selected_group_ids": set(user.groups.values_list("pk", flat=True)),
		},
	)
