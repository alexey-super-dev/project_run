# Generated by Django 5.1.3 on 2024-12-03 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0031_alter_athleteinfo_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='athleteinfo',
            name='test_field',
            field=models.CharField(default='', max_length=255),
        ),
    ]
