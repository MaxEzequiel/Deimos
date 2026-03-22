from django.db import models


class Plan(models.Model):
    nombre = models.CharField(max_length=60, blank=True, null=True)
    descripcion = models.CharField(max_length=60, blank=True, null=True)
    precio_base = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return self.nombre or "Plan"
