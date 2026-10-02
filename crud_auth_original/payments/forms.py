from datetime import date

from django import forms
from django.utils import timezone

from .models import MonthlyPayment


class PeriodForm(forms.Form):
    period = forms.DateField(label="Mes", input_formats=["%Y-%m"], widget=forms.DateInput(format="%Y-%m", attrs={"type": "month", "class": "module-input"}))

    def clean_period(self):
        return self.cleaned_data["period"].replace(day=1)


class PaymentFilterForm(forms.Form):
    period_from = forms.DateField(label="Mes desde", required=False, input_formats=["%Y-%m"], widget=forms.DateInput(format="%Y-%m", attrs={"type": "month", "class": "module-input"}))
    period_to = forms.DateField(label="Mes hasta", required=False, input_formats=["%Y-%m"], widget=forms.DateInput(format="%Y-%m", attrs={"type": "month", "class": "module-input"}))

    def clean_period_from(self):
        period = self.cleaned_data.get("period_from")
        return period.replace(day=1) if period else period

    def clean_period_to(self):
        period = self.cleaned_data.get("period_to")
        return period.replace(day=1) if period else period

    def clean(self):
        data = super().clean()
        period_from = data.get("period_from")
        period_to = data.get("period_to")
        if period_from and period_to and period_from > period_to:
            self.add_error("period_to", "El mes hasta debe ser igual o posterior al mes desde.")
        return data


class GeneratePaymentsForm(PeriodForm):
    due_day = forms.IntegerField(label="Día de vencimiento", min_value=1, max_value=31, initial=10, widget=forms.NumberInput(attrs={"class": "module-input"}))

    def clean(self):
        data = super().clean()
        if data.get("period") and data.get("due_day"):
            try:
                date(data["period"].year, data["period"].month, data["due_day"])
            except ValueError:
                self.add_error("due_day", "Ese día no existe en el mes seleccionado.")
        return data


class RecordPaymentForm(forms.ModelForm):
    paid_on = forms.DateField(label="Fecha de pago", initial=timezone.localdate, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "module-input"}))
    method = forms.ChoiceField(label="Medio de pago", choices=[("", "Seleccionar")] + list(MonthlyPayment.Method.choices), widget=forms.Select(attrs={"class": "module-input"}))

    class Meta:
        model = MonthlyPayment
        fields = ["paid_on", "method", "reference"]
        widgets = {"reference": forms.TextInput(attrs={"class": "module-input"})}


class MemberPaymentForm(RecordPaymentForm):
    period = forms.DateField(label='Mensualidad', input_formats=['%Y-%m'], widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month', 'class': 'module-input'}))

    class Meta(RecordPaymentForm.Meta):
        fields = ['period', 'amount', 'paid_on', 'method', 'reference']
        labels = {'amount': 'Importe del pago'}
        widgets = {**RecordPaymentForm.Meta.widgets, 'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'module-input'})}

    def __init__(self, *args, member, **kwargs):
        self.member = member
        super().__init__(*args, **kwargs)
        self.fields['amount'].help_text = 'Se completa con el precio del plan del socio. Puede ajustarse manualmente si corresponde.'

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
