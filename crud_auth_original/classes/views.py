from django.shortcuts import render, redirect
from .models import Course, Inscription
from people.models import Person
from .forms import CourseForm, InscriptionForm
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib import messages
from django.db import transaction
# Create your views here. 


#  class es lo que vera el user, en codigo se manejara como course
@login_required
@user_passes_test(lambda user: user.is_staff, login_url="/error_403/")
@permission_required(["classes.view_course","classes.add_course"],login_url="/error_403")
def create_class(request):
    if request.method == "GET":
        return render(request, "create_class.html",{"course_form" : CourseForm()})
    else:
        current_class = CourseForm(request.POST)
        if current_class.is_valid():
            course_instance = current_class.save(commit=False)
            course_instance.teacher = Person.objects.get(user = request.user)
            with transaction.atomic():
                course_instance.save()
            messages.success(request, "Clase creada correctamente.")
            return redirect("list_class")
        else:
            return render(request, "create_class.html", {"course_form" : CourseForm})

@login_required
@permission_required(["classes.view_course"],login_url="/error_403")
def list_class(request):
    if request.method == "GET": 
        courses = Course.objects.all()
        return render(request, "list_class.html",{"courses": courses})

@login_required
@user_passes_test(lambda user: user.is_staff, login_url="/error_403/")
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
            messages.success(request, "Clase actualizada correctamente.")
            return redirect("list_class")
        return render(request, "edit_class.html", {"edit_form" : form})

@login_required
@user_passes_test(lambda user: user.is_staff, login_url="/error_403/")
@permission_required(["classes.view_course","classes.delete_course"],login_url="/error_403")
def delete_class(request, course_id):
    if request.method == "GET":
        return render(request,"delete_class.html")
    else:
        course = Course.objects.get(id = course_id)
        with transaction.atomic():
            course.delete()
        messages.success(request, "Clase eliminada correctamente.")
        return redirect("list_class")


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="/error_403/")
@permission_required(["classes.view_course", "classes.change_course"], login_url="/error_403")
@transaction.atomic
def manage_inscriptions(request, course_id):
    course = Course.objects.get(id=course_id)
    form = InscriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        inscription, created = Inscription.objects.get_or_create(course=course, participant=form.cleaned_data["participant"])
        messages.success(request, "Usuario inscripto correctamente." if created else "El usuario ya estaba inscripto en esta clase.")
        return redirect("manage_inscriptions", course_id=course.id)
    inscriptions = Inscription.objects.filter(course=course).select_related("participant", "participant__user")
    return render(request, "manage_inscriptions.html", {"course": course, "form": form, "inscriptions": inscriptions})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url="/error_403/")
@permission_required(["classes.view_course", "classes.change_course"], login_url="/error_403")
@transaction.atomic
def delete_inscription(request, inscription_id):
    inscription = Inscription.objects.get(id=inscription_id)
    course_id = inscription.course_id
    if request.method == "POST":
        inscription.delete()
        messages.success(request, "Inscripción eliminada.")
    return redirect("manage_inscriptions", course_id=course_id)

