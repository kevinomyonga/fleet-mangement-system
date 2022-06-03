# Generated by Django 3.1.5 on 2022-02-26 00:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('route', '0002_auto_20220225_1659'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(1, ' Not Started'), (2, 'Started'), (3, 'Completed'), (4, 'Failed')], default=1),
        ),
    ]
