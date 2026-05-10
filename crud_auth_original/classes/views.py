from django.shortcuts import render, redirect
from .models import Course
from people.models import Person
from .forms import CourseForm
from django.contrib.auth.decorators import login_required
# Create your views here. 
# Mineaqua

@login_required
def create_class(request):
    if request.method == "GET":
        return render(request, "create_class.html",{"class_form" : CourseForm()})
    else:
        current_class = CourseForm(request.POST)
        if current_class.is_valid():
            course_instance = current_class.save(commit=False)
            course_instance.teacher = Person.objects.get(user = request.user)
            course_instance.save()
            return redirect("home")
        else:
            return render(request, "create_class.html", {"class_form" : CourseForm})

