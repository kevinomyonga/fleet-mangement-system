# Generated by Django 3.1.5 on 2021-12-08 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0005_auto_20210929_1142'),
    ]

    operations = [
        migrations.CreateModel(
            name='STKPushRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('MerchantRequestID', models.CharField(max_length=50)),
                ('CheckoutRequestID', models.CharField(max_length=50)),
                ('ResponseCode', models.IntegerField()),
                ('ResponseDescription', models.CharField(max_length=150)),
                ('CustomerMessage', models.CharField(max_length=150)),
                ('AccountReference', models.CharField(max_length=150)),
                ('TransactionDesc', models.CharField(max_length=150)),
                ('PhoneNumber', models.CharField(max_length=150)),
                ('TransactionDate', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='Amount',
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='CheckoutRequestID',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='MerchantRequestID',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='MpesaReceiptNumber',
            field=models.CharField(blank=True, default='', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='PhoneNumber',
            field=models.CharField(blank=True, default='', max_length=13, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='ResultCode',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='ResultDesc',
            field=models.CharField(blank=True, default='', max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='TransactionDate',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
