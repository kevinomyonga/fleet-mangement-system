from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AppointmentsViewSet, AvailableSlots

router = DefaultRouter()
router.register('bookings', AppointmentsViewSet)

urlpatterns = [
     path('', include(router.urls)),
     path('availableslots/', AvailableSlots.as_view()),
]
