from django import forms
from tutorials.models import Publication


class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ["title", "description", "content", "image"]
