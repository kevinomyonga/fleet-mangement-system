from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('json', login_required(views.VehicleJsonView.as_view()), name='json'),
    path('create-iframe', login_required(views.CreateView.as_view()), name='create-iframe'),
]

