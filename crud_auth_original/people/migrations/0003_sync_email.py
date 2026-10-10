from django.db import migrations


def sync_email(apps, schema_editor):
	Person = apps.get_model("people", "Person")
	User = apps.get_model("auth", "User")
	alias = schema_editor.connection.alias
	for person in Person.objects.using(alias).select_related("user").iterator():
		# Preserve the profile email already shown in the application.
		email = person.email or person.user.email or ""
		User.objects.using(alias).filter(pk=person.user_id).update(email=email)
		Person.objects.using(alias).filter(pk=person.pk).update(email=email)


class Migration(migrations.Migration):
	dependencies = [
		("people", "0002_alter_person_email_alter_person_gender_and_more"),
		("auth", "0012_alter_user_first_name_max_length"),
	]
	operations = [migrations.RunPython(sync_email, migrations.RunPython.noop)]
