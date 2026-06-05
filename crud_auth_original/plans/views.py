from django.shortcuts import render, redirect, get_object_or_404
from plans.models import Plan

# modulo de pdf
from django_xhtml2pdf.utils import pdf_decorator

# funciones para el inicio de sesion

from django.contrib.auth.decorators import login_required, permission_required

from plans.forms import PlanForm

@login_required
@permission_required(["plans.add_plan","plans.view_plan"], login_url="/error_403")
def create_plan(request):
    if request.method == "POST":
        plan = PlanForm(request.POST)
        if plan.is_valid():
            plan.save()
            return redirect("home")
        else:
            return render(request, "create_plan.html", {"plan_form": plan})
    else:
        return render(request, "create_plan.html", {"plan_form": PlanForm()})

@login_required
@permission_required("plans.view_plan", login_url="/error_403")
def list_plans(request):
    if request.method == "GET":
        plans = Plan.objects.all()
        return render(request, "list_plans.html", {"plans": plans})

@login_required
@pdf_decorator
@permission_required(["plans.view_plan"], login_url="/error_403")
def plans_pdf(request):
    if request.method == "GET":
        plans = Plan.objects.all()
        return render(request, "plans_pdf.html", {"plans": plans})

@login_required
@permission_required(["plans.change_plan","plans.view_plan"], login_url="/error_403")
def edit_plan(request, plan_id):
    plan = Plan.objects.get(id=plan_id)
    if request.method == "GET":
        form = PlanForm(instance=plan)
        return render(request, "edit_plan.html", {"form": form})
    else:
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return redirect("list_plans")
        else:
            error = "form is invalid, please verify the fields"
            return render(request, "edit_plan.html", {"form": form, "error": error})

@login_required
@permission_required(["plans.delete_plan","plans.view_plan"], login_url="/error_403")
def delete_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if request.method == "GET":
        return render(request, "delete_plan.html")
    else:
        plan.delete()
        return redirect("list_plans")
