from django.db import models
from people.models import Person
from django.core.validators import MinLengthValidator,MaxLengthValidator
from django.core.exceptions import ValidationError
from datetime import timedelta
# Create your models here. 

class Course(models.Model):
    name = models.CharField(max_length= 50, 
        validators=[MinLengthValidator(5,"El nombre de la clase debe tener almenos 5 caracteres"),
        MaxLengthValidator(30,"el nombre de la clase no debe superar los 30 caracteres")])
    description = models.CharField(default="sin descripcion", 
        validators=[MinLengthValidator(5, "la descripcion debe tener al menos 5 caracteres"),
        MaxLengthValidator(150, "la descripcion debe tener como maximo 150 caracteres")])
    teacher = models.ForeignKey(Person, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    
    
    def clean(self):
        if self.starts_at and self.ends_at:
            # Validación 1: ends_at > starts_at
            if self.ends_at <= self.starts_at:
                raise ValidationError({
                    'ends_at': 'La fecha de finalización debe ser mayor a la fecha de inicio.'
                })
            
            # Validación 2: Duración máxima de 5 horas
            duracion = self.ends_at - self.starts_at
            if duracion > timedelta(hours=5):
                raise ValidationError({
                    'ends_at': f'La duración máxima permitida es de 5 horas. La duración ingresada es de {duracion}.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Inscription(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    participant = models.ForeignKey(Person, on_delete=models.CASCADE)
    