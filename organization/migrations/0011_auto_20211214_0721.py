# Generated by Django 3.1.5 on 2021-12-14 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0010_organizationsmsprovider'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmpesadetails',
            name='client_id',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='organizationmpesadetails',
            name='client_secret',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='organizationmpesadetails',
            name='implementation',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Daraja'), (2, 'Kopokopo')], default=None),
        ),
        migrations.AddField(
            model_name='organizationmpesadetails',
            name='till_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='organizationmpesadetails',
            name='business_short_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='organizationmpesadetails',
            name='consumer_key',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='organizationmpesadetails',
            name='consumer_secret',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='organizationmpesadetails',
            name='pass_key',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='organizationsmsprovider',
            name='provider',
            field=models.PositiveSmallIntegerField(choices=[(1, "Africa's talking"), (2, 'Infobip'), (3, 'Vonage'), (4, 'Twilio'), (5, 'Vaspro')], default=None),
        ),
    ]
