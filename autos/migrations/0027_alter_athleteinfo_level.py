# Generated by Django 5.0.2 on 2024-11-28 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0026_rename_comment_athleteinfo_goals'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athleteinfo',
            name='level',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
