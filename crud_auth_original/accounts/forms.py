from cProfile import label
from os import name
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.validators import MaxLengthValidator,MinLengthValidator,ValidationError

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["is_staff","username"]
        labels = {"is_staff": "Es staff",
                "username": "Nombre de usuario"}
        
        widgets = {
            "is_staff" : forms.CheckboxInput()
        }


def unique_group_validator(value):
    if Group.objects.filter(name = value).exists():
        raise ValidationError(f"el nombre de grupo {value} ya existe")

class GroupForm(forms.ModelForm):
    name = forms.CharField(
        validators= [MaxLengthValidator(50, "el nombre del grupo no debe superar los 40 caracteres"),
                    MinLengthValidator(3, "el nombre del grupo debe tener al menos 3 caracteres"),
                    unique_group_validator],
        label= "nombre del grupo")
    
    class Meta():
        model = Group
        fields = ["name"]
        label = "nombre del grupo"