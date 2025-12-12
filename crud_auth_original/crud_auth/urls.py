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

from django.contrib import admin
from django.urls import path
from tasks.views import *

urlpatterns = [
    path("admin/", admin.site.urls),
    path("home/",home, name="home"),
    path("singup/", singup, name="singup"),
    path("logout/", singout, name="logout"),
    path("login/", log_in),
    path("delete_user/", delete_user, name="delete_user"),
    path("perfiles/", perfiles, name="perfiles"),
    path("editar_membresia/", editar_membresia, name="editar_membresia"),
    path("crear_plan/", crear_plan, name="crear_plan"),
    path("listar_planes/" , listar_planes, name = "listar_planes"),
    path("editar_plan/<int:id_plan>", editar_plan, name="editar_plan"),
    path("eliminar_plan/<int:id_plan>" , eliminar_plan, name="eliminar_plan"),
    path("pdf_planes/", pdf_planes, name="pdf_planes")
]

