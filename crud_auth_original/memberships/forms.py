from django import forms
from .models import Membership


class MemberManagementForm(forms.ModelForm):
	status = forms.ChoiceField(
		choices=[("active", "Activa"), ("inactive", "Inactiva")],
		label="Estado de membresía",
	)

	class Meta:
		model = Membership
		fields = ["plan", "status"]
		labels = {"plan": "Plan asignado"}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for field in self.fields.values():
			field.widget.attrs["class"] = "module-input"
		self.fields["plan"].required = True

	def clean_plan(self):
		plan = self.cleaned_data["plan"]
		if not plan.base_price or plan.base_price <= 0:
			raise forms.ValidationError("Seleccioná un plan con precio positivo.")
		return plan


class MembershipForm(forms.ModelForm):
	STATUS_CHOICES = [
		("active", "Active"),
		("inactive", "Inactive"),
	]

	status = forms.ChoiceField(
		choices=STATUS_CHOICES,
		widget=forms.Select(attrs={"class": "module-input"}),
		label="Membership status",
	)

	class Meta:
		model = Membership
		fields = ["status"]
