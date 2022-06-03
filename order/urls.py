from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('track/<str:public_id>', views.ReviewView.as_view(), name='track'),
    path('review/<str:public_id>', views.ReviewView.as_view(), name='review'),

    path('', login_required(views.IndexView.as_view()), name='index'),
    path('map', login_required(views.MapView.as_view()), name='map'),
    path('plan', login_required(views.PlanView.as_view()), name='plan'),
    path('json', login_required(views.OrdersJsonView.as_view()), name='json'),
    path('create', login_required(views.CreateView.as_view()), name='create'),
    path('<int:pk>', login_required(views.OrderView.as_view()), name='detail'),
    path('reviews', login_required(views.ReviewsView.as_view()), name='reviews'),
    path('export', login_required(views.ExportOrdersView.as_view()), name='export'),
    path('payments', login_required(views.PaymentsView.as_view()), name='payments'),
    path('track', login_required(views.OrderTrackingIframeView.as_view()), name='track'),
    path('route/json', login_required(views.RouteJsonView.as_view()), name='route-json'),
    path('<int:pk>/partial', login_required(views.OrderPartialView.as_view()), name='detail-partial'),
    path('export/reviews', login_required(views.ExportReviewsView.as_view()), name='export-reviews'),
    path('upload/iframe', login_required(views.UploadOrdersIframeView.as_view()), name='upload-iframe'),
    path('state/<int:pk>/iframe', login_required(views.StateIframeView.as_view()), name='state-iframe'),
    path('assign/<int:pk>/iframe', login_required(views.AssignIframeView.as_view()), name='assign-iframe'),
    path('pickup/<int:pk>/iframe', login_required(views.PickupIframeView.as_view()), name='pickup-iframe'),
    path('dropoff/<int:pk>/iframe', login_required(views.DropoffIframeView.as_view()), name='dropoff-iframe'),
    path('multi-assign/iframe', login_required(views.MultiAssignIframeView.as_view()), name='multi-assign-iframe'),
    path('ajax-assign/iframe', login_required(views.AjaxAssignIframeView.as_view()), name='ajax-assign-iframe'),
    path('export/driver/reviews', login_required(views.ExportDriverReviewsView.as_view()), name='export-driver-reviews'),
    path('ajax-assign/iframe/<int:vehicle_id>/<int:route_id>', login_required(views.AjaxAssignIframeView.as_view()), name='ajax-assign-iframe'),
]







