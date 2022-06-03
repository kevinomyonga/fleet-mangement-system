from rest_framework import serializers
from appointments.models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Appointment
        exclude = ['created_at']
