from django.urls import path
from .management_views import member_list, manage_member

urlpatterns = [
    path('', member_list, name='member_list'),
    path('<int:user_id>/', manage_member, name='manage_member'),
]
