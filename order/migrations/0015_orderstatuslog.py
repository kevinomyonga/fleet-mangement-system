# Generated by Django 3.1.5 on 2022-02-24 11:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0014_auto_20220217_1236'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderStatusLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(max_length=50)),
                ('order_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_status_logs', to='order.order')),
            ],
            options={
                'verbose_name': 'OrderStatusLog',
                'verbose_name_plural': 'OrderStatusLogs',
            },
        ),
    ]
