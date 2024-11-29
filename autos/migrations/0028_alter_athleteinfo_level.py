# Generated by Django 5.0.2 on 2024-11-29 00:11

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0027_alter_athleteinfo_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athleteinfo',
            name='level',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
        ),
    ]
