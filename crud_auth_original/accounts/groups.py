from django.shortcuts import render, redirect
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

# modelo del usuario por defecto de django
from django.contrib.auth.models import Permission

# form de grupos
from accounts.forms import GroupForm
# funciones para el inicio de sesion
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required

def accounts_admin_group_list(request):
    if request.method == "GET":
        groups = Group.objects.all()
        return render(request, "group_templates/list_groups.html", {"groups" : groups})


def accounts_admin_group_create(request):
    MODELS =  {
        "planes" : {"app_label" : "plans", "model_name" : "plan", "label" : "Planes"},
        "courses" : {"app_label" : "classes", "model_name" : "course", "label" : "Clases"}
    }
    form = GroupForm()
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
                perms.append({
                "action":    action,
                "codename":  codename,
                "checkbox":  f"perm_{module_key}_{action}"
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

    if request.method == "GET":
        # retornamos todo en una vista
        return render(request, "group_templates/create_group.html", {"data": modules_data, "form" : form})
    
    
    if request.method == "POST":
        # Recopilar todos los permisos que deberia tener el grupo
        perms_to_assign = []
        form = GroupForm(request.POST)
        if form.is_valid():
            group_created = form.save()
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
        else:
            return render(request, "group_templates/create_group.html", {"form" : form, "data" : modules_data})
        group_created.permissions.add(*perms_to_assign)
        messages.success(request, "Grupo Creado correctamente")
        return redirect("accounts_admin_home")
