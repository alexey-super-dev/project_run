from django.db import models


class Autos(models.Model):
    name = models.CharField(max_length=100)
