from django.urls import path, include
from . import views

urlpatterns = [
	path('profile', views.ProfileView.as_view()),
	path('organizations', views.OrganizationsView.as_view()),
]

