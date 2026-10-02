from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class MonthlyPayment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Efectivo"
        TRANSFER = "transfer", "Transferencia"
        CARD = "card", "Tarjeta"

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="monthly_payments", verbose_name="Socio")
    period = models.DateField("Mes de la cuota", help_text="Se guarda como el primer día del mes.")
    amount = models.DecimalField("Importe", max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    due_date = models.DateField("Vencimiento")
    paid_on = models.DateField("Fecha de pago", null=True, blank=True)
    coverage_start = models.DateField("Inicio de vigencia", null=True, blank=True)
    coverage_end = models.DateField("Fin de vigencia", null=True, blank=True)
    method = models.CharField("Medio de pago", max_length=12, choices=Method.choices, blank=True)
    reference = models.CharField("Referencia del comprobante", max_length=100, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="recorded_monthly_payments", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period", "member__username"]
        verbose_name = "mensualidad"
        verbose_name_plural = "mensualidades"
        constraints = [
            models.UniqueConstraint(fields=["member", "period"], name="unique_member_month"),
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="monthly_payment_positive_amount"),
            models.CheckConstraint(condition=(models.Q(paid_on__isnull=True, method="") | (models.Q(paid_on__isnull=False) & ~models.Q(method=""))), name="monthly_payment_payment_details"),
        ]

    @property
    def status(self):
        if self.paid_on:
            return "paid"
        return "overdue" if self.due_date < timezone.localdate() else "pending"

    @property
    def status_label(self):
        return {"paid": "Pagada", "overdue": "Vencida", "pending": "Pendiente"}[self.status]

    def clean(self):
        super().clean()
        errors = {}
        if self.period and self.period.day != 1:
            errors["period"] = "El período debe ser el primer día del mes."
        if self.period and self.due_date and (self.period.year, self.period.month) != (self.due_date.year, self.due_date.month):
            errors["due_date"] = "El vencimiento debe pertenecer al mes de la cuota."
        if self.paid_on and self.paid_on > timezone.localdate():
            errors["paid_on"] = "La fecha de pago no puede ser futura."
        if bool(self.paid_on) != bool(self.method):
            errors["method"] = "Indicá la fecha y el medio de pago juntos."
        if bool(self.coverage_start) != bool(self.coverage_end):
            errors["coverage_start"] = "Indicá inicio y fin de vigencia juntos."
        if self.coverage_start and self.coverage_end and self.coverage_end <= self.coverage_start:
            errors["coverage_end"] = "El fin de vigencia debe ser posterior al inicio."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.member} · {self.period:%m/%Y}"
