# Generated by Django 5.0.2 on 2024-11-05 04:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0020_challengerecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='carbon_emission',
            field=models.IntegerField(default=0),
        ),
    ]
