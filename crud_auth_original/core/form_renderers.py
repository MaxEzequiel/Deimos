from django.forms.renderers import DjangoTemplates
from django.template.loader import get_template


class DeimosFormRenderer(DjangoTemplates):
	"""Use Deimos layouts while retaining Django's accessible widget markup."""

	form_template_name = "includes/styled_form_fields.html"
	field_template_name = "includes/styled_field.html"

	def get_template(self, template_name):
		custom_templates = {
			"django/forms/errors/list/default.html": "includes/form_errors.html",
			"django/forms/errors/dict/default.html": "includes/form_error_dict.html",
		}
		if template_name in custom_templates:
			return get_template(custom_templates[template_name])
		if template_name in {self.form_template_name, self.field_template_name}:
			return get_template(template_name)
		return super().get_template(template_name)
