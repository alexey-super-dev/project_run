# Generated by Django 5.0.2 on 2024-10-13 00:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0011_position_speed'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='distance',
            field=models.FloatField(default=0),
        ),
    ]
