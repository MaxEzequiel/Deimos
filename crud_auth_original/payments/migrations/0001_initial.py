from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="Payment", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("amount", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)])),
        ("method", models.CharField(choices=[("CASH", "Efectivo"), ("CARD", "Tarjeta"), ("TRANSFER", "Transferencia")], max_length=10)),
        ("status", models.CharField(choices=[("PENDING", "Pendiente"), ("PAID", "Pagado"), ("CANCELLED", "Cancelado")], default="PAID", max_length=10)),
        ("paid_at", models.DateTimeField(auto_now_add=True)), ("reference", models.CharField(blank=True, max_length=80)),
        ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ("-paid_at",)})]
