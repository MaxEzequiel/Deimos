from django import forms


class CheckInForm(forms.Form):
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