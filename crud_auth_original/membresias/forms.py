from django import forms
from .models import Membresia

class MembresiaForm(forms.ModelForm):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
    ]

    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Estado de Membresía'
    )

    class Meta:
        model = Membresia
        fields = ['estado']
