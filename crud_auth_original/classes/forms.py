from django.core import validators
from django import forms
from classes.models import Course, inscription
# meow
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name","description","starts_at","ends_at"]
        labels = {
            "name":"Nombre de la clase",
            "description":"descripcion de la clase",
            "starts_at": "fecha y hora de inicio",
            "ends_at": "fecha y hora de finalizacion"
        }
        widgets = {
            'starts_at': forms.DateTimeInput(attrs={"type": "datetime-local"}),
            'ends_at': forms.DateTimeInput(attrs={"type": "datetime-local"})
        }