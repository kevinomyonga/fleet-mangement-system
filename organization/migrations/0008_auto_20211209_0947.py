# Generated by Django 3.1.5 on 2021-12-09 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0007_auto_20211208_0636'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganisationSmsProvider',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.PositiveSmallIntegerField(choices=[(1, "Africa's talking"), (2, 'Infobip'), (3, 'Vonage'), (4, 'Twilio'), (5, 'Vaspro')], default=None, max_length=50)),
                ('sender_id', models.CharField(max_length=150)),
                ('api_key', models.CharField(blank=True, max_length=200, null=True)),
                ('username', models.CharField(blank=True, max_length=150, null=True)),
                ('base_url', models.URLField(blank=True, null=True)),
                ('api_secret', models.CharField(blank=True, max_length=200, null=True)),
                ('account_sid', models.CharField(blank=True, max_length=200, null=True)),
                ('auth_token', models.CharField(blank=True, max_length=200, null=True)),
                ('verification_code', models.CharField(blank=True, max_length=6, null=True)),
                ('verified', models.BooleanField(default=False)),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='organization.organization')),
            ],
        ),
        migrations.DeleteModel(
            name='OrganizationMpesaDetails',
        ),
    ]
