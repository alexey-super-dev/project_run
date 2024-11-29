# Generated by Django 5.0.2 on 2024-11-29 01:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0029_alter_athleteinfo_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athleteinfo',
            name='level',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
            preserve_default=False,
        ),
    ]
