# Generated by Django 3.1.5 on 2022-02-25 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0015_orderstatuslog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='state',
            field=models.PositiveIntegerField(choices=[(2, 'Not collected'), (1, 'Collected for delivery'), (3, 'Damaged in transit'), (4, 'Rejected by recipeint'), (5, 'Failed'), (6, 'Delivered'), (7, 'Returned to warehouse')], default=2),
        ),
    ]