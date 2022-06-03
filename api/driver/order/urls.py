from django.urls import path, include
from . import views

urlpatterns = [
	path('<int:pk>', views.IndexView.as_view()),
	path('routes', views.RouteView.as_view()),
	path('filter', views.FilterView.as_view()),
	path('stats', views.DriverStatsView.as_view()),
    path('self_assign', views.SelfAssignView.as_view()),
    path('filter_assign', views.FilterAssignView.as_view()),
    path('start', views.StartOrderView.as_view()),
    path('accept', views.AcceptOrderView.as_view()),
    path('<int:pk>/fail', views.FailedOrderView.as_view()),
    path('<int:pk>/arrived', views.ArrivedOrderView.as_view()),
    path('<int:pk>/complete', views.CompleteOrderView.as_view()),
    path('<int:pk>/change-payment-method', views.ChangePayView.as_view()),
    path('send_stkpush', views.SendSTKPush.as_view()),
    # View previous orders
    path('history', views.OrderHistory.as_view()),
]
