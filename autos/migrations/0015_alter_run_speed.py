# Generated by Django 5.0.2 on 2024-10-13 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0014_run_speed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='speed',
            field=models.FloatField(default=0, null=True),
        ),
    ]
