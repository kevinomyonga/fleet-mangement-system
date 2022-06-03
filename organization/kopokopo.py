import k2connect
from django.conf import settings
import requests
import logging
logger = logging.getLogger(__name__)

def get_access_token(client_id, client_secret):
    url = settings.KOPOKOPO_BASE_URL

    # initialize
    k2connect.initialize(client_id, client_secret, url)

    # get auth
    token_service = k2connect.Tokens
    access_token_request = token_service.request_access_token()
    access_token = token_service.get_access_token(access_token_request)
    return access_token 

def push_stk_request(client_id, client_secret, amount, till_number, phone_number, order_id):
    callback_url = settings.KOPOKOPO_CALLBACK_URL
    payment_url = settings.KOPOKOPO_PAYMENT_URL
    access_token = get_access_token(client_id, client_secret)

    logger.debug(f'token {access_token}')
    phone_number = f'+{phone_number}'

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer %s" % access_token
    }

    payload = {
        "payment_channel" : "M-PESA STK Push",
        "till_number" : str(till_number),
        "subscriber": {
            "phone_number": phone_number,
        },
        "amount": {
            "currency": "KES",
            "value": str(amount)
        },
        "metadata":{
            "order_id": order_id
        },
        "_links" : {
            "callback_url": callback_url
        }
    }
    requests.post(
            payment_url, json=payload, headers=headers)

