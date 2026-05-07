from django import forms
from people.models import Person

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['id_number', 'name', 'surname', 'birth_date', 'gender', 'phone_number', 'email']
        labels = {
            'id_number': 'DNI',
            'name': 'Nombre',
            'surname': 'Apellido',
            'birth_date': 'Fecha de nacimiento',
            'gender': 'Género',
            'phone_number': 'Teléfono',
            'email': 'Correo electrónico',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }