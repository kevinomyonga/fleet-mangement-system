from django.urls import path, include
from django.conf.urls import url
from . import views

urlpatterns = [
	path('auth', views.AuthView.as_view()),
	path('profile', views.ProfileView.as_view()),
	path('passwd', views.PasswordSetView.as_view()),
	path('phone/code', views.PhoneCodeView.as_view()),
    path('fcm/update', views.FCMUpdateView.as_view()),
	path('phone/verify', views.PhoneVerifyView.as_view()),
    path('location/update', views.LocationView.as_view()),
	path('profile/update', views.ProfileUpdateView.as_view()),

    path('order/', include('api.driver.order.urls')),
    path('route/', include('api.driver.route.urls')),
]
