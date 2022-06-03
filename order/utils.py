from django.utils import timezone
import base64, validators, re, pandas
from . import models

def complete_order(order):
	order.state = models.Order.DELIVERED
	order.datetime_completed = timezone.now()
	order.public_id = base64.b64encode(bytes(str(order.pk), 'ascii')).decode().strip("=")
	order.save()

def failed_order(order):
	order.state = models.Order.FAILED
	order.datetime_failed = timezone.now()
	order.public_id = base64.b64encode(bytes(str(order.pk), 'ascii')).decode().strip("=")
	order.save()

def driver_assigned_order(order):
	order.state = models.Order.SUBMITTED_PENDING_FOWARD_DELIVERY
	order.datetime_assigned = timezone.now()
	order.save()


def csv_header_to_slug(header_name):
	if not validators.truthy(header_name):
		return None
	header_name = str(header_name).lower()
	header_name = re.sub(r'\W+', '', header_name)
	return header_name.replace("a", "").replace("e", "").replace("i", "").replace("o", "").replace("u", "")

def process_cell(doc, x, y):
	value = doc.iloc[x, y]
	if pandas.isnull(value) or not validators.truthy(value):
		return None
	return str(value)
