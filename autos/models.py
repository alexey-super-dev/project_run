from django.contrib.auth.models import User
from django.db import models


class Autos(models.Model):
    name = models.CharField(max_length=100)


class Run(models.Model):
    comment = models.CharField(max_length=250)
    athlete = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=50, default='init')
