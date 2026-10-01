from datetime import date

from django import forms
from django.utils import timezone

from .models import MonthlyPayment


class PeriodForm(forms.Form):
    period = forms.DateField(label="Mes", input_formats=["%Y-%m"], widget=forms.DateInput(format="%Y-%m", attrs={"type": "month", "class": "form-control"}))

    def clean_period(self):
        return self.cleaned_data["period"].replace(day=1)


class GeneratePaymentsForm(PeriodForm):
    due_day = forms.IntegerField(label="Día de vencimiento", min_value=1, max_value=31, initial=10, widget=forms.NumberInput(attrs={"class": "form-control"}))

    def clean(self):
        data = super().clean()
        if data.get("period") and data.get("due_day"):
            try:
                date(data["period"].year, data["period"].month, data["due_day"])
            except ValueError:
                self.add_error("due_day", "Ese día no existe en el mes seleccionado.")
        return data


class RecordPaymentForm(forms.ModelForm):
    paid_on = forms.DateField(label="Fecha de pago", initial=timezone.localdate, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}))
    method = forms.ChoiceField(label="Medio de pago", choices=[("", "Seleccionar")] + list(MonthlyPayment.Method.choices), widget=forms.Select(attrs={"class": "form-control"}))

    class Meta:
        model = MonthlyPayment
        fields = ["paid_on", "method", "reference"]
        widgets = {"reference": forms.TextInput(attrs={"class": "form-control"})}


class MemberPaymentForm(RecordPaymentForm):
    period = forms.DateField(label='Mensualidad', input_formats=['%Y-%m'], widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month', 'class': 'form-control'}))

    class Meta(RecordPaymentForm.Meta):
        fields = ['period', 'amount', 'paid_on', 'method', 'reference']
        labels = {'amount': 'Importe del pago'}
        widgets = {**RecordPaymentForm.Meta.widgets, 'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-control'})}

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
