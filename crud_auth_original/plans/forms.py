from django import forms
from .models import Plan
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator,MinLengthValidator

def plan_name_unique_validator(value):
    if Plan.objects.filter(name=value).exists():
        raise ValidationError("este nombre de plan ya se encuentra registrado")

def plan_description_unique_validator(value):
    if Plan.objects.filter(name=value).exists():
        raise ValidationError("esta descripcion ya se encuentra en uso")


class PlanForm(forms.ModelForm):
    name = forms.CharField(
        validators=[plan_name_unique_validator,
                    MinLengthValidator(3,"El nombre del plan debe tener al menos 3 caracteres"),
                    MaxLengthValidator(50, "El nombre del plan no debe superar los 50 caracteres")],
        label="nombre del plan"
    )
    
    description = forms.CharField(
        validators=[plan_description_unique_validator,
                    MinLengthValidator(5, "La descripcion debe tener al menos 5 caracteres"),
                    MaxLengthValidator(180,"La descripcion del plan no debe superar los 180 caracteres")],
        label="descripcion del plan"
    )
    
    class Meta:
        model = Plan
        fields = ["name", "description", "base_price"]
        labels = {
            "name": "nombre del plan",
            "description": "descripcion del plan",
            "base_price": "precio del plan",
        }
