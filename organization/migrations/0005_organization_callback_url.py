# Generated by Django 3.1.5 on 2021-05-13 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_organization_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='callback_url',
            field=models.URLField(max_length=2048, null=True),
        ),
    ]
