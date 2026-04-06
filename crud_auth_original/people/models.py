from django.db import models
from django.conf import settings
# Create your models here.
class Person(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey("plans.Plan", on_delete=models.SET_NULL, null=True, blank=True)
    id_number = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=50)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.surname} ({self.user.username})"