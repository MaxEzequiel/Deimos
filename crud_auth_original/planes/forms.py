from django import forms
from .models import Plan

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["nombre", "descripcion", "precio_base"]
        labels = {
            "nombre": "nombre del plan",
            "descripcion": "descripcion del plan",
            "precio_base": "precio del plan",
        }
