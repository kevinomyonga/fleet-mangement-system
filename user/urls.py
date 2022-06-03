from django.contrib.auth.decorators import login_required
from .utils import anonymous_required
from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('login/', anonymous_required(views.LoginView.as_view()), name='login'),
    path('verify', login_required(views.SendVerifyEmailView.as_view()), name='verify'),
    path('verify/<str:token>', views.VerifyEmailRedirectView.as_view(), name='verify'),
    path('register/', anonymous_required(views.RegisterView.as_view()), name='register'),
    path('developers/', login_required(views.DevelopersView.as_view()), name='developers'),
]

