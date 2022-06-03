from channels.routing import ProtocolTypeRouter, URLRouter
from .consumer import AsyncOrdersConsumer
from django.urls import path

websockets = URLRouter([
    path(
        "ws/orders/<int:organisation_id>/<int:user_id>", AsyncOrdersConsumer,
        name="orders",
    ),
])
