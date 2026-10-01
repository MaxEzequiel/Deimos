from django import forms
from people.models import Person


class CheckInForm(forms.Form):
    def clean_dni(self):
        dni = self.cleaned_data['dni'].strip()
        if not dni.isascii() or not dni.isdecimal() or not 100000 <= int(dni) <= 9999999999:
            raise forms.ValidationError("Ingresá un DNI válido de 6 a 10 dígitos")
        dni = str(int(dni))
        people = list(Person.objects.select_related('user').filter(id_number=int(dni))[:2])
        if not people:
            raise forms.ValidationError("No existe un socio registrado con ese DNI")
        if len(people) > 1:
            raise forms.ValidationError("El DNI pertenece a más de un socio. Corregí los registros antes de continuar")
        self.person = people[0]
        return dni

    dni = forms.CharField(
        label="DNI",
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ingresá tu DNI',
            'autofocus': True,
            'autocomplete': 'off',
            'class': 'checkin-input',
        })
    )
    observaciones = forms.CharField(
        label="Observaciones (opcional)",
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Ej: Ingresó con lesión, etc.',
            'rows': 2,
            'class': 'checkin-textarea',
        })
    )
