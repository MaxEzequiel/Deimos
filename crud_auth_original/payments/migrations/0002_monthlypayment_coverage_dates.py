from calendar import monthrange
from datetime import date

from django.db import migrations, models


def next_month_expiry(paid_on):
    year = paid_on.year + (paid_on.month == 12)
    month = paid_on.month % 12 + 1
    return date(year, month, min(paid_on.day, monthrange(year, month)[1]))


def fill_coverage_dates(apps, schema_editor):
    MonthlyPayment = apps.get_model("pagos", "MonthlyPayment")
    for payment in MonthlyPayment.objects.filter(paid_on__isnull=False, coverage_start__isnull=True):
        payment.coverage_start = payment.paid_on
        payment.coverage_end = next_month_expiry(payment.paid_on)
        payment.save(update_fields=["coverage_start", "coverage_end"])


class Migration(migrations.Migration):

    dependencies = [
        ("pagos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="monthlypayment",
            name="coverage_start",
            field=models.DateField(blank=True, null=True, verbose_name="Inicio de vigencia"),
        ),
        migrations.AddField(
            model_name="monthlypayment",
            name="coverage_end",
            field=models.DateField(blank=True, null=True, verbose_name="Fin de vigencia"),
        ),
        migrations.RunPython(fill_coverage_dates, migrations.RunPython.noop),
    ]
