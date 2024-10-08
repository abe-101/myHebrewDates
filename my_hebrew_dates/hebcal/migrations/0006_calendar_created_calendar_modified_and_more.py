# Generated by Django 5.0.9 on 2024-09-16 12:38

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hebcal", "0005_alter_calendar_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="calendar",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="calendar",
            name="modified",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="hebrewdate",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="hebrewdate",
            name="modified",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
