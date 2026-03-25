from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Membership

from django.contrib.auth.decorators import login_required

from memberships.forms import MembershipForm

# //// modulo membresia //// 



@login_required
def edit_membership(request):
    membership, created = Membership.objects.get_or_create(user=request.user)

    if request.method == "GET":
        username = request.user.username
        form = MembershipForm(instance=membership)
        return render(request, "edit_membership.html", {"form": form, "username": username})
    else:
        form = MembershipForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            messages.success(request, "Membership updated")
            return redirect("home")
        return render(request, "edit_membership.html", {"form": form})