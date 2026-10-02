from django import forms
from .models import Membership


class MemberManagementForm(forms.ModelForm):
    status = forms.ChoiceField(choices=[('active', 'Activa'), ('inactive', 'Inactiva')], label='Estado de membresía')

    class Meta:
        model = Membership
        fields = ['plan', 'status']
        labels = {'plan': 'Plan asignado'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'module-input'

class MembershipForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'module-input'}),
        label='Membership status'
    )

    class Meta:
        model = Membership
        fields = ['status']
