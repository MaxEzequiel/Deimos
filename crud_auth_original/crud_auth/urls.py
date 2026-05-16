"""
URL configuration for crud_auth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth import views
from django.contrib import admin
from django.urls import path, include
from accounts.views import home, signup, signout, login_view, delete_account
from memberships.views import edit_membership
from plans.views import create_plan, list_plans, edit_plan, delete_plan, plans_pdf
from classes.views import create_class, edit_class, list_class
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="root"),
    path("home/", home, name="home"),
    path("signup/", signup, name="signup"),
    path("logout/", signout, name="logout"),
    path("login/", login_view, name="login"),
    path("delete-account/", delete_account, name="delete_account"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("edit-membership/", edit_membership, name="edit_membership"),
    path("create-plan/", create_plan, name="create_plan"),
    path("list-plans/", list_plans, name="list_plans"),
    path("edit-plan/<int:plan_id>", edit_plan, name="edit_plan"),
    path("delete-plan/<int:plan_id>", delete_plan, name="delete_plan"),
    path("plans-pdf/", plans_pdf, name="plans_pdf"),
    path("create-class/", create_class, name="create_class"),
    path("edit-class/<int:course_id>", edit_class, name="edit_class"),
    path("list_class/", list_class, name="list_class")
]

