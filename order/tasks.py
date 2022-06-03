from django.core import serializers
import validators, requests, json
from celery import shared_task


@shared_task
def ping_callback(order_id):
	from .models import Order
	try:
		order = Order.objects.get(pk=order_id)
	except Order.DoesNotExist:
		return

	callback_url = order.organization.callback_url
	if not validators.truthy(callback_url) or not validators.url(callback_url):
		return

	headers = {'Content-Type' : 'application/json', 'user-agent' : 'GetbodaApi/1.0' }
	try:
		requests.post(callback_url, headers=headers, data=json.dumps(order.to_dict()), verify=False, timeout=12)
	except Exception as e:
		print(e)


@shared_task()
def replicate_order(order_pk):
	from .models import Order
	try:
		order = Order.objects.get(pk=order_pk)
	except Order.DoesNotExist:
		return

	sync_callback_url = order.organization.sync_callback_url
	if not validators.truthy(sync_callback_url) or not validators.url(sync_callback_url):
		return

	order_json = json.loads(serializers.serialize('json', [order]))[0]
	faliures_json = json.loads(serializers.serialize('json', order.failures.all() ))
	order_items_json = json.loads(serializers.serialize('json', order.items.all() ))

	rider_json = None
	if order.rider:
		rider_json = json.loads(serializers.serialize('json', [order.rider] ))[0]

	payload = {
		"order" : order_json,
		"rider" : rider_json,
		"failures" : faliures_json,
		"order_items" : order_items_json,
	}
	token = 'a21e3d5e5f2f24e0c79bd291d8f44ab996f634a7'
	#endpoint = 'http://10.114.0.8:8080/api/v1/order/replicate?organization_id=1'
	HEADERS = {'Content-Type' : 'application/json', 'Authorization' : f'Token {token}' }
	requests.post(sync_callback_url, headers=HEADERS, data=json.dumps(payload), verify=False, timeout=12)
