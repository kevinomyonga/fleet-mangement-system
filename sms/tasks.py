from django.template import Context, Template
from sms.send_sms import send_sms
import validators, africastalking, base64
from django.urls import reverse_lazy
from django.conf import settings



def order_created_sms(order):
	if order is None or \
		not order.organization.send_order_received_sms or \
		not validators.truthy(order.organization.order_received_sms):
		return

	phone_number = order.dropoff_contact_phone_number
	if not validators.between(phone_number, 1000000000, 999999999999):
		return

	dropoff_name = order.dropoff_contact_name
	dropoff_name = dropoff_name.strip().split()[0].strip() if validators.truthy(dropoff_name) else ""
	order_ref = order.ref if validators.truthy(order.ref) else order.pk

	public_id = order.public_id
	if not validators.truthy(public_id):
		public_id = base64.b64encode(bytes(str(order.pk), 'utf-8')).decode().strip("=")
		order.public_id = public_id
		order.save()

	context = Context({"first_name": dropoff_name, 'order_ref' : order_ref})

	url = reverse_lazy("order:track", kwargs={'public_id' : public_id})
	txt = f'{order.organization.order_received_sms} .To track your order {settings.TEMPLATE_HOST_URL}{url}'
	template = Template(txt)
	message = template.render(context)

	organization = order.organization

	# send sms
	send_sms(organization, phone_number, message) # Use a queued task to send sms

def order_assign_sms(order):
	if order is None or \
		not order.organization.send_driver_assign_sms or \
		not validators.truthy(order.organization.driver_assign_sms) or \
		not validators.truthy(order.rider):
		return

	phone_number = order.dropoff_contact_phone_number
	if not validators.between(phone_number, 1000000000, 999999999999):
		return

	rider = order.rider
	rider_phone =  f'+{rider.phone_number}'
	rider_name = rider.full_names().strip().split()[0].strip()
	order_ref = order.ref if validators.truthy(order.ref) else order.pk

	public_id = order.public_id
	if not validators.truthy(public_id):
		public_id = base64.b64encode(bytes(str(order.pk), 'utf-8')).decode().strip("=")
		order.public_id = public_id
		order.save()

	url = reverse_lazy("order:track", kwargs={'public_id' : public_id})
	txt = f'{order.organization.driver_assign_sms} .To track your order {settings.TEMPLATE_HOST_URL}{url}'

	context = Context({"rider_name": rider_name, 'rider_phone' : rider_phone, 'order_ref' : order_ref})
	template = Template(txt)
	message = template.render(context)

	organization = order.organization

	# send sms
	send_sms(organization, phone_number, message)

def order_reassign_sms(order):
	if order is None or \
		not order.organization.send_driver_reassign_sms or \
		not validators.truthy(order.organization.driver_reassign_sms) or \
		not validators.truthy(order.rider):
		return


	phone_number = order.dropoff_contact_phone_number
	if not validators.between(phone_number, 1000000000, 999999999999):
		return

	rider = order.rider
	rider_phone =  f'+{rider.phone_number}'
	rider_name = rider.full_names().strip().split()[0].strip()
	order_ref = order.ref if validators.truthy(order.ref) else order.pk

	public_id = order.public_id
	if not validators.truthy(public_id):
		public_id = base64.b64encode(bytes(str(order.pk), 'utf-8')).decode().strip("=")
		order.public_id = public_id
		order.save()

	url = reverse_lazy("order:track", kwargs={'public_id' : public_id})
	txt = f'{order.organization.driver_reassign_sms} .To track your order {settings.TEMPLATE_HOST_URL}{url}'

	context = Context({"rider_name": rider_name, 'rider_phone' : rider_phone, 'order_ref' : order_ref})
	template = Template(txt)
	message = template.render(context)

	organization = order.organization

	# send sms
	send_sms(organization, phone_number, message)

def order_start_sms(order):
	if order is None or \
		not order.organization.send_driver_start_sms or \
		not validators.truthy(order.organization.driver_start_sms) or \
		not validators.truthy(order.rider):
		return

	phone_number = order.dropoff_contact_phone_number
	if not validators.between(phone_number, 1000000000, 999999999999):
		return

	rider = order.rider
	rider_phone =  f'+{rider.phone_number}'
	rider_name = rider.full_names().strip().split()[0].strip()
	order_ref = order.ref if validators.truthy(order.ref) else order.pk

	public_id = order.public_id
	if not validators.truthy(public_id):
		public_id = base64.b64encode(bytes(str(order.pk), 'utf-8')).decode().strip("=")
		order.public_id = public_id
		order.save()

	url = reverse_lazy("order:track", kwargs={'public_id' : public_id})
	txt = f'{order.organization.driver_start_sms} .To track your order {settings.TEMPLATE_HOST_URL}{url}'

	context = Context({"rider_name": rider_name, 'rider_phone' : rider_phone, 'order_ref' : order_ref})
	template = Template(txt)
	message = template.render(context)

	organization = order.organization

	# send sms
	send_sms(organization, phone_number, message)

def order_complete_sms(order):
	if order is None or \
		not order.organization.send_driver_complete_sms or \
		not validators.truthy(order.organization.driver_complete_sms) or \
		not validators.truthy(order.rider):
		return

	phone_number = order.dropoff_contact_phone_number
	if not validators.between(phone_number, 1000000000, 999999999999):
		return

	public_id = order.public_id
	if not validators.truthy(public_id):
		public_id = base64.b64encode(bytes(str(order.pk), 'utf-8')).decode().strip("=")
		order.public_id = public_id
		order.save()

	rider = order.rider
	rider_phone =  f'+{rider.phone_number}'
	rider_name = rider.full_names().strip().split()[0].strip()
	order_ref = order.ref if validators.truthy(order.ref) else order.pk


	url = reverse_lazy("order:review", kwargs={'public_id' : public_id})
	txt = f'{order.organization.driver_complete_sms} .To track your order {settings.TEMPLATE_HOST_URL}{url}'

	context = Context({"rider_name": rider_name, 'rider_phone' : rider_phone, 'order_ref' : order_ref})
	template = Template(txt)
	message = template.render(context)

	organization = order.organization

	# send sms
	send_sms(organization, phone_number, message)

def send_verify_message(verification_code, phone_number):
	message = f'Your verification code is {verification_code}'
	sms = africastalking.SMS
	phone_number = f'+{phone_number}'
	try:
		response = sms.send(message, [phone_number], sender_id=settings.DEFAULT_AFRICASTALKING_USERNAME)
		print(response)
	except Exception as e:
		print(e)
