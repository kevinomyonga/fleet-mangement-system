from django.shortcuts import render
from rest_framework import viewsets
from .serializers import DriversSerializer, OrganizationSerializer

# Create your views here.
class DriversViewSet(viewsets.ModelViewSet):
    queryset = Drivers.objects.order_by("-created_at")
    serializer_class = DriversSerializer
    permission_classes = []
    authentication_classes = []
