from django.db import migrations


def import_history(apps, schema_editor):
    Charge = apps.get_model("pagos", "MonthlyPayment")
    Movement = apps.get_model("pagos", "PaymentMovement")
    alias = schema_editor.connection.alias
    for charge in Charge.objects.using(alias).filter(paid_on__isnull=False).iterator():
        Movement.objects.using(alias).create(
            charge_id=charge.pk, amount=charge.amount, paid_on=charge.paid_on,
            method=charge.method, reference=charge.reference, recorded_by_id=charge.recorded_by_id,
        )


class Migration(migrations.Migration):
    dependencies = [("pagos", "0002_paymentmovement")]
    operations = [migrations.RunPython(import_history, migrations.RunPython.noop)]
