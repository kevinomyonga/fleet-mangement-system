# Generated by Django 3.1.5 on 2021-12-09 09:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0006_auto_20211208_0636'),
    ]

    operations = [
        migrations.DeleteModel(
            name='STKPushRequest',
        ),
        migrations.RemoveField(
            model_name='order',
            name='Amount',
        ),
        migrations.RemoveField(
            model_name='order',
            name='CheckoutRequestID',
        ),
        migrations.RemoveField(
            model_name='order',
            name='MerchantRequestID',
        ),
        migrations.RemoveField(
            model_name='order',
            name='MpesaReceiptNumber',
        ),
        migrations.RemoveField(
            model_name='order',
            name='PhoneNumber',
        ),
        migrations.RemoveField(
            model_name='order',
            name='ResultCode',
        ),
        migrations.RemoveField(
            model_name='order',
            name='ResultDesc',
        ),
        migrations.RemoveField(
            model_name='order',
            name='TransactionDate',
        ),
    ]
