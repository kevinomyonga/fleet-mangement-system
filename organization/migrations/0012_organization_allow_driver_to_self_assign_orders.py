# Generated by Django 3.1.5 on 2021-12-15 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0011_auto_20211214_0721'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='allow_driver_to_self_assign_orders',
            field=models.BooleanField(default=False),
        ),
    ]
