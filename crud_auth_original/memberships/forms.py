from django import forms
from .models import Membership

class MembershipForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Membership status'
    )

    class Meta:
        model = Membership
        fields = ['status']
