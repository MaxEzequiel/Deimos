from django.shortcuts import render, redirect, get_object_or_404

# formularios de login y register
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# modelo del usuario por defecto de django
from django.contrib.auth.models import User

# datos del perfil persona
from people.models import Person
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
            status = "No membership found. Please create a membership."
        return render(request, "home.html", {"estado": status})
    else:
        return render(request, "home.html", {"estado": "The user is not logged in. Log in to view your membership status"})


def signup(request):
    if request.method == "GET":
        return render(request, "signup.html", {"form": UserCreationForm})
    else:
        if request.POST["password1"] == request.POST["password2"]:

            try:
                user = User.objects.create_user(
                    username=request.POST["username"],
                    password=request.POST["password1"],
                    is_staff=request.POST.get("is_staff") == "1",
                )
                user.save()

                person = Person.objects.create(
                    user=user,
                    plan=None,
                    id_number=request.POST.get("dni", ""),
                    name=request.POST.get("name", ""),
                    surname=request.POST.get("surname", ""),
                    birth_date=request.POST.get("birth_date") or None,
                    gender=request.POST.get("gender", ""),
                    phone_number=request.POST.get("phone_number", ""),
                    email=request.POST.get("email", ""),
                )
                Routine.objects.create(
                    client=person,
                    name="Mi rutina",
                    description="",
                )

                Membership.objects.create(user=user)
                login(request, user)
                return redirect("home")
            except Exception as excep:
                logout(request)
                print(excep)
                return render(
                    request,
                    "signup.html",
                    {"form": UserCreationForm, "error": "usuario ya existe"},
                )

        else:
            logout(request)
            return render(
                request,
                "signup.html",
                {"form": UserCreationForm, "error": "las contraseñas no coinciden"},
            )


def signout(request):
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
                    "error": "username or password isnt correct",
                },
            )
        else:
            login(request, user)
            return redirect("home")


@login_required
def delete_account(request):
    if request.method == "GET":
        username = request.user.username
        return render(request, "delete_user.html", {"username": username})
    else:
        if request.POST.get("password"):
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
