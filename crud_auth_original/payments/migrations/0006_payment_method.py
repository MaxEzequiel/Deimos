from django.db import migrations, models


METHODS = [
	("cash", "Efectivo"),
	("transfer", "Transferencia"),
	("card", "Tarjeta"),
]


class Migration(migrations.Migration):
	dependencies = [("pagos", "0005_merge_payment_coverage")]

	operations = [
		migrations.AddField(
			model_name=model_name,
			name="method",
			field=models.CharField(
				blank=True, choices=METHODS, max_length=12,
				verbose_name="Medio de pago",
			),
		)
		for model_name in ("monthlypayment", "paymentmovement")
	]
