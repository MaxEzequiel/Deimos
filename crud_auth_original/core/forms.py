from django import forms
from django.utils import timezone


class DateRangeForm(forms.Form):
    desde = forms.DateField(required=False)
    hasta = forms.DateField(required=False)

    def clean(self):
        data = super().clean()
        if data.get("desde") and data.get("hasta") and data["desde"] > data["hasta"]:
            raise forms.ValidationError("La fecha desde debe ser anterior a la fecha hasta")
        return data


class StatisticsPeriodForm(forms.Form):
    anio = forms.IntegerField(required=False, min_value=1, max_value=9999)
    mes = forms.IntegerField(required=False, min_value=1, max_value=12)

    def clean_anio(self):
        return self.cleaned_data.get("anio") or timezone.localdate().year
