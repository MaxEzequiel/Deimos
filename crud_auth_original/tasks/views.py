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

from tasks.forms import MembresiaForm, PlanForm


# Create your views here.
# //// Modulo Login ////

# mostrar todos los perfiles modelo de user 
def perfiles(request):
    if request.method == "GET":
        perfiles = Persona.objects.select_related("usuario").all()
        return render(request, "perfiles.html", {"perfiles": perfiles})

def singup(request):
    if request.method == "GET":
        return render(request, "singup.html", {"form": UserCreationForm})
    else:
        if request.POST["password1"] == request.POST["password2"]:

            try:
                # register user usamos create_user para que cifre automaticamente la contraseña
                # tambien valida que el nombre de usuario sea unico
                user = User.objects.create_user(
                    username=request.POST["username"],
                    password=request.POST["password1"],
                    is_staff = request.POST.get("is_staff") == "1"
                )
                user.save()

                rutina = Rutina.objects.create()
                # crear Profile con los campos enviados en singup.html (sin validaciones extra)
                Persona.objects.create(
                    usuario=user,
                    dni=request.POST.get("dni", ""),
                    nombre=request.POST.get("name", ""),
                    apellido=request.POST.get("surname", ""),
                    fecha_nacimiento=request.POST.get("birth_date") or None,
                    genero=request.POST.get("gender", ""),
                    telefono=request.POST.get("phone_number", ""),
                    email=request.POST.get("email", ""),
                    rutina=rutina,
                )

                Membresia.objects.create(id_cliente=user)
                # crea la cookie del token del inicio de sesion
                login(request, user)
                return redirect("home")
            except Exception as excep:
                logout(request)
                print(excep)
                return render(
                    request,
                    "singup.html",
                    {"form": UserCreationForm, "error": "usuario ya existe"},
                )

        else:
            logout(request)
            return render(
                request,
                "singup.html",
                {"form": UserCreationForm, "error": "las contraseñas no coinciden"},
            )
            
            
# vista de inicio con estado de membresia si es que existe 
def home(request):
    if request.user.is_authenticated:
        membresia = Membresia.objects.get(id_cliente=request.user)
        estado = membresia.estado
        return render(request, "home.html", {"estado" : estado})
    else:
        return render(request,"home.html", {"estado" : "The user is not logged in. Log in to view your membership status"} )



def singout(request):
    logout(request)
    return redirect("home")


# login 
def log_in(request):
    if request.method == "GET":
        return render(request, "login.html", {"login_form": AuthenticationForm})
    else:
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if user == None:
            # si las credenciales son incorrectas elimina la cookie de session id
            logout(request)
            return render(
                request,
                "login.html",
                {
                    "login_form": AuthenticationForm,
                    "error": "username or password isnt correct",
                },
            )
        else:
            login(request, user)
            return redirect("home")

@login_required
def delete_user(request):
    if request.method == "GET":
        username = request.user.username
        return render(request, "delete_user.html", {"username": username})
    else:
        if request.POST["password"]:
            password = request.POST["password"]
            if request.user.check_password(password):
                user = request.user
                logout(request)
                user.delete()
                return redirect("home")
            else:
                return render(
                    request,
                    "delete_user.html",
                    {"error": "la contraseña no es correcta"},
                )
        else:
            return render(
                request,
                "delete_user.html",
                {"error": "la contraseña no puede estar vacia"},
            )


# //// fin del modulo login

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
    