# Generated by Django 5.1.3 on 2024-12-05 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0034_collectableitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectableitem',
            name='uid',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
    ]
