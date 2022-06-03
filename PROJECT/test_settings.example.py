from .settings import DATABASES, SECRET_KEY, INSTALLED_APPS


SECRET_KEY = SECRET_KEY


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

INSTALLED_APPS = INSTALLED_APPS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'your-db',
        'USER': 'your-user',
        'PASSWORD': 'your-pass',
        'HOST': 'localhost',
        'PORT': '',
    }
}


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"