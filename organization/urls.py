from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>',login_required(views.ItemView.as_view()), name='detail'),
    path('start', login_required(views.RedirectView.as_view()), name='index'),
    path('create', login_required(views.CreateView.as_view()), name='create'),
    path('join/<str:token>', views.OrganizationJoinView.as_view(), name='join'),
    path('add/user', login_required(views.OrganizationAddUserView.as_view()), name='add-user'),
    path('add/sms_gateway', login_required(views.OrganizationAddSmsGateway.as_view()), name='add_sms_gateway'),
    path('verify_sms_settings', login_required(views.VerifySmsSettings.as_view()), name='verify_sms_settings'),
    path('add/m_details', login_required(views.OrganizationAddMpesaDetails.as_view()), name='add-m-details'),
    path('switch/<int:organization_user_id>',login_required(views.SwitchView.as_view()), name='switch'),
    path('remove/user/<int:organization_user_id>',login_required(views.OrganizationRemoveUserIframeView.as_view()), name='remove-user'),
    path('stkpush_callback', views.STKPushCallback.as_view(), name='stkpush_callback'),
    path('kopokopo_callback', views.KopokopoCallback.as_view(), name='kopokopo_callback'),
]
