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
                    MinLengthValidator(3, "el nombre del grupo debe tener al menos 3 caracteres")],
        label= "nombre del grupo")
    
    # Validar que el nombre sea único, pero excluir el grupo actual si está siendo editado
    def clean_name(self):
        name = self.cleaned_data['name']
        # Buscar grupos con este nombre
        query = Group.objects.filter(name=name)
        # Si estamos editando (tiene pk y se le pasa una instancia existente) excluir el grupo actual de la búsqueda
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        # Si encuentra otro grupo con el mismo nombre, lanzar error
        if query.exists():
            raise ValidationError(f"el nombre de grupo {name} ya existe")
        return name
    
    class Meta():
        model = Group
        fields = ["name"]
        label = "nombre del grupo"