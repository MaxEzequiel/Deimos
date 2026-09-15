from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Payment(models.Model):
    METHOD_CHOICES = (("CASH", "Efectivo"), ("CARD", "Tarjeta"), ("TRANSFER", "Transferencia"))
    STATUS_CHOICES = (("PENDING", "Pendiente"), ("PAID", "Pagado"), ("CANCELLED", "Cancelado"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PAID")
    paid_at = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ("-paid_at",)
