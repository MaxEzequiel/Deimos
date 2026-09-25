from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from tutorials.models import Publication
from tutorials.forms import PublicationForm


@login_required
@permission_required(["tutorials.view_publication", "tutorials.add_publication"], login_url="/error_403")
def create_publication(request):
    if request.method == "GET":
        return render(request, "create_publication.html", {"publication_form": PublicationForm()})
    else:
        publication_form = PublicationForm(request.POST, request.FILES)
        if publication_form.is_valid():
            publication_form.save()
            return redirect("list_publications")
        return render(request, "create_publication.html", {"publication_form": publication_form})


@login_required
@permission_required(["tutorials.view_publication"], login_url="/error_403")
def list_publications(request):
    publications = Publication.objects.all()
    return render(request, "list_publications.html", {"publications": publications})


@login_required
@permission_required(["tutorials.view_publication"], login_url="/error_403")
def detail_publication(request, publication_id):
    publication = Publication.objects.get(id=publication_id)
    return render(request, "detail_publication.html", {"publication": publication})


@login_required
@permission_required(["tutorials.view_publication", "tutorials.change_publication"], login_url="/error_403")
def edit_publication(request, publication_id):
    publication = Publication.objects.get(id=publication_id)
    if request.method == "GET":
        return render(request, "edit_publication.html", {"publication_form": PublicationForm(instance=publication)})
    else:
        publication_form = PublicationForm(request.POST, request.FILES, instance=publication)
        if publication_form.is_valid():
            publication_form.save()
            return redirect("list_publications")
        return render(request, "edit_publication.html", {"publication_form": publication_form})


@login_required
@permission_required(["tutorials.view_publication", "tutorials.delete_publication"], login_url="/error_403")
def delete_publication(request, publication_id):
    publication = Publication.objects.get(id=publication_id)
    if request.method == "GET":
        return render(request, "delete_publication.html", {"publication": publication})
    else:
        publication.delete()
        return redirect("list_publications")
