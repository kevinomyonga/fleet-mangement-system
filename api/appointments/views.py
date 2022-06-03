from datetime import time, datetime, timedelta

from django.utils import timezone

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import AppointmentSerializer
from appointments.models import Appointment

class AvailableSlots(APIView):

    authentication_classes = []

    permission_classes = []

    def get(self, request):
        # if the date was not passed set it to current date
        if request.GET.get('date'):
            date_gte = datetime.strptime(request.GET.get('date'), '%d-%m-%Y').date()
        else:
            date_gte = datetime.now().date()

        opening_time = time(8)
        opening_date_time = timezone.make_aware(datetime.combine(date_gte, opening_time))

        closing_time = time(17)
        closing_date_time = timezone.make_aware(datetime.combine(date_gte, closing_time))

        current_date_time = opening_date_time
        
        # available slots
        slots = []
        while current_date_time>=opening_date_time and current_date_time<closing_date_time and (
                    ((closing_date_time - opening_date_time).total_seconds() / 3600) >= 1):
            
            booked = Appointment.objects.filter(appointment_date=current_date_time).exists()

            # check if the slot is available 
            if not booked and current_date_time >= timezone.localtime(timezone.now()):
                end_time = current_date_time + timedelta(hours=1)
                slots.append(current_date_time.strftime("%H:%M") + ' - ' + end_time.strftime("%H:%M"))

                current_date_time = current_date_time + timedelta(hours=1)
            else:
                current_date_time = current_date_time + timedelta(hours=1)

        return Response({"available_slots": slots})


class AppointmentsViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.order_by('-created_at')
    serializer_class = AppointmentSerializer
    permission_classes = []
    authentication_classes = []
