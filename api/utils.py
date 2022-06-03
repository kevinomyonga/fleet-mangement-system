from firebase_admin import messaging
from django.conf import settings

def send_message(message, phone_number):
	africastalking.initialize(settings.DEFAULT_AFRICASTALKING_USERNAME, settings.DEFAULT_AFRICASTALKING_API_KEY)
	sms = africastalking.SMS
	recipients = [f"+{phone_number}"]
	try:
		return sms.send(message, recipients, sender_id=settings.DEFAULT_AFRICASTALKING_USERNAME)
	except Exception as e:
		print ('Encountered an error while sending: %s' % str(e))
		return None


def new_assignment_driver_push(order):
	if order is None:
		return

	driver = order.rider
	if driver is None:
		return

	driver_auth = driver.get_driver_auth()
	if driver_auth is None:
		return

	driver_fcms = driver_auth.get_fcms()
	if driver_fcms.count() < 1:
		return

	payload = {
		'userID' : str(driver.pk),
		'orderID' : str(order.pk),
		'phoneNumber' : str(driver_auth.phone_number),
		'organizationID' : str(driver.organization.pk),
	}
	for driver_fcm in driver_fcms[:10]:
		token = driver_fcm.token
		message = messaging.Message(data=payload,token=token)
		try:
			response = messaging.send(message)
			print(response)
			success = True
		except Exception as e:
			print(e)
			pass


def payment_made_driver_push(order, payment):
	if order is None:
		return

	driver = order.rider
	if driver is None:
		return

	driver_auth = driver.get_driver_auth()
	if driver_auth is None:
		return

	driver_fcms = driver_auth.get_fcms()
	if driver_fcms.count() < 1:
		return

	payload = {
		'userID' : str(driver.pk),
		'organizationID' : str(driver.organization.pk),
		'orderID' : str(order.pk),
		'phoneNumber' : str(driver_auth.phone_number),
		'MpesaReceiptNumber': str(payment.MpesaReceiptNumber),
		'price': str(order.price),
		'amount': str(payment.Amount),
	}
	for driver_fcm in driver_fcms[:10]:
		token = driver_fcm.token
		message = messaging.Message(data=payload,token=token)
		try:
			response = messaging.send(message)
			print(response)
			success = True
		except Exception as e:
			print(e)
			pass
