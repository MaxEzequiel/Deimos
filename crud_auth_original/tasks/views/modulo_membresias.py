from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db import transaction, IntegrityError
# formularios de login y register
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
# modelo del usuario por defecto de django
from django.contrib.auth.models import User
# datos del perfil persona
from ..models import Persona,RutinaEjercicioDia,Rutina,Ejercicio,Dia,Membresia,Plan

# modulo de pdf
from django_xhtml2pdf.utils import pdf_decorator

# funciones para el inicio de sesion
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.decorators import login_required

from tasks.forms import MembresiaForm, PlanForm

# //// modulo membresia //// 



@login_required
def editar_membresia(request):
    # obtener o crear la membresía del usuario
    membresia= Membresia.objects.get_or_create(id_cliente=request.user)

    if request.method == "GET":
        username = request.user.username
        form = MembresiaForm(instance=membresia)
        return render(request, "editar_membresia.html", {"form": form,"username":username})
    # POST 
    else:
        form = MembresiaForm(request.POST, instance=membresia)
        if form.is_valid():
            form.save()
            messages.success(request, "Membresía actualizada")
            return redirect("home")
        return render(request, "editar_membresia.html", {"form": form})
