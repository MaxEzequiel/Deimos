from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from tutorials.models import Publication
from tutorials.forms import PublicationForm


# --- VER: cualquier usuario con permiso view_publication ---
@login_required
@permission_required("tutorials.view_publication", login_url="/error_403")
def list_publications(request):
    publications = Publication.objects.all()
    puede_editar = (
        request.user.has_perm("tutorials.add_publication")
        or request.user.has_perm("tutorials.change_publication")
        or request.user.has_perm("tutorials.delete_publication")
    )
    return render(request, "list_publications.html", {
        "publications": publications,
        "puede_editar": puede_editar,
    })


@login_required
@permission_required("tutorials.view_publication", login_url="/error_403")
def detail_publication(request, publication_id):
    publication = get_object_or_404(Publication, id=publication_id)
    puede_editar = (
        request.user.has_perm("tutorials.add_publication")
        or request.user.has_perm("tutorials.change_publication")
        or request.user.has_perm("tutorials.delete_publication")
    )
    return render(request, "detail_publication.html", {
        "publication": publication,
        "puede_editar": puede_editar,
    })


# --- CREAR: solo quien tenga add_publication ---
@login_required
@permission_required("tutorials.add_publication", login_url="/error_403")
def create_publication(request):
    if request.method == "GET":
        return render(request, "create_publication.html", {"publication_form": PublicationForm()})
    else:
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("list_publications")
        return render(request, "create_publication.html", {"publication_form": form})


# --- EDITAR: solo quien tenga change_publication ---
@login_required
@permission_required("tutorials.change_publication", login_url="/error_403")
def edit_publication(request, publication_id):
    publication = get_object_or_404(Publication, id=publication_id)
    if request.method == "GET":
        return render(request, "edit_publication.html", {"publication_form": PublicationForm(instance=publication)})
    else:
        form = PublicationForm(request.POST, request.FILES, instance=publication)
        if form.is_valid():
            form.save()
            return redirect("list_publications")
        return render(request, "edit_publication.html", {"publication_form": form})


# --- ELIMINAR: solo quien tenga delete_publication ---
@login_required
@permission_required("tutorials.delete_publication", login_url="/error_403")
def delete_publication(request, publication_id):
    publication = get_object_or_404(Publication, id=publication_id)
    if request.method == "GET":
        return render(request, "delete_publication.html", {"publication": publication})
    else:
        publication.delete()
        return redirect("list_publications")