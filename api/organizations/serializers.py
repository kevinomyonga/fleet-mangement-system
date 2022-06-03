from rest_framework import serializers
from organizations.models import Driver, Organization


class DriversSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        exclude = ["created_at"]
