from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Membership

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.contrib.auth.models import User
from people.models import Person

from memberships.forms import MembershipForm

# //// modulo membresia //// 



@login_required
@user_passes_test(lambda user: user.is_staff, login_url="/error_403/")
@transaction.atomic
def edit_membership(request, account_id=None):
    target_user = request.user if account_id is None else get_object_or_404(User, id=account_id)
    membership, created = Membership.objects.get_or_create(user=target_user)

    if request.method == "GET":
        username = target_user.username
        form = MembershipForm(instance=membership)
        return render(request, "edit_membership.html", {"form": form, "username": username})
    else:
        form = MembershipForm(request.POST, instance=membership)
        if form.is_valid():
            with transaction.atomic():
                membership = form.save()
                # Mantiene ambos vínculos históricos sincronizados.
                Person.objects.filter(user=target_user).update(plan=membership.plan)
            messages.success(request, "Membresía y plan actualizados correctamente.")
            return redirect("home")
        return render(request, "edit_membership.html", {"form": form})
