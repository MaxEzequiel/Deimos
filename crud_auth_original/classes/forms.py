from django.core import validators
from django import forms
from classes.models import Course, Inscription


# meow
class CourseForm(forms.ModelForm):
	class Meta:
		model = Course
		fields = ["name", "description", "starts_at", "ends_at", "max_capacity", "price"]
		labels = {
			"name": "Nombre de la clase",
			"description": "descripcion de la clase",
			"starts_at": "fecha y hora de inicio",
			"ends_at": "fecha y hora de finalizacion",
			"max_capacity": "capacidad maxima de alumnos",
		}
		widgets = {
			"starts_at": forms.DateTimeInput(
				format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
			),
			"ends_at": forms.DateTimeInput(
				format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
			),
		}
