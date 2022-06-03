# Generated by Django 3.1.5 on 2021-11-17 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('job_title', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('company', models.CharField(max_length=150)),
                ('phone_number', models.CharField(max_length=10)),
                ('number_of_orders', models.CharField(max_length=100)),
                ('interest', models.CharField(max_length=150)),
                ('message', models.TextField()),
                ('appointment_date', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]