from django.urls import path, include
from . import views

urlpatterns = [
	path('', views.FilterView.as_view()),
    path('by-ref', views.RefView.as_view()),
	path('sync', views.SyncOrderView.as_view()),
	path('replicate', views.ReplicateOrderView.as_view()),

	path('create', views.CreateView.as_view()),
    path('<int:pk>', views.IndexView.as_view()),
    path('<int:pk>/cancel', views.CancelView.as_view()),
]
