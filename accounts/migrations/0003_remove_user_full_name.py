# Generated by Django 5.0.6 on 2024-07-21 13:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_auto_20240721_1724"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="full_name",
        ),
    ]
