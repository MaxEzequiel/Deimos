from django import forms
from django.contrib.auth.models import User

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["is_staff","username"]
        labels = {"is_staff": "Es staff",
                "username": "Nombre de usuario"}
        
        widgets = {
            "is_staff" : forms.CheckboxInput()
        }