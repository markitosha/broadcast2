# Generated by Django 3.1.5 on 2021-01-24 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_device'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='sid',
            field=models.CharField(default='qwe', max_length=128, verbose_name='sid'),
        ),
    ]