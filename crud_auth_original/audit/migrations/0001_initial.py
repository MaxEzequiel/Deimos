from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("CREATE", "Creación"), ("UPDATE", "Actualización"), ("DELETE", "Eliminación")], max_length=10)),
                ("resource", models.CharField(max_length=120)),
                ("object_id", models.CharField(blank=True, max_length=64)),
                ("path", models.CharField(max_length=255)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "evento de auditoría", "verbose_name_plural": "eventos de auditoría", "ordering": ("-created_at",)},
        ),
    ]
