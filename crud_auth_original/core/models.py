from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=10)
    detail = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    modify_date = models.DateTimeField(auto_now_add=True)