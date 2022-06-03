from channels.routing import ProtocolTypeRouter, URLRouter
from order.routing import websockets

application = ProtocolTypeRouter({
    "websocket": websockets,
})
