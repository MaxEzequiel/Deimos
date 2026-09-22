from django.db import models
from django.conf import settings
from django.utils import timezone


class CheckIn(models.Model):
    """Registro de ingreso al gimnasio"""
    
    dni = models.CharField("DNI", max_length=20, db_index=True)
    person = models.ForeignKey(
        'people.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkins',
        verbose_name="Persona"
    )
    fecha = models.DateField("Fecha", default=timezone.localdate)
    hora_entrada = models.DateTimeField("Hora de entrada", default=timezone.now)
    observaciones = models.TextField("Observaciones", blank=True, null=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Registrado por"
    )

    class Meta:
        verbose_name = "Check-in"
        verbose_name_plural = "Check-ins"
        ordering = ['-hora_entrada']

    def __str__(self):
        return f"{self.dni} - {self.hora_entrada.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Asociar persona por id_number (DNI)
        if not self.person and self.dni:
            try:
                from people.models import Person
                self.person = Person.objects.filter(id_number=self.dni).first()
            except Exception:
                pass
        super().save(*args, **kwargs)