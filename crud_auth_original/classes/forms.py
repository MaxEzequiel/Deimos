from django.core import validators
from django import forms
from classes.models import Course, inscription
# meow
class CourseForm(forms.ModelForm):
    model = Course
    fields = ["name","description","teacher","starts_at","ends_at"]
    labels = {
        "name":"Nombre de la clase",
        "description":"descripcion de la clase",
        "starts_at": "fecha y hora de inicio",
        "ends_at": "fecha y hora de finalizacion"
    }
    widgets = forms.DateTimeInput(attrs={"type":"datetime-local"})