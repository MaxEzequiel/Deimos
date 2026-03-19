from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
# Create your models here.


class Plan(models.Model):
    nombre = models.CharField(max_length=60,blank=True,null=True)
    descripcion = models.CharField(max_length=60,blank=True,null=True)
    precio_base = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return f"{Plan.nombre}"

class Ejercicio(models.Model):
    nombre=models.CharField(max_length=40)
    descripcion=models.CharField(max_length=100)

class Dia(models.Model):
    nombre = models.CharField(max_length=15)

class Rutina(models.Model):
    descripcion = models.CharField(max_length=200)


# tabla intermedia entre rutina > ejercicio,dias (ManyToMany)
class RutinaEjercicioDia(models.Model):
    rutina = models.ForeignKey(Rutina,on_delete=models.CASCADE,related_name="ejercicios_dias")
    dias = models.ForeignKey(Dia,on_delete=models.CASCADE)
    ejercicios = models.ForeignKey(Ejercicio,on_delete=models.CASCADE)
    repeticiones = models.IntegerField(null=True,blank=True)
    sets = models.IntegerField(null=True,blank=True)
    fallo = models.CharField(max_length=7, default="No")



#perfil de la persona relacionada a un user unico (tabla auth_user)
class Persona(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    id_plan = models.ForeignKey(Plan,on_delete=models.CASCADE, null=True, blank=True)
    dni = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=10)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=200,blank=True,null=True)
    rutina = models.ForeignKey(Rutina,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.surname} ({self.user.username})"

# modelo de membresia 
class Membresia(models.Model):
    id_cliente = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    estado = models.CharField(max_length=12, default="inactivo")
    id_plan = models.ForeignKey(Plan,on_delete=models.CASCADE,blank=True , null=True)


