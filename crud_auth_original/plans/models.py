from django.db import models


class Plan(models.Model):
    name = models.CharField(max_length=60, blank=True, null=True)
    description = models.CharField(max_length=60, blank=True, null=True)
    base_price = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        db_table = "planes_plan"

    def __str__(self):
        return self.name or "Plan"
