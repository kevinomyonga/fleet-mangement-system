from django.urls import path, include
from . import views

urlpatterns = [
	path('', views.RoutesView.as_view()),
	path('<int:pk>', views.RouteView.as_view()),
	path('<int:pk>/start', views.StartRouteView.as_view()),
]
