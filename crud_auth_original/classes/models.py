from django.db import models
from people.models import Person
from django.core.validators import MinLengthValidator,EmailValidator
# Create your models here.
class Course(models.Model):
    name = models.CharField(max_length= 50, validators=[MinLengthValidator(5)])
    description = models.CharField(default="sin descripcion", validators=[MinLengthValidator(5)], max_length= 100)
    teacher = models.ForeignKey(Person, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

class inscription(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    participant = models.ForeignKey(Person, on_delete=models.CASCADE)
    