from django.db import models
from django.conf import settings


class Membership(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=12, default="inactive")
    plan = models.ForeignKey("plans.Plan", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"Membership {self.user.username}: {self.status}"