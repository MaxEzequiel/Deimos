import logging
from smtplib import SMTPException
from django.contrib import messages
from django.utils import timezone

logger = logging.getLogger(__name__)
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Inscription
from .forms import CourseForm
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from core.audit import audit
from django.db import transaction

# Create your views here.


#  class es lo que vera el user, en codigo se manejara como course
@login_required
@permission_required(
	["classes.view_course", "classes.add_course"], login_url="/error_403"
)
@require_http_methods(["GET", "POST"])
def create_class(request):
	if request.method == "GET":
		return render(
			request, "create_class.html", {"course_form": CourseForm()}
		)
	else:
		current_class = CourseForm(request.POST)
		if current_class.is_valid():
			with transaction.atomic():
				course_instance = current_class.save(commit=False)
				course_instance.teacher = request.user
				course_instance.save()
				audit(
					request,
					"CREATE",
					"clase: "
					+ str(course_instance.id)
					+ " - "
					+ course_instance.name,
				)
			return redirect("list_class")
		else:
			return render(
				request, "create_class.html", {"course_form": current_class}
			)


@login_required
@permission_required(["classes.view_course"], login_url="/error_403")
@require_http_methods(["GET"])
def list_class(request):
	if request.method == "GET":
		courses = Course.objects.all()
		for course in courses:
			inscriptions = Inscription.objects.filter(course=course)
			free_spots = course.max_capacity - inscriptions.count()
			course.free_spots = free_spots
			if free_spots > 0:
				course.has_spots = True
			else:
				course.has_spots = False
		return render(request, "list_class.html", {"courses": courses})


@login_required
@permission_required(
	["classes.view_course", "classes.change_course"], login_url="/error_403"
)
@require_http_methods(["GET", "POST"])
def edit_class(request, course_id):
	course = get_object_or_404(Course, pk=course_id)
	if request.method == "GET":
		form = CourseForm(instance=course)
		return render(request, "edit_class.html", {"edit_form": form})
	else:
		form = CourseForm(request.POST, instance=course)
		if form.is_valid():
			with transaction.atomic():
				form.save()
				audit(
					request,
					"UPDATE",
					"clase: " + str(course.id) + " - " + course.name,
				)
			return redirect("list_class")
		return render(request, "edit_class.html", {"edit_form": form})


@login_required
@permission_required(
	["classes.view_course", "classes.delete_course"], login_url="/error_403"
)
@require_http_methods(["GET", "POST"])
def delete_class(request, course_id):
	course = get_object_or_404(Course, pk=course_id)
	if request.method == "GET":
		return render(request, "delete_class.html")
	else:
		with transaction.atomic():
			audit(
				request,
				"DELETE",
				"clase: " + str(course.id) + " - " + course.name,
			)
			course.delete()
		return redirect("list_class")


@login_required
@require_http_methods(["GET", "POST"])
def inscription_question(request, course_id):
	course = get_object_or_404(Course, pk=course_id)
	if request.method == "GET":
		return render(request, "inscription_question.html", {"course": course})
	with transaction.atomic():
		course = get_object_or_404(
			Course.objects.select_for_update(), pk=course_id
		)
		error = None
		if course.teacher_id == request.user.pk:
			error = (
				"El profesor de la clase no puede inscribirse a su propia clase"
			)
		elif Inscription.objects.filter(
			course=course, participant=request.user
		).exists():
			error = "Ya estás inscripto en esta clase"
		elif (
			Inscription.objects.filter(course=course).count()
			>= course.max_capacity
		):
			error = "Todos los cupos ya están ocupados"
		if error:
			return render(
				request,
				"inscription_question.html",
				{"course": course, "error": error},
			)
		Inscription.objects.create(course=course, participant=request.user)
		audit(request, "INSCRIBE", f"clase: {course.id} - {course.name}")
	if request.user.email:
		message = (
			f"Te inscribiste a la clase: {course.name}\n"
			f"Descripción: {course.description}\n"
			f"Inicio: {timezone.localtime(course.starts_at):%d/%m/%Y %H:%M}\n"
			f"Fin: {timezone.localtime(course.ends_at):%d/%m/%Y %H:%M}\n"
			f"Profesor: {course.teacher.username}"
		)
		try:
			send_mail(
				f"Inscripción a la clase {course.name}",
				message,
				None,
				[request.user.email],
			)
		except (OSError, SMTPException):
			logger.exception("No se pudo enviar la confirmación de inscripción")
			messages.warning(
				request,
				(
					"La inscripción se guardó, pero no se pudo enviar el correo de "
					"confirmación"
				),
			)
	return redirect("list_class")
