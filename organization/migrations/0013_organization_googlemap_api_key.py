# Generated by Django 3.1.5 on 2021-12-17 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0012_organization_allow_driver_to_self_assign_orders'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='googlemap_api_key',
            field=models.CharField(max_length=255, null=True),
        ),
    ]