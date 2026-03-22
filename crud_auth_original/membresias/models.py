from django.db import models
from django.conf import settings


class Membresia(models.Model):
    id_cliente = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    estado = models.CharField(max_length=12, default="inactivo")
    id_plan = models.ForeignKey("planes.Plan", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"Membresia {self.id_cliente.username}: {self.estado}"
