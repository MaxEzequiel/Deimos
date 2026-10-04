from django.urls import path
from django.views.generic import RedirectView
from .management_views import member_list

urlpatterns = [
    path('', member_list, name='member_list'),
    path('<int:user_id>/', RedirectView.as_view(pattern_name='manage_member', permanent=False)),
]
