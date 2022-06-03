from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('json', login_required(views.JsonView.as_view()), name='json'),
    path('create-json', login_required(views.CreateJsonView.as_view()), name='create-json'),
]

