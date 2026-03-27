from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db import transaction, IntegrityError
# formularios de login y register
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
# modelo del usuario por defecto de django
from django.contrib.auth.models import User
# datos del perfil persona
from accounts.models import Person, RoutineExerciseDay, Routine, Exercise, Day
from memberships.models import Membership
from plans.models import Plan

# modulo de pdf
from django_xhtml2pdf.utils import pdf_decorator

# funciones para el inicio de sesion
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.decorators import login_required

from plans.forms import PlanForm

@login_required
def create_plan(request):
    if request.method == "POST":
        Plan.objects.create(
            name=request.POST.get("nombre", ""),
            description=request.POST.get("descripcion", ""),
            base_price=float(request.POST.get("precio", 0) or 0),
        )
        return redirect("home")
    else:
        return render(request, "create_plan.html")


def list_plans(request):
    if request.method == "GET":
        plans = Plan.objects.all()
        return render(request, "list_plans.html", {"plans": plans})

@pdf_decorator
def plans_pdf(request):
    if request.method == "GET":
        plans = Plan.objects.all()
        return render(request, "plans_pdf.html", {"plans": plans})


def edit_plan(request, plan_id):
    plan = Plan.objects.get(id=plan_id)
    if request.method == "GET":
        form = PlanForm(instance=plan)
        return render(request, "edit_plan.html", {"form": form})
    else:
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return redirect("list_plans")
        else:
            error = "form is invalid, please verify the fields"
            return render(request, "edit_plan.html", {"form": form, "error": error})

def delete_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if request.method == "GET":
        return render(request, "delete_plan.html")
    else:
        plan.delete()
        return redirect("list_plans")
