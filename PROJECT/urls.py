"""PROJECT URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse_lazy
from django.views.generic.base import RedirectView
from organization.views import DashboardView
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_required(DashboardView.as_view()), name='dashboard'),
	path('order/', include(('order.urls', 'order'), namespace='order')),
	path('route/', include(('route.urls', 'route'), namespace='route')),
	path('driver/', include(('driver.urls', 'driver'), namespace='driver')),
	path('vehicle/', include(('vehicle.urls', 'order'), namespace='vehicle')),
	path('accounts/', include(('user.urls', 'accounts'), namespace='accounts')),
	path('organizations/', include(('organization.urls', 'organization'), namespace='organization')),

    path('api/v1/', include('api.urls')),
    #path('', RedirectView.as_view(url=reverse_lazy('organizations:index')), name='home'),
]
