from django import forms
from people.models import Person

class PersonForm(forms.ModelForm):
    required_marker_fields = {'id_number', 'birth_date', 'email'}

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
            'birth_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.required_marker_fields:
            self.fields[field_name].required = True
