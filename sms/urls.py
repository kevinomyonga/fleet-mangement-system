from django.urls import path
from . import views

app_name = 'sms' 

urlpatterns = [
    path('send/', views.SendSms.as_view(), name='send'),
]

