# Generated by Django 4.2.7 on 2024-01-16 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_doorlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='doorlog',
            name='response',
            field=models.CharField(max_length=500, null=True),
        ),
    ]