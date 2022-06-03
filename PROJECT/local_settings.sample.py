import firebase_admin
from firebase_admin import credentials

from .settings import BASE_DIR, SECRET_KEY
import os, africastalking

#STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'your-db',
        'USER': 'your-user',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [("localhost", 6379)],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    },
}

# celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'


SENDGRID_API_KEY = ''
DEFAULT_FROM_EMAIL = ""


DEFAULT_AFRICASTALKING_SENDER_ID = ''
DEFAULT_AFRICASTALKING_USERNAME = ''
DEFAULT_AFRICASTALKING_API_KEY = ''


cred = credentials.Certificate("")
firebase_admin.initialize_app(cred)

africastalking.initialize(DEFAULT_AFRICASTALKING_USERNAME, DEFAULT_AFRICASTALKING_API_KEY)


WS_CONNECT_URL = 'ws://127.0.0.1:8000/ws/orders'
TEMPLATE_HOST_URL = 'http://127.0.0.1:8000'
MPESA_AUTH_URL = ""
MPESA_ONLINE_PAYMENT_URL = ""
MPESA_ORDER_CALLBACK_URL = ""


#DEBUG = False
#ALLOWED_HOSTS = ['*']
