from django.shortcuts import render, redirect
from .models import Course, Inscription
from .forms import CourseForm
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from core.audit import audit
from django.db import transaction
# Create your views here. 


#  class es lo que vera el user, en codigo se manejara como course
@login_required
@permission_required(["classes.view_course","classes.add_course"],login_url="/error_403")
def create_class(request):
    if request.method == "GET":
        return render(request, "create_class.html",{"course_form" : CourseForm()})
    else:
        current_class = CourseForm(request.POST)
        if current_class.is_valid():
            with transaction.atomic():
                course_instance = current_class.save(commit=False)
                course_instance.teacher = request.user
                course_instance.save()
                audit(request, "CREATE", "clase: " + str(course_instance.id) + " - " + course_instance.name)
            return redirect("list_class")
        else:
            return render(request, "create_class.html", {"course_form" : CourseForm})

@login_required
@permission_required(["classes.view_course"],login_url="/error_403")
def list_class(request):
    if request.method == "GET": 
        courses = Course.objects.all()
        for course in courses:
            inscriptions = Inscription.objects.filter(course = course)
            free_spots = course.max_capacity - inscriptions.count()
            course.free_spots = free_spots
            if free_spots > 0:
                course.has_spots = True
            else:
                course.has_spots = False
        return render(request, "list_class.html",{"courses": courses})

@login_required
@permission_required(["classes.view_course", "classes.change_course"],login_url="/error_403")
def edit_class(request, course_id): 
    course = Course.objects.get(id = course_id)
    if request.method == "GET":
        form = CourseForm(instance=course)
        return render(request, "edit_class.html", {"edit_form" : form})
    else:
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                audit(request, "UPDATE", "clase: " + str(course.id) + " - " + course.name)
            return redirect("list_class")
        return render(request, "edit_class.html", {"edit_form" : form})

@login_required
@permission_required(["classes.view_course","classes.delete_course"],login_url="/error_403")
def delete_class(request, course_id):
    if request.method == "GET":
        return render(request,"delete_class.html")
    else:
        course = Course.objects.get(id = course_id)
        with transaction.atomic():
            audit(request, "DELETE", "clase: " + str(course.id) + " - " + course.name)
            course.delete()
        return redirect("list_class")

@login_required
def inscription_question(request, course_id):
    course = Course.objects.get(id = course_id)
    if request.method == "GET":
        return render(request, "inscription_question.html", {"course" : course})
    else:
        if course.teacher == request.user:
            return render(request, "inscription_question.html", {"course" : course, "error" : "El profesor de la clase no puede inscribirse a su propia clase"})
        already_inscribed = Inscription.objects.filter(course = course, participant = request.user)
        if already_inscribed.count() > 0:
            return render(request, "inscription_question.html", {"course" : course, "error" : "Ya estas inscripto en esta clase"})
        inscriptions = Inscription.objects.filter(course = course)
        if inscriptions.count() >= course.max_capacity:
            return render(request, "inscription_question.html", {"course" : course, "error" : "Todos los cupos ya estan ocupados"})
        inscription = Inscription()
        inscription.course = course
        inscription.participant = request.user
        with transaction.atomic():
            inscription.save()
            audit(request, "INSCRIBE", "clase: " + str(course.id) + " - " + course.name)
        try:
            student = request.user.person
            if student.email:
                subject = "Inscripcion a la clase " + course.name
                message = ("Te inscribiste a la clase: " + course.name + "\n" +
                           "Descripcion: " + course.description + "\n" +
                           "Inicio: " + course.starts_at.strftime("%d/%m/%Y %H:%M") + "\n" +
                           "Fin: " + course.ends_at.strftime("%d/%m/%Y %H:%M") + "\n" +
                           "Profesor: " + course.teacher.username)
                send_mail(subject, message, None, [student.email])
        except Exception:
            pass
        return redirect("list_class")

