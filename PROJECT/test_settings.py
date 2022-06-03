import firebase_admin
from firebase_admin import credentials

from .settings import BASE_DIR, SECRET_KEY
import os, africastalking


SENDGRID_API_KEY = ''
DEFAULT_FROM_EMAIL = ""


DEFAULT_AFRICASTALKING_SENDER_ID = ''
DEFAULT_AFRICASTALKING_USERNAME = ''
DEFAULT_AFRICASTALKING_API_KEY = ''


#cred = credentials.Certificate("path/to/firebase.json")
#firebase_admin.initialize_app(cred)

africastalking.initialize(DEFAULT_AFRICASTALKING_USERNAME, DEFAULT_AFRICASTALKING_API_KEY)


WS_CONNECT_URL = 'ws://127.0.0.1:8000/ws/orders'
TEMPLATE_HOST_URL = 'http://127.0.0.1:8000'
MPESA_AUTH_URL = ""
MPESA_ONLINE_PAYMENT_URL = ""
MPESA_ORDER_CALLBACK_URL = ""


#DEBUG = False
#ALLOWED_HOSTS = ['*']
