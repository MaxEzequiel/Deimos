from django import forms
from .models import Plan

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["name", "description", "base_price"]
        labels = {
            "name": "nombre del plan",
            "description": "descripcion del plan",
            "base_price": "precio del plan",
        }
