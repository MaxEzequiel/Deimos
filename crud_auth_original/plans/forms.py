from django import forms
from .models import Plan
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator,MinLengthValidator,MinValueValidator

def plan_name_unique_validator(value):
    if Plan.objects.filter(name=value).exists():
        raise ValidationError("este nombre de plan ya se encuentra registrado")

def plan_description_unique_validator(value):
    if Plan.objects.filter(description=value).exists():
        raise ValidationError("esta descripcion ya se encuentra en uso")


class PlanForm(forms.ModelForm):
    name = forms.CharField(
        validators=[MinLengthValidator(3,"El nombre del plan debe tener al menos 3 caracteres"),
                    MaxLengthValidator(50, "El nombre del plan no debe superar los 50 caracteres")],
        label="nombre del plan"
    )
    
    description = forms.CharField(
        validators=[MinLengthValidator(5, "La descripcion debe tener al menos 5 caracteres"),
                    MaxLengthValidator(180,"La descripcion del plan no debe superar los 180 caracteres")],
        label="descripcion del plan"
    )
    
    base_price = forms.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(100, "el precio minimo es de $100.00")],
        label="Precio del plan"
    )

    def clean_name(self):
        value = self.cleaned_data["name"]
        if Plan.objects.filter(name=value).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Este nombre de plan ya se encuentra registrado")
        return value

    def clean_description(self):
        value = self.cleaned_data["description"]
        if Plan.objects.filter(description=value).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Esta descripción ya se encuentra en uso")
        return value
    
    class Meta:
        model = Plan
        fields = ["name", "description", "base_price"]
        labels = {
            "name": "nombre del plan",
            "description": "descripcion del plan",
            "base_price": "precio del plan",
        }
