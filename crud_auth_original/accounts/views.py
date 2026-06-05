from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

# formularios de login y register
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# modelo del usuario por defecto de django
from django.contrib.auth.models import User, Permission
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
def deactivate_account(request, account_id):
    user = User.objects.get(id = account_id)
    if request.method == "GET":
        return render(request, "deactivate_account.html", {"user" : user})
    else:
        user.is_active = 0
        user.save()
        return redirect("list_accounts")


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



# Admin de accounts 

@login_required
def accounts_admin_home(request):
        if request.method == "GET":
            users = User.objects.all().exclude(id = request.user.id)
            return render(request, "accounts_admin_home.html",{"accounts" : users})



def accounts_admin_edit(request, account_id):
    # instaciamos el usuario que recibe el get
    
    # Configuración de modelos para gestionar permisos
    # app_label: nombre de la app de django que tiene el modelo de los permisos a gestionar
    # model_name: nombre del modelo sobre el cual queremos realizar la gestion
    # label: texto a mostrarse en el template
    MODELS =  {
        "planes" : {"app_label" : "plans", "model_name" : "plan", "label" : "Planes"},
        "courses" : {"app_label" : "classes", "model_name" : "course", "label" : "Clases"}
    }
    if request.method == "GET":
        target_user = User.objects.get(id = account_id)
        if not request.user.is_staff:
            return redirect("home")

        # guardamos los id de los permisos que tiene el usuario activo actualmente
        user_perms_ids = set(target_user.user_permissions.values_list("id", flat = True))
        
        modules_data = []
        # recorre los modulos y su contenido  
        for module_key, config in MODELS.items():
            perms = [] 
            # recorremos las 4 acciones que realizan como permiso dentro de un modelo
            for action in ["add","change","delete","view"]:
                # creamos el nombre de texto que tiene cada permiso action + _ + model name
                codename = f"{action}_{config['model_name']}"
                try:
                    # content type contiene los modelos dentro de cada app y se usa de puntero en auth_permission
                    content_type = ContentType.objects.get(
                        app_label = config["app_label"],
                        model = config["model_name"]
                    )
                    # traemos el objeto del permiso a que corresponde el content type y la accion del loop actual
                    perm = Permission.objects.get(
                        content_type = content_type,
                        codename = codename
                    )
                    granted = perm.id in user_perms_ids
                    # añadimos el perm y granted guarda un boolean si tiene o no el permiso activo
                    perms.append({
                    "action":    action,
                    "codename":  codename,
                    "checkbox":  f"perm_{module_key}_{action}",
                    "granted":   granted,
                })
                except (ContentType.DoesNotExist, Permission.DoesNotExist):
                    pass
                # añadimos los permisos, el nombre del modulo y el label al diccionario final
            modules_data.append(
                {
                    "key" : module_key,
                    "label": config["label"],
                    "perms": perms
                }
            )
        # retornamos todo en una vista
        return render(request, "accounts_admin_edit.html", {"user": target_user, "data": modules_data})
    
    if request.method == "POST":
        target_user = User.objects.get(id = account_id)
        if not request.user.is_staff:
            return redirect("home")
        
        # Recopilar todos los permisos que debería tener el usuario
        perms_to_assign = []
        
        for module_key, config in MODELS.items():
            for action in ["add","change","delete","view"]:
                codename = f"{action}_{config['model_name']}"
                checkbox_name = f"perm_{module_key}_{action}"
                
                try:
                    content_type = ContentType.objects.get(
                        app_label=config["app_label"],
                        model=config["model_name"],
                    )
                    perm = Permission.objects.get(
                        content_type=content_type,
                        codename=codename,
                    )
                except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
                    continue
                
                # Si el checkbox está marcado, añadir el permiso a la lista
                if checkbox_name in request.POST:
                    perms_to_assign.append(perm)
        
        # Asignar todos los permisos de una vez (reemplaza los anteriores)
        target_user.user_permissions.set(perms_to_assign)
        messages.success(request, "Permisos actualizados")
        return redirect("accounts_admin_home")