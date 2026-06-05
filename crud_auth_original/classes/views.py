from django.shortcuts import render, redirect
from .models import Course
from people.models import Person
from .forms import CourseForm
from django.contrib.auth.decorators import login_required, permission_required
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
            course_instance = current_class.save(commit=False)
            course_instance.teacher = Person.objects.get(user = request.user)
            course_instance.save()
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
@permission_required(["classes.view_course", "classes.change_course"],login_url="/error_403")
def edit_class(request, course_id): 
    course = Course.objects.get(id = course_id)
    if request.method == "GET":
        form = CourseForm(instance=course)
        return render(request, "edit_class.html", {"edit_form" : form})
    else:
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect("list_class")
        return render(request, "edit_class.html", {"edit_form" : form})

@login_required
@permission_required(["classes.view_course","classes.delete_course"],login_url="/error_403")
def delete_class(request, course_id):
    if request.method == "GET":
        return render(request,"delete_class.html")
    else:
        course = Course.objects.get(id = course_id)
        course.delete()
        return redirect("list_class")
