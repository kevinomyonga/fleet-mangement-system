import requests
from requests.auth import HTTPBasicAuth
from base64 import b64encode

from datetime import datetime

from django.conf import settings


from order.models import STKPushRequest

auth_URL = settings.MPESA_AUTH_URL
onlinePayment_URL = settings.MPESA_ONLINE_PAYMENT_URL
callback_url = settings.MPESA_ORDER_CALLBACK_URL

def getToken(consumer_key, consumer_secret):

    r = requests.get(auth_URL, auth=HTTPBasicAuth(
        consumer_key, consumer_secret))

    json_response = r.json()
    access_token = json_response.get('access_token')
    return access_token

def getTimestamp():
    unformatted_time = datetime.now()
    formatetted_time = unformatted_time.strftime("%Y%m%d%H%M%S")
    return formatetted_time

def getTime(unformatted_time):
    transation_time = str(unformatted_time)
    print('=====================unformated time=======================')
    print(unformatted_time)
    transation_date_time = datetime.strptime(
        transation_time, '%Y%m%d%H%M%S')
    print('=====================formated time=======================')
    print(transation_date_time)
    return transation_date_time

def getPassword(business_short_code, passkey):
    timestamp = getTimestamp()
    data = f'{business_short_code}{passkey}{timestamp}'
    encoded_string = b64encode(data.encode())
    decoded_string = encoded_string.decode('utf-8')
    return decoded_string

   
def save_stkpush_request(response_data, phone_number, account_reference, transaction_description):
    if "errorCode" in response_data.keys():
            return response_data
    else:
        data = {}
        data['MerchantRequestID'] = response_data['MerchantRequestID']
        data['CheckoutRequestID'] = response_data['CheckoutRequestID']
        data['ResponseCode'] = response_data['ResponseCode']
        data['ResponseDescription'] = response_data['ResponseDescription']
        data['CustomerMessage'] = response_data['CustomerMessage']
        data['PhoneNumber'] = phone_number
        data['AccountReference'] = account_reference
        data['TransactionDesc'] = transaction_description

        push_request = STKPushRequest.objects.create(
            **data
        )
        push_request.save()

        return response_data

def push_request(consumer_key, consumer_secret, passkey, business_short_code, amount, phone_number, account_reference='', transaction_description=''):
        
        password = getPassword(business_short_code, passkey)

        access_token = getToken(consumer_key, consumer_secret)

        timestamp = getTimestamp()


        headers = {"Authorization": "Bearer %s" % access_token}
        request = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": float(amount),
            "PartyA": str(phone_number),
            "PartyB": business_short_code,
            "PhoneNumber": str(phone_number),
            "CallBackURL": callback_url,
            "AccountReference": str(account_reference),
            "TransactionDesc": transaction_description
        }
        response = requests.post(
            onlinePayment_URL, json=request, headers=headers)
        response_data = response.json()

        if "errorCode" in response_data.keys():
            return response_data
        else:
            save_stkpush_request(response_data, phone_number, account_reference, transaction_description)
            return response_data