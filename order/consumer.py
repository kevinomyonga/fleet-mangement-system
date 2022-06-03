from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser
from organization.models import OrganizationUser
from channels.exceptions import DenyConnection
from asgiref.sync import async_to_sync
import json

CHANNEL_NAME = "orders"
class AsyncOrdersConsumer(WebsocketConsumer):

	def connect(self):
		self.organisation_id = self.scope['url_route']['kwargs']['organisation_id']
		self.user_id = self.scope['url_route']['kwargs']['user_id']
		self.room_group_name = f'orders_{self.organisation_id}'
		print(self.room_group_name)
		async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
		self.accept()

	def disconnect(self, close_code):
		async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

	def order_created(self, event):
		print("New order")
		self.send(text_data=json.dumps({'action' : 'order_created', 'order_id' : event['message'] }))

	def order_updated(self, event):
		print("Order updated")
		self.send(text_data=json.dumps({'action' : 'order_updated', 'order_id' : event['message'] }))

