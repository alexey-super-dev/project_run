# Generated by Django 5.0.2 on 2024-09-16 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0004_rename_runner_run_athlete'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='status',
            field=models.CharField(default='ok', max_length=50),
        ),
    ]
