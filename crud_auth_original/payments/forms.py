from django import forms
from django.utils import timezone

from .models import MonthlyPayment


class RecordPaymentForm(forms.ModelForm):
    paid_on = forms.DateField(label="Fecha de pago", initial=timezone.localdate, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "module-input"}))

    class Meta:
        model = MonthlyPayment
        fields = ["paid_on", "reference"]
        widgets = {"reference": forms.TextInput(attrs={"class": "module-input"})}


class MemberPaymentForm(RecordPaymentForm):
    period = forms.DateField(label='Mes del pago', input_formats=['%Y-%m'], widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month', 'class': 'module-input'}))

    class Meta(RecordPaymentForm.Meta):
        fields = ['period', 'amount', 'paid_on', 'reference']
        labels = {'amount': 'Importe del pago'}
        widgets = {**RecordPaymentForm.Meta.widgets, 'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'module-input'})}

    def __init__(self, *args, member, **kwargs):
        self.member = member
        super().__init__(*args, **kwargs)

    def clean_period(self):
        return self.cleaned_data['period'].replace(day=1)

    def clean(self):
        data = super().clean()
        if data.get('period'):
            existing = MonthlyPayment.objects.filter(member=self.member, period=data['period']).first()
            if existing and existing.paid_on:
                self.add_error('period', 'Esta mensualidad ya está pagada')
            elif existing and data.get('amount') is not None and existing.amount != data['amount']:
                self.add_error('amount', f'La cuota pendiente tiene un importe de ${existing.amount}. Ingresá ese importe para saldarla')
        return data
