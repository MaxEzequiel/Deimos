from django.urls import path

from . import views
from memberships.management_views import manage_member

urlpatterns = [
    path("", views.subscription_list),
    path("subscriptions/<int:user_id>/", manage_member, name="manage_member"),
    path("subscriptions/", views.subscription_list, name="subscription_list"),
    path("subscriptions/<int:user_id>/pay/", views.pay_subscription, name="pay_subscription"),
    path("history/", views.payment_history, name="payment_history"),
    path("history/<int:movement_id>/cancel/", views.cancel_payment, name="cancel_payment"),
]
