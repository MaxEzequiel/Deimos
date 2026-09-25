from django.db import models


class Publication(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to="publications/")

    def __str__(self):
        return self.title
