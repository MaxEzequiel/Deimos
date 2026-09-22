from django.urls import path
from . import views

urlpatterns = [
    path('', views.checkin_home, name='checkin_home'),
    path('success/<int:pk>/', views.checkin_success, name='checkin_success'),
    path('history/', views.checkin_history, name='checkin_history'),
]