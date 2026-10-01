from django.urls import path

from . import views

urlpatterns = [
    path("", views.payment_list, name="payment_list"),
    path("generate/", views.generate_payments, name="generate_payments"),
    path("<int:payment_id>/record/", views.record_payment, name="record_payment"),
]
