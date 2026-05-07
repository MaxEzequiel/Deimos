from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator, EmailValidator, MinValueValidator, MaxValueValidator
# Create your models here.



class Person(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey("plans.Plan", on_delete=models.SET_NULL, null=True, blank=True)
    id_number = models.IntegerField(
        validators=[
            MinValueValidator(100000, "el dni debe tener al menos 6 digitos, ingrese un dni valido"),
            MaxValueValidator(9999999999, "el dni debe tener un maximo de 10 digitos, ingrese un numero valido")
        ])
    name = models.CharField(
        validators=[MinLengthValidator(2, "el nombre debe tener almenos 2 caracteres"),
        MaxLengthValidator(40, "el nombre no debe superar los 40 caracteres")])
    surname = models.CharField(
        validators=[MinLengthValidator(2, "el apellido debe tener almenos 2 caracteres"),
        MaxLengthValidator(40, "el apellido no debe superar los 40 caracteres")])
    birth_date = models.DateField(null=True, blank=True)

    GENDER_CHOICES = [("Femenino", "Femenino"), ("Masculino", "Masculino"), ("Otro", "Otro")]
    gender = models.CharField(choices=GENDER_CHOICES, verbose_name="genero",max_length=10, blank=True)
    phone_number = models.CharField(validators=[MinLengthValidator(8, "el numero de telefono debe tener al menos 8 caracteres"), MaxLengthValidator(20, "el numero de telefono no debe superar los 20 caracteres")], blank=True)
    email = models.EmailField(validators=[EmailValidator("el email no es valido")], blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.surname} ({self.user.username})"