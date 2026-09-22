from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Membership(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=12, default="inactive")
    plan = models.ForeignKey("plans.Plan", on_delete=models.SET_NULL, blank=True, null=True)
    
    # Nuevos campos
    start_date = models.DateField("Fecha de inicio", null=True, blank=True)
    end_date = models.DateField("Fecha de vencimiento", null=True, blank=True)
    
    # Duración por defecto (30 días si el plan no la define)
    DEFAULT_DURATION_DAYS = 30
    
    def save(self, *args, **kwargs):
        # Si tiene fecha de inicio pero no de vencimiento, calcularla
        if self.start_date and not self.end_date:
            # Por ahora todos los planes duran 30 días
            # Si después agregás duración al Plan, cambialo por self.plan.duration_days
            self.end_date = self.start_date + timedelta(days=self.DEFAULT_DURATION_DAYS)
        super().save(*args, **kwargs)
    
    @property
    def dias_restantes(self):
        """Días que quedan hasta el vencimiento"""
        if self.end_date:
            return (self.end_date - timezone.localdate()).days
        return None
    
    @property
    def dias_totales(self):
        """Días totales del período"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    @property
    def dias_transcurridos(self):
        """Días transcurridos desde el inicio"""
        if self.start_date:
            return (timezone.localdate() - self.start_date).days
        return None
    
    @property
    def porcentaje_transcurrido(self):
        """Porcentaje del período que ya pasó"""
        if self.dias_totales and self.dias_transcurridos is not None:
            return min(100, max(0, int((self.dias_transcurridos / self.dias_totales) * 100)))
        return None
    
    def __str__(self):
        return f"Membership {self.user.username}: {self.status}"