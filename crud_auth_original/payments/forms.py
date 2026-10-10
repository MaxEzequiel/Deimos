from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import MonthlyPayment, PAYMENT_METHODS, PAYMENT_KINDS
from classes.models import Course


class RecordPaymentForm(forms.ModelForm):
	paid_on = forms.DateField(
		label="Fecha de pago",
		initial=timezone.localdate,
		widget=forms.DateInput(
			format="%Y-%m-%d", attrs={"type": "date", "class": "module-input"}
		),
	)

	class Meta:
		model = MonthlyPayment
		fields = ["paid_on"]


class MemberPaymentForm(RecordPaymentForm):
	kind = forms.ChoiceField(label="Qué desea pagar", choices=PAYMENT_KINDS, required=False, initial="gym")
	courses = forms.ModelMultipleChoiceField(label="Clases a pagar", queryset=Course.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)

	method = forms.ChoiceField(
		label="Medio de pago",
		choices=[("", "Seleccioná un medio de pago"), *PAYMENT_METHODS],
		widget=forms.Select(attrs={"class": "module-input"}),
	)
	period = forms.DateField(
		label="Mes del pago",
		input_formats=["%Y-%m"],
		widget=forms.DateInput(
			format="%Y-%m", attrs={"type": "month", "class": "module-input"}
		),
	)

	class Meta(RecordPaymentForm.Meta):
		fields = ["period", "amount", "paid_on", "method"]
		labels = {"amount": "Importe del pago"}
		widgets = {
			"amount": forms.NumberInput(
				attrs={"step": "0.01", "min": "0.01", "class": "module-input"}
			)
		}

	def __init__(self, *args, member, selected_plan=None, **kwargs):
		self.member = member
		self.selected_plan = selected_plan
		super().__init__(*args, **kwargs)
		from .services import available_payment_courses
		self.fields["courses"].queryset = available_payment_courses(member)
		self.fields["courses"].help_text = "Seleccioná una o más clases. Al confirmar el pago se registra la inscripción."
		self.fields["courses"].label_from_instance = lambda course: f"{course.name} - ${course.price}"
		self.fields["amount"].widget.attrs["readonly"] = True
		self.fields["amount"].help_text = (
			"Se suma el precio de musculación y/o las clases seleccionadas. Las cuotas pendientes conservan "
			"su importe original."
		)
		self.order_fields(["period", "kind", "courses", "amount", "paid_on", "method"])

	def clean_period(self):
		return self.cleaned_data["period"].replace(day=1)

	def clean(self):
		data = super().clean()
		data["kind"] = data.get("kind") or "gym"
		if data.get("period"):
			existing = MonthlyPayment.objects.filter(member=self.member, period=data["period"]).first()
			if existing and existing.paid_on:
				self.add_error("period", "Esta mensualidad ya está pagada")
			elif existing:
				if data["kind"] != existing.kind:
					self.add_error("kind", "La cuota pendiente conserva su concepto original.")
				if data.get("amount") != existing.amount:
					self.add_error("amount", f"La cuota pendiente tiene un importe de ${existing.amount}.")
			else:
				from .services import payment_quote
				try:
					amount, items = payment_quote(self.member, data["kind"], data.get("courses", ()), self.selected_plan)
				except ValidationError as error:
					self.add_error(None, error)
				else:
					if data.get("amount") != amount:
						self.add_error("amount", f"El importe debe coincidir con el precio final: ${amount}.")
		return data
