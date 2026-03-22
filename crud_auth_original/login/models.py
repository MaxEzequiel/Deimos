from django.db import models
from django.conf import settings


class Dia(models.Model):
    nombre = models.CharField(max_length=15)

    def __str__(self):
        return self.nombre


class Rutina(models.Model):
    descripcion = models.CharField(max_length=200)

    def __str__(self):
        return self.descripcion


class Ejercicio(models.Model):
    nombre = models.CharField(max_length=40)
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class RutinaEjercicioDia(models.Model):
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name="ejercicios_dias")
    dias = models.ForeignKey(Dia, on_delete=models.CASCADE)
    ejercicios = models.ForeignKey(Ejercicio, on_delete=models.CASCADE)
    repeticiones = models.IntegerField(null=True, blank=True)
    sets = models.IntegerField(null=True, blank=True)
    fallo = models.CharField(max_length=7, default="No")

    def __str__(self):
        return f"{self.rutina} - {self.ejercicios} ({self.dias})"


class Persona(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    id_plan = models.ForeignKey("planes.Plan", on_delete=models.SET_NULL, null=True, blank=True)
    dni = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=10)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=200, blank=True, null=True)
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.usuario.username})"

