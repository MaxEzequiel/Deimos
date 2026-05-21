from django.shortcuts import render, redirect, get_object_or_404

# formularios de login y register
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# modelo del usuario por defecto de django
from django.contrib.auth.models import User
from accounts.forms import UserEditForm

# datos del perfil persona
from people.models import Person
from people.forms import PersonForm
from memberships.models import Membership
from routines.models import Routine
# funciones para el inicio de sesion
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.decorators import login_required

# vista de inicio con estado de membresia si es que existe 
def home(request):
    if request.user.is_authenticated:
        try:
            membership = Membership.objects.get(user=request.user)
            status = membership.status
        except Membership.DoesNotExist:
            # si no existe la membresia, se puede crear o mostrar estado claro
            status = "No se encontro la membresia, porfavor adquiera una"
        return render(request, "home.html", {"estado": status})
    else:
        return render(request, "home.html", {"estado": "Inicia sesion para ver el estado de tu membresia"})


def create_account(request):
    if request.method == "GET":
        return render(request, "signup.html", {"user_form": UserCreationForm(), "person_form": PersonForm()})
    else:
        user_form = UserCreationForm(request.POST)
        person_form = PersonForm(request.POST)
        if user_form.is_valid() and person_form.is_valid():
            try:
                # creamos el objeto del formulario recibido sin guardar para añadir el campo de is_staff
                # al formulario final
                user = user_form.save(commit=False)
                user.is_staff = request.POST.get("is_staff", False)
                user.save()
                
                person = person_form.save(commit=False)
                person.user = user
                person.save()
                
                Routine.objects.create(client=person, name=f"Rutina de {person.name}", description="Rutina personalizada")
                Membership.objects.create(user=user)
                login(request, user)
                return redirect("home")
            except Exception as e:
                logout(request)
                print(e)
                return render(request, "signup.html", {"user_form": UserCreationForm(), "person_form": PersonForm(), "e": "usuario ya existe"})
        return render(request, "signup.html", {
        "user_form": user_form,
        "person_form": person_form,
    })
                            
def singout(request):
    logout(request)
    return redirect("home")


# login
def login_view(request):
    if request.method == "GET":
        return render(request, "login.html", {"login_form": AuthenticationForm})
    else:
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if user is None:
            logout(request)
            return render(
                request,
                "login.html",
                {
                    "login_form": AuthenticationForm,
                    "error": "el usuario o contraseña no son correctos",
                },
            )
        else:
            login(request, user)
            return redirect("home")


@login_required
def deactivate_account(request):
    if request.method == "GET":
        username = request.user.username
        return render(request, "delete_user.html", {"username": username})
    else:
        if request.POST.get("password"):
            password = request.POST["password"]
            if request.user.check_password(password):
                user = request.user
                logout(request)
                user.is_active = 0
                user.save()
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


# vistas de gestion de usuarios 

def list_accounts(request):
    if request.method == "GET":
        users = User.objects.all().exclude(id = request.user.id)
        return render(request, "list_accounts.html",{"accounts" : users})


def edit_account(request, account_id):
    user = get_object_or_404(User, id=account_id)
    person = get_object_or_404(Person, user=user)
    
    if request.method == "GET":
        user_form = UserEditForm(instance=user)
        person_form = PersonForm(instance=person)
        return render(request, "edit_account.html", {
            "user_form": user_form,
            "person_form": person_form,
            "account_id": account_id,
        })
    else:
        user_form = UserEditForm(request.POST, instance=user)
        person_form = PersonForm(request.POST, instance=person)
        
        if user_form.is_valid() and person_form.is_valid():
            user_form.save()
            person_form.save()
            return redirect("list_accounts")
        
        return render(request, "edit_account.html", {
            "user_form": user_form,
            "person_form": person_form,
            "account_id": account_id,
        })

