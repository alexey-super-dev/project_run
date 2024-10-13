from django.contrib.auth.models import User
from django.db import models


class Autos(models.Model):
    name = models.CharField(max_length=100)


class Run(models.Model):
    comment = models.CharField(max_length=250)
    athlete = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=50, default='init')
    distance = models.FloatField(null=True)
    run_time_seconds = models.IntegerField(null=True)
    speed = models.FloatField(default=0)


class Position(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=20, decimal_places=10)
    longitude = models.DecimalField(max_digits=20, decimal_places=10)
    date_time = models.DateTimeField(null=True)
    speed = models.FloatField(default=0)
    distance = models.FloatField(default=0)
