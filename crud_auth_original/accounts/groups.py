from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from accounts.forms import GroupForm
from accounts.signals import clear_permission_cache
from core.audit import audit
from core.decorators import superuser_required

MODULES = {
    'planes': ('plans', 'plan', 'Planes'),
    'pagos': ('pagos', 'monthlypayment', 'Mensualidades'),
    'courses': ('classes', 'course', 'Clases'),
    'tutorials': ('tutorials', 'publication', 'Publicaciones'),
}


@login_required
@superuser_required
@require_GET
def accounts_admin_group_list(request):
    return render(request, 'group_templates/list_groups.html', {'groups': Group.objects.all()})


def _group_form(request, group=None):
    modules_data = []
    selected = set(group.permissions.values_list('pk', flat=True)) if group else set()
    available = {}
    for key, (app, model, label) in MODULES.items():
        perms = []
        for action in ('add', 'change', 'delete', 'view'):
            codename = f'{action}_{model}'
            perm = Permission.objects.filter(content_type__app_label=app, content_type__model=model, codename=codename).first()
            if perm:
                checkbox = f'perm_{key}_{action}'
                available[checkbox] = perm
                perms.append({'action': action, 'codename': codename, 'checkbox': checkbox, 'has_perm': checkbox in request.POST if request.method == 'POST' else perm.pk in selected})
        modules_data.append({'key': key, 'label': label, 'perms': perms})
    form = GroupForm(request.POST if request.method == 'POST' else None, instance=group)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            editing = group is not None
            group = form.save()
            # Keep permissions belonging to modules not edited by this screen.
            retained = group.permissions.exclude(pk__in=[p.pk for p in available.values()])
            group.permissions.set(list(retained) + [p for checkbox, p in available.items() if checkbox in request.POST])
            clear_permission_cache(request.user)
            audit(request, 'UPDATE' if editing else 'CREATE', f'grupo: {group.id} - {group.name}')
        messages.success(request, 'Grupo guardado correctamente')
        return redirect('accounts_admin_home')
    template = 'edit_group.html' if group else 'create_group.html'
    return render(request, f'group_templates/{template}', {'form': form, 'data': modules_data, 'group': group})


@login_required
@superuser_required
@require_http_methods(['GET', 'POST'])
def accounts_admin_group_create(request):
    return _group_form(request)


@login_required
@superuser_required
@require_http_methods(['GET', 'POST'])
def accounts_admin_group_edit(request, group_id):
    return _group_form(request, get_object_or_404(Group, pk=group_id))
