# Generated by Django 5.0.2 on 2024-11-14 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0021_run_carbon_emission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challengerecord',
            name='name',
            field=models.CharField(choices=[('RUN_10', 'Сделай 10 Забегов!'), ('RUN_50', 'Пробеги 50 километров!')], default='', max_length=255),
        ),
    ]
