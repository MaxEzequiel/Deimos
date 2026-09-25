from django.urls import path
from tutorials.views import (
    create_publication,
    list_publications,
    detail_publication,
    edit_publication,
    delete_publication,
)

urlpatterns = [
    path("publications/", list_publications, name="list_publications"),
    path("publications/create/", create_publication, name="create_publication"),
    path("publications/<int:publication_id>/", detail_publication, name="detail_publication"),
    path("publications/<int:publication_id>/edit/", edit_publication, name="edit_publication"),
    path("publications/<int:publication_id>/delete/", delete_publication, name="delete_publication"),
]
