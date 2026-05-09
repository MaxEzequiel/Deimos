from django.db import models
from people.models import Person
from django.core.validators import MinLengthValidator,MaxLengthValidator
# Create your models here.
class Course(models.Model):
    name = models.CharField(max_length= 50, 
        validators=[MinLengthValidator(5,"El nombre de la clase debe tener almenos 3 caracteres"),
        MaxLengthValidator(30,"el nombre de la clase no debe superar los 30 caracteres")])
    description = models.CharField(default="sin descripcion", 
        validators=[MinLengthValidator(5, "la descripcion debe tener al menos 5 caracteres"),
        MaxLengthValidator(150, "la descripcion debe tener como maximo 150 caracteres")])
    teacher = models.ForeignKey(Person, on_delete=models.CASCADE,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()


class inscription(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    participant = models.ForeignKey(Person, on_delete=models.CASCADE)
    