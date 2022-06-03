from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('', login_required(views.IndexView.as_view()), name='index'),
    path('json', login_required(views.DriversJsonView.as_view()), name='json'),
    path('create', login_required(views.CreateView.as_view()), name='create'),
    path('<int:pk>', login_required(views.DriverView.as_view()), name='index'),
    path('<int:pk>/edit', login_required(views.EditView.as_view()), name='edit'),
    path('<int:pk>/delete', login_required(views.DriverDeleteView.as_view()), name='delete'),
    path('track/iframe', login_required(views.DriverTrackingIframeView.as_view()), name='track'),
    path('orders/iframe', login_required(views.DriverOrdersIframeView.as_view()), name='orders'),
]

