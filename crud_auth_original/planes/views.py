from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db import transaction, IntegrityError
# formularios de login y register
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
# modelo del usuario por defecto de django
from django.contrib.auth.models import User
# datos del perfil persona
from .models import Persona,RutinaEjercicioDia,Rutina,Ejercicio,Dia,Membresia,Plan

# modulo de pdf
from django_xhtml2pdf.utils import pdf_decorator

# funciones para el inicio de sesion
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.decorators import login_required

from tasks.forms import PlanForm

@login_required
def crear_plan(request):
    if request.method == "POST":
        Plan.objects.create(
            nombre = request.POST.get("nombre", ""),
            descripcion = request.POST.get("descripcion", ""),
            precio_base = float(request.POST.get("precio","")),
            )
        return redirect("home")
    else: 
        return render(request, "crear_plan.html")


def listar_planes(request):
    if request.method == "GET":
        planes = Plan.objects.all()
        return render(request , "listar_planes.html", {"planes" : planes})

@pdf_decorator
def pdf_planes(request):
    if request.method == "GET":
        planes = Plan.objects.all()
        return render(request , "pdf_planes.html", {"planes" : planes})


def editar_plan(request, id_plan):
    plan = Plan.objects.get(id = id_plan)
    if request.method == "GET": 
        form = PlanForm(instance=plan)
        return render(request, "editar_plan.html", {"form" : form})
    
    else:
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return redirect("listar_planes")
        else:
            error = "formulario no valido, revisa los campos nuevamente"
            return render(request, "editar_plan.html", {"form" : form, "error" : error})

def eliminar_plan(request, id_plan):
    plan = Plan.objects.get(id = id_plan)
    if request.method == "GET":
        return render(request, "eliminar_plan.html")
    # POST
    else:
        plan.delete()
        return redirect("listar_planes")
