from django.db import models
from django.conf import settings

# ordenar los modelos en base su logica
class Day(models.Model):
    name = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Routine(models.Model):
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.description


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

    def __str__(self):
        return f"{self.routine} - {self.exercise} ({self.day})"


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
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.surname} ({self.user.username})"

