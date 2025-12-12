from django import forms
from .models import Membresia,Plan

class MembresiaForm(forms.ModelForm):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
    ]
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Estado de Membresía"
    )

    class Meta:
        model = Membresia
        fields = ['estado']  # Solo el campo estado, id_cliente se asigna en la vista

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["nombre", "descripcion", "precio_base"]
        labels = {
        "nombre" : "nombre del plan", 
        "descripcion" : "descripcion del plan",
        "precio_base" : "precio del plan"
        }