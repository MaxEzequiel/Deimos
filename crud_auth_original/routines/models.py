from django.db import models
from django.conf import settings
# Create your models here.

class Day(models.Model):
    name = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Routine(models.Model):
    # Una rutina está asociada a un cliente (Person) 1:1, para facilitar un solo plan por usuario
    client = models.OneToOneField(
        "people.Person",
        on_delete=models.CASCADE,
        related_name="routine",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100, help_text="Nombre de la rutina, p.ej. Fuerza pierna")
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.client or 'Sin cliente'}"


class Exercise(models.Model):
    name = models.CharField(max_length=40)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class RoutineExerciseDay(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name="routine_exercises")
    day = models.ForeignKey(Day, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    repetitions = models.IntegerField(null=True, blank=True)
    sets = models.IntegerField(null=True, blank=True)
    failure = models.CharField(max_length=7, default="No")

    class Meta:
        # evita duplicados de estos campos que sean iguales en los 3 datos. Atomicidad : D (creo)
        unique_together = ("routine", "day", "exercise")

    def __str__(self):
        return f"{self.routine} - {self.exercise} ({self.day})"