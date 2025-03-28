from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
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
    carbon_emission = models.IntegerField(default=0)


class Position(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=20, decimal_places=10)
    longitude = models.DecimalField(max_digits=20, decimal_places=10)
    date_time = models.DateTimeField(null=True)
    speed = models.FloatField(default=0)
    distance = models.FloatField(default=0)


class AthleteCoachRelation(models.Model):
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, related_name='athletes')
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaches')
    rate = models.IntegerField(null=True)

    class Meta:
        unique_together = ('athlete', 'coach')


class ChallengeRecord(models.Model):
    CHALLENGE_CHOICES = [
        ('RUN_10', 'Сделай 10 Забегов!'),
        ('RUN_50', 'Пробеги 50 километров!'),
        ('RUN_2_10', '2 километра за 10 минут!')
    ]

    athlete = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges')
    name = models.CharField(max_length=255, choices=CHALLENGE_CHOICES, default='')

    class Meta:
        unique_together = ('athlete', 'name')


class AthleteInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    weight = models.IntegerField(null=True, validators=[MinValueValidator(30), MaxValueValidator(200)])
    goals = models.CharField(max_length=200, default='')
    test_field = models.CharField(max_length=255, default='')


class CollectableItem(models.Model):
    users = models.ManyToManyField(User, related_name='collectable_items')
    name = models.CharField(max_length=255)
    uid = models.CharField(max_length=50)
    value = models.IntegerField()
    latitude = models.DecimalField(max_digits=20, decimal_places=10)
    longitude = models.DecimalField(max_digits=20, decimal_places=10)
    picture = models.CharField(max_length=255, default='')
