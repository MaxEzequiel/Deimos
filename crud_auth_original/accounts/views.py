from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

# formularios de login y register
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# modelo del usuario por defecto de django
from django.contrib.auth.models import User, Permission, Group 
from accounts.forms import UserEditForm

# datos del perfil persona
from people.models import Person
from people.forms import PersonForm
from memberships.models import Membership
from routines.models import Routine
# funciones para el inicio de sesion
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count

# vista de inicio con estado de membresia si es que existe 
@login_required
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

@login_required
@transaction.atomic
def create_account(request):
    if request.method == "GET":
        return render(request, "signup.html", {"user_form": UserCreationForm(), "person_form": PersonForm()})
    else:
        user_form = UserCreationForm(request.POST)
        person_form = PersonForm(request.POST)
        
        if user_form.is_valid() and person_form.is_valid():
            try:
                # creamos el objeto del formulario recibido sin guardar para añadir campos adicionales
                user = user_form.save(commit=False)
                
                # Verificar si se marcó la opción "es administrador"
                # Los privilegios se administran sólo desde el módulo protegido de grupos.
                is_admin = False
                if is_admin:
                    user.is_superuser = True
                    user.is_staff = True  # También necesita is_staff para acceder al admin
                
                user.save()
                
                person = person_form.save(commit=False)
                person.user = user
                person.save()
                
                Routine.objects.create(client=person, name=f"Rutina de {person.name}", description="Rutina personalizada")
                Membership.objects.create(user=user)
                login(request, user)
                messages.success(request, "Usuario registrado correctamente.")
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
        if user is None or user.is_active == 0:
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
def deactivate_account(request, account_id):
    user = get_object_or_404(User, id=account_id)
    if request.method == "GET":
        return render(request, "deactivate_account.html", {"user" : user})
    else:
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, "La cuenta fue desactivada.")
        return redirect("list_accounts")


# vistas de gestion de usuarios 
@login_required
def list_accounts(request):
    if request.method == "GET":
        users = User.objects.all().exclude(id = request.user.id)
        return render(request, "list_accounts.html",{"accounts" : users})

@login_required
@transaction.atomic
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



# Admin de accounts 

@login_required
def accounts_admin_home(request):
        if request.method == "GET":
            users = User.objects.all().exclude(id = request.user.id)
            return render(request, "accounts_admin_home.html",{"accounts" : users})


@login_required
@transaction.atomic
def accounts_admin_edit(request, account_id):
    if request.method == "GET":
        groups = Group.objects.all()
        user = User.objects.get(id = account_id)
        return render(request, "accounts_admin_edit.html", {"user" : user, "groups" : groups})
    
    if request.method == "POST":
        group_id = request.POST.get("group_id")
        user = User.objects.get(id = account_id)
        user.groups.clear()
        # Obtener el objeto Group usando el ID y asignarlo al usuario
        if group_id:
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
        return redirect("accounts_admin_home")


@login_required
def reports_home(request):
    """Panel con tres gráficos generados desde las tablas reales del sistema."""
    from classes.models import Course
    from plans.models import Plan

    membership_data = list(Membership.objects.values("status").annotate(total=Count("id")).order_by("status"))
    plan_data = list(Plan.objects.annotate(total=Count("person")).values("name", "total").order_by("name"))
    class_data = list(Course.objects.values("teacher__name", "teacher__surname").annotate(total=Count("id")).order_by("teacher__surname"))
    return render(request, "reports/report_home.html", {
        "membership_labels": [row["status"] or "Sin estado" for row in membership_data],
        "membership_values": [row["total"] for row in membership_data],
        "plan_labels": [row["name"] or "Sin plan" for row in plan_data],
        "plan_values": [row["total"] for row in plan_data],
        "class_labels": [f'{row["teacher__name"]} {row["teacher__surname"]}' for row in class_data],
        "class_values": [row["total"] for row in class_data],
    })
