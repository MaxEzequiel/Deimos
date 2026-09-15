from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    ACTION_CHOICES = (("CREATE", "Creación"), ("UPDATE", "Actualización"), ("DELETE", "Eliminación"))

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=120)
    object_id = models.CharField(max_length=64, blank=True)
    path = models.CharField(max_length=255)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "evento de auditoría"
        verbose_name_plural = "eventos de auditoría"

    def __str__(self):
        return f"{self.action} {self.resource} — {self.created_at:%Y-%m-%d %H:%M}"
