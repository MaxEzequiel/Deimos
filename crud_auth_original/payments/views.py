from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import redirect, render
from .forms import PaymentForm
from .models import Payment

@login_required
@permission_required("pagos.view_payment", login_url="/error_403/")
def list_payments(request):
    return render(request, "payments/list.html", {"payments": Payment.objects.select_related("user")})

@login_required
@permission_required("pagos.add_payment", login_url="/error_403/")
@transaction.atomic
def create_payment(request):
    form = PaymentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pago registrado correctamente.")
        return redirect("list_payments")
    return render(request, "payments/create.html", {"form": form})
