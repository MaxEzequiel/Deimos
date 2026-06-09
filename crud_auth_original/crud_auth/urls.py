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
from accounts.views import *
from accounts.groups import *
from memberships.views import edit_membership
from plans.views import create_plan, list_plans, edit_plan, delete_plan, plans_pdf
from classes.views import create_class, edit_class, list_class, delete_class
from .core_view import error_403
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="root"),
    path("home/", home, name="home"),
    # modulo de usuarios
    path("accounts/", list_accounts, name="list_accounts"),
    path("accounts/admin", accounts_admin_home, name = "accounts_admin_home"),
    path("accounts/admin/edit/<int:account_id>", accounts_admin_edit, name="accounts_admin_edit"),
    path("accounts/create/", create_account, name="create_account"),
    path("accounts/logout/", singout, name="logout"),
    path("accounts/login/", login_view, name="login"),
    path("accounts/deactivate-account/<int:account_id>", deactivate_account, name="deactivate_account"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/edit-membership/", edit_membership, name="edit_membership"),
    path("accounts/edit/<int:account_id>", edit_account, name="edit_account"),
    # modulo de planes
    path("create-plan/", create_plan, name="create_plan"),
    path("list-plans/", list_plans, name="list_plans"),
    path("edit-plan/<int:plan_id>", edit_plan, name="edit_plan"),
    path("delete-plan/<int:plan_id>", delete_plan, name="delete_plan"),
    path("plans-pdf/", plans_pdf, name="plans_pdf"),
    # modulo de clases
    path("create-class/", create_class, name="create_class"),
    path("edit-class/<int:course_id>", edit_class, name="edit_class"),
    path("list-class/", list_class, name="list_class"),
    path("delete_class/<int:course_id>",delete_class, name="delete_class"),
    # cure
    path("error_403/", error_403, name="error_403"),
    # grupos de permisos
    path("accounts/admin/groups", accounts_admin_group_list, name="accounts_admin_group_list"),
    path("accounts/admin/groups/create", accounts_admin_group_create, name="accounts_admin_group_create"),
    path("accounts/admin/groups/edit/<int:group_id>", accounts_admin_group_edit, name="accounts_admin_group_edit")
]

