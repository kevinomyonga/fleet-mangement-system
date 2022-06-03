from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import post_save
from django.db import connection, OperationalError
from organization.models import Organization
from django.dispatch import receiver
from django.utils import timezone
from driver.models import Driver, Coords
from user.models import User
from django.db import models
import datetime, validators

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer




# from django_fsm import FSMIntegerField

# For logging
class OrderStatusLog(models.Model):
	order_id = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_status_logs')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now_add=True)
	action = models.CharField(max_length=50)

	class Meta:
		"""Meta definition for OrderStatusLog."""

		verbose_name = 'OrderStatusLog'
		verbose_name_plural = 'OrderStatusLogs'

	def __str__(self):
		"""Unicode representation of OrderStatusLog."""
		return f'{self.action}'


class OrderItem(models.Model):
	COLLECTED = 1
	NOT_COLLECTED = 2
	DAMAGED = 3
	REJECTED = 4
	FAILED = 5
	DELIVERED = 6
	RETURNED = 7

	STATUSES = (
		(NOT_COLLECTED,'Not collected'),
		(COLLECTED,'Collected for delivery'),
		(DAMAGED,'Damaged in transit'),
		(REJECTED,'Rejected by recipeint'),
		(FAILED,'Failed'),
		(DELIVERED,'Delivered'),
		(RETURNED, 'Returned to warehouse'),
	)
	name = models.CharField(max_length=75)
	paid = models.BooleanField(default=False)
	state = models.PositiveIntegerField(choices=STATUSES,default=NOT_COLLECTED)
	price = models.DecimalField(max_digits=50,decimal_places=2, null=True)
	width = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	weight = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	length = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	height = models.DecimalField(max_digits=12, decimal_places=2, null=True)

class OrderFailure(models.Model):
	reason = models.CharField(max_length=1024)
	created = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
	#payment status
	PREPAID = 1
	POSTPAID = 2
	POSTPAID_MM = 3
	CREDIT = 4

	#Vehicle types

	TBD = 0
	MOTOBIKE = 1
	MOTOBIKEWITHBOX = 2
	PICKUP_OPEN = 3
	PICKUP_CLOSED = 4
	VAN = 5
	TRUCK_3T = 6
	TRUCK_4T = 7
	TRUCK_5T = 8
	TRUCK_7T = 9
	TRUCK_10T = 10
	TRUCK_12T = 11
	TRUCK_25T = 12
	TRUCK_27T = 13
	TRUCK_3T_REFER = 14
	TRAILER = 15
	INTER_COUNTY = 16
	GLOBAL = 17


	PAYMENT_METHOD = (
		(PREPAID,'Prepaid'),
		(POSTPAID,'Postpaid - Cash'),
		(POSTPAID_MM,'Postpaid - Mobile money'),
		(CREDIT,'Credit'),
	)

	VEHICLE_TYPES = (
		(TBD, 'TBD'),
		(MOTOBIKE, 'Motorbike'),
		(MOTOBIKEWITHBOX, 'Motorbike with box'),
		(PICKUP_OPEN, 'Pick Up Open'),
		(PICKUP_CLOSED, 'Pick Up Closed'),
		(VAN, 'Van'),
		(TRUCK_3T, 'Truck 3 Tone'),
		(TRUCK_4T, 'Truck 4 Tone'),
		(TRUCK_5T, 'Truck 5 Tone'),
		(TRUCK_7T, 'Truck 7 Tone'),
		(TRUCK_10T, 'Truck 10 Tone'),
		(TRUCK_12T, 'Truck 12 Tone'),
		(TRUCK_25T, 'Truck 25 Tone'),
		(TRUCK_27T, 'Truck 27 Tone'),
		(TRUCK_3T_REFER, 'Truck 3 Tone Refer'),
		(TRAILER, 'Trailer 27 Ton with container'),
		(INTER_COUNTY, 'Inter-county'),
		(GLOBAL, 'Global'),
	)


	# delivery state
	DRAFT = 1
	""" submitted time """
	SUBMITTED_PENDING_VENDOR_PICK_UP = 2
	SUBMITTED_PENDING_FOWARD_DELIVERY = 3
	""" Dispatched """
	DISPATCHED = 4
	""" Arrival at client """
	ARRAVAL_AT_CLIENT = 5
	""" Failed """
	FAILED_AT_CLIENT = 6
	""" delivered """
	DELIVERED = 7
	""" submit to warehouse """
	SUBMITTED_RETURN_TO_WAREHOUSE = 8
	""" complete """
	COMPLETED_TO_WAREHOUSE = 9
	""" vendor """
	SUBMITTED_RETURN_TO_VENDOR = 10
	""" complete to vendor  """
	COMPLETED_TO_VENDOR = 11
	""" Admin approve all completed orders """
	CANCELLED = 12
	""" Admin approve all completed orders """
	RESCHEDULED = 13
	""" Order has been rescheduled """

	DELIVERY_STATE = (
		(DRAFT,'Submitted'),
		(SUBMITTED_PENDING_VENDOR_PICK_UP,'Driver Unassigned'),
		(SUBMITTED_PENDING_FOWARD_DELIVERY,'Driver Assigned'),
		(DISPATCHED,'in progress'),
		(ARRAVAL_AT_CLIENT, 'Arrival at client'),
		(FAILED_AT_CLIENT, 'Failed'),
		(DELIVERED, 'Delivered'),
		(SUBMITTED_RETURN_TO_WAREHOUSE, 'failed awaiting warehouse'),
		(COMPLETED_TO_WAREHOUSE, 'Delivered at warehouse'),
		(SUBMITTED_RETURN_TO_VENDOR, 'Returned from warehouse'),
		(COMPLETED_TO_VENDOR, 'Recieved from warehouse'),
		(CANCELLED, 'Cancelled'),
		(RESCHEDULED, 'Rescheduled'),

	)

	ANYTIME = 1
	MORNING = 2
	AFTERNOON = 3

	PREFERED_TIME = (
		(ANYTIME, 'Anytime'),
		(MORNING, 'Morning'),
		(AFTERNOON, 'Afternoon')
	)
	paid = models.BooleanField(default=False)
	notes = models.TextField(blank=True, null=True)
	ref = models.CharField(max_length=50, null=True)
	sid = models.CharField(max_length=50, null=True, blank=True)
	public_id = models.CharField(max_length=75, null=True, unique=True)
	state = models.PositiveIntegerField(choices=DELIVERY_STATE,default=DRAFT)
	# Bump state to status
	# status = FSMIntegerField(default=DRAFT)
	payment_method = models.PositiveSmallIntegerField(choices=PAYMENT_METHOD,default=PREPAID)


	modified = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)


	datetime_failed = models.DateTimeField(null=True)
	datetime_started = models.DateTimeField(null=True)
	datetime_arrived = models.DateTimeField(null=True)
	datetime_assigned = models.DateTimeField(null=True)
	datetime_accepted = models.DateTimeField(null=True)
	datetime_reviewed = models.DateTimeField(null=True)
	datetime_completed = models.DateTimeField(null=True)
	datetime_ordered = models.DateTimeField(default=timezone.now)

	failure_reason = models.CharField(max_length=255, null=True)
	complete_lat = models.DecimalField(max_digits=22, decimal_places=16, null=True)
	complete_lng = models.DecimalField(max_digits=22, decimal_places=16, null=True)

	payment_notes = models.CharField(max_length=2048, null=True)
	signature = models.URLField(max_length=2048, null=True)
	pod_images = ArrayField(models.URLField(max_length=2048), null=True)

	price = models.DecimalField(max_digits=50,decimal_places=2, null=True)
	width = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	weight = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	length = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	height = models.DecimalField(max_digits=12, decimal_places=2, null=True)

	pickup_location_details = models.TextField(null=True)
	pickup_location_name = models.CharField(max_length=255)
	pickup_contact_phone_number = models.BigIntegerField(null=True)
	pickup_contact_name = models.CharField(max_length=255, null=True)
	pickup_contact_email = models.EmailField(max_length=254, null=True)
	pickup_location_name_more = models.CharField(max_length=255, null=True)
	pickup_lat = models.DecimalField(max_digits=22, decimal_places=16, null=True)
	pickup_lng = models.DecimalField(max_digits=22, decimal_places=16, null=True)

	dropoff_location_details = models.TextField(null=True)
	dropoff_location_name = models.CharField(max_length=255)
	dropoff_contact_phone_number = models.BigIntegerField(null=True)
	dropoff_contact_name = models.CharField(max_length=255, null=True)
	dropoff_contact_email = models.EmailField(max_length=254, null=True)
	dropoff_location_name_more = models.CharField(max_length=255, null=True)
	dropoff_lat = models.DecimalField(max_digits=22, decimal_places=16, null=True)
	dropoff_lng = models.DecimalField(max_digits=22, decimal_places=16, null=True)

	customer_phone_number = models.BigIntegerField(null=True)
	customer_email = models.EmailField(max_length=254, null=True)
	customer_last_name = models.CharField(max_length=75, null=True)
	customer_first_name = models.CharField(max_length=75, null=True)

	review = models.CharField(max_length=2048, null=True, blank=True)
	rating = models.DecimalField(max_digits=2, decimal_places=1, null=True)

	rider = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True)
	vehicle_type = models.PositiveSmallIntegerField(choices=VEHICLE_TYPES, default=TBD)

	preffered_delivery_date = models.DateField(default=datetime.date.today)
	preffered_delivery_period = models.PositiveSmallIntegerField(default=ANYTIME, choices=PREFERED_TIME)

	failures = models.ManyToManyField(OrderFailure)
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
	added_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="order_added_by")
	modified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="order_modified_by")

	items = models.ManyToManyField(OrderItem)

	prev_id = models.BigIntegerField(null=True, db_index=True)
	prev_id_external = models.BigIntegerField(null=True, db_index=True)

	class Meta:
		unique_together = [['ref', 'organization']]
		index_together = [
			["rider", "datetime_ordered", "state", "organization"],
			["datetime_ordered", "state", "organization"],
			["rating", "datetime_ordered", "organization"],
		]

	def mpesa_code(self):


			# check if mpesa transaction exists
		mpesa_exists = MpesaPayments.objects.filter(order__pk =self.pk).exists()

		if mpesa_exists:
			details = MpesaPayments.objects.filter(order__pk =self.pk)
			return details
		else:
			return None

	def driver_location(self):
		if self.rider is not None and self.rider.get_driver_location() is not None:
			return self.rider.get_driver_location()

		if validators.truthy(self.pickup_lat) and \
			validators.truthy(self.pickup_lng) and \
			validators.between(self.pickup_lng, -180.0, 180.0) and \
			validators.between(self.pickup_lat, -90.0, 90.0):
			c = Coords()
			c.lat = self.pickup_lat
			c.lng = self.pickup_lng
			return c

		return None


	def time_ago(self):
		d = timezone.now() - self.created
		return self.hms(d.total_seconds())

	def driver_time_ago(self):
		if self.datetime_assigned:
			d = timezone.now() - self.datetime_assigned
			return self.hms(d.total_seconds())
		else:
			return "Unknown"


	def hms(self, seconds):
		d = int(seconds // (3600 * 24))
		h = int(seconds % (3600 * 24) // 3600)
		m = int(seconds % 3600 // 60)
		if d > 0:
			return '{:02d} days: {:02d} hrs ago'.format(d, h)

		if h < 1:
			if m < 2:
				return 'now'
			return '{:02d} mins ago'.format(m)

		return '{:02d} hrs: {:02d} mins ago'.format(h, m)

	def allowed_states(self):
		if self.state == self.DRAFT:
			return (
				(self.FAILED_AT_CLIENT, 'Failed'),
				(self.DELIVERED, 'Delivered'),
				(self.SUBMITTED_RETURN_TO_WAREHOUSE, 'failed awaiting warehouse'),
				(self.COMPLETED_TO_WAREHOUSE, 'Delivered at warehouse'),
				(self.SUBMITTED_RETURN_TO_VENDOR, 'Returned from warehouse'),
				(self.COMPLETED_TO_VENDOR, 'Recieved from warehouse'),
				(self.CANCELLED, 'Cancelled'),
				(self.RESCHEDULED, 'Rescheduled'),

			)
		elif self.state == self.SUBMITTED_PENDING_VENDOR_PICK_UP:
			return (
				(self.FAILED_AT_CLIENT, 'Failed'),
				(self.DELIVERED, 'Delivered'),
				(self.SUBMITTED_RETURN_TO_WAREHOUSE, 'failed awaiting warehouse'),
				(self.COMPLETED_TO_WAREHOUSE, 'Delivered at warehouse'),
				(self.SUBMITTED_RETURN_TO_VENDOR, 'Returned from warehouse'),
				(self.COMPLETED_TO_VENDOR, 'Recieved from warehouse'),
				(self.CANCELLED, 'Cancelled'),
				(self.RESCHEDULED, 'Rescheduled'),
			)
		elif self.state == self.SUBMITTED_PENDING_FOWARD_DELIVERY:
			return (
				(self.DISPATCHED,'in progress'),
				(self.ARRAVAL_AT_CLIENT, 'Arrival at client'),
				(self.FAILED_AT_CLIENT, 'Failed'),
				(self.DELIVERED, 'Delivered'),
				(self.SUBMITTED_RETURN_TO_WAREHOUSE, 'failed awaiting warehouse'),
				(self.COMPLETED_TO_WAREHOUSE, 'Delivered at warehouse'),
				(self.SUBMITTED_RETURN_TO_VENDOR, 'Returned from warehouse'),
				(self.COMPLETED_TO_VENDOR, 'Recieved from warehouse'),
				(self.CANCELLED, 'Cancelled'),
				(self.RESCHEDULED, 'Rescheduled'),
			)
		else:
			return (
				(self.ARRAVAL_AT_CLIENT, 'Arrival at client'),
				(self.FAILED_AT_CLIENT, 'Failed'),
				(self.DELIVERED, 'Delivered'),
				(self.SUBMITTED_RETURN_TO_WAREHOUSE, 'failed awaiting warehouse'),
				(self.COMPLETED_TO_WAREHOUSE, 'Delivered at warehouse'),
				(self.SUBMITTED_RETURN_TO_VENDOR, 'Returned from warehouse'),
				(self.COMPLETED_TO_VENDOR, 'Recieved from warehouse'),
				(self.CANCELLED, 'Cancelled'),
				(self.RESCHEDULED, 'Rescheduled'),
			)

	def items_to_dict(self):
		items = []
		for item in self.items.all():
			items.append({'id' : item.pk, 'paid': item.paid, 'price' : str(item.price), 'name' : item.name})
		return items

	def to_dict(self):
		order_dict = {
			'ID': self.pk,
			'ref': self.ref,
			'sid': self.sid,
			'state' : self.state,
			'state_display' : self.get_state_display(),
			'notes' : self.notes,
			'payment_method' : self.payment_method,
			'payment_method_display' : self.get_payment_method_display(),
			'paid' : self.paid if self.payment_method == self.POSTPAID else True,
			'modified' : self.modified.isoformat(),
			'created' : self.created.isoformat(),
			'signature' : self.signature,
			'pod_images' : self.pod_images,
			'datetime_failed' : self.datetime_failed.isoformat() if self.datetime_failed is not None else None,
			'datetime_ordered' : self.datetime_ordered.isoformat() if self.datetime_ordered is not None else None,
			'datetime_reviewed' : self.datetime_reviewed.isoformat() if self.datetime_reviewed is not None else None,
			'datetime_completed' : self.datetime_completed.isoformat() if self.datetime_completed is not None else None,

			'price' : str(self.price) if self.price is not None else None,
			'width' : str(self.width) if self.width is not None else None,
			'weight' : str(self.weight) if self.weight is not None else None,
			'length' : str(self.length) if self.length is not None else None,
			'height' : str(self.height) if self.height is not None else None,

			'pickup' : {
				'location' : {
					'address' : self.pickup_location_name,
					'apartment' : self.pickup_location_name_more,
					'coords' : {
						'lat' : str(self.pickup_lat) if self.pickup_lat is not None else None,
						'lng' : str(self.pickup_lng) if self.pickup_lng is not None else None,
					}
				},
				'contact' : {
					'name' : self.pickup_contact_name,
					'email' : self.pickup_contact_email,
					'phone_number' : self.pickup_contact_phone_number,
					'name' : self.pickup_contact_name,
				},
				'notes' : self.pickup_location_details
			},
			'dropoff' : {
				'location' : {
					'address' : self.dropoff_location_name,
					'apartment' : self.dropoff_location_name_more,
					'coords' : {
						'lat' : str(self.dropoff_lat) if self.dropoff_lat is not None else None,
						'lng' : str(self.dropoff_lng) if self.dropoff_lng is not None else None,
					}
				},
				'contact' : {
					'name' : self.dropoff_contact_name,
					'email' : self.dropoff_contact_email,
					'phone_number' : self.dropoff_contact_phone_number,
					'name' : self.dropoff_contact_name,
				},
				'notes' : self.dropoff_location_details
			},
			'review' : self.review,
			'rating' : str(self.rating) if self.rating is not None else None,
			'items' : self.items_to_dict(),
			'rider' : None,
			'vehicle_type' : self.vehicle_type,
			'vehicle_type_display' : self.get_vehicle_type_display(),
			'preffered_delivery_date' : self.preffered_delivery_date.isoformat(),
			'preffered_delivery_period' : self.preffered_delivery_period,
			'preffered_delivery_period_display' : self.get_preffered_delivery_period_display()
		}
		if self.rider is not None:
			order_dict['rider'] = {
				'ID' : self.rider.pk,
				'name' : self.rider.full_names(),
				'phone_number' : self.rider.phone_number,
			}
		return order_dict


@receiver(post_save, sender=Order)
def notify_client(sender, instance, created, **kwargs):
	callback_url = instance.organization.callback_url
	if validators.truthy(callback_url) and validators.url(callback_url):
		from .tasks import ping_callback
		ping_callback.delay(instance.pk)

	sync_callback_url = instance.organization.sync_callback_url
	if validators.truthy(sync_callback_url) and validators.url(sync_callback_url):
		from .tasks import replicate_order
		replicate_order.delay(instance.pk)

	organization_id = instance.organization.pk
	group_name = f"orders_{organization_id}"
	print(group_name)
	channel_layer = get_channel_layer()

	if created:
		print(f'New order with pk: {instance.pk} was created.')
		async_to_sync(channel_layer.group_send)(group_name, {'type' : "order.created", "message" : instance.pk})
	else:
		print(f'Order with pk: {instance.pk} was updated.')
		async_to_sync(channel_layer.group_send)(group_name, {'type' : "order.updated", "message" : instance.pk})


class STKPushRequest(models.Model):
    MerchantRequestID = models.CharField(max_length=50)
    CheckoutRequestID = models.CharField(max_length=50)
    ResponseCode = models.IntegerField()
    ResponseDescription = models.CharField(max_length=150)
    CustomerMessage = models.CharField(max_length=150)
    AccountReference = models.CharField(max_length=150)
    TransactionDesc = models.CharField(max_length=150)
    PhoneNumber = models.CharField(max_length=150)
    TransactionDate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Checkout id: {self.CheckoutRequestID} by {self.PhoneNumber}"

class MpesaPayments(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	MpesaReceiptNumber = models.CharField(max_length=20, primary_key=True)
	MerchantRequestID = models.CharField(max_length=50, blank=True, null=True, default='')
	CheckoutRequestID = models.CharField(max_length=50, blank=True, null=True, default='')
	ResultCode = models.IntegerField(blank=True, null=True, default=0)
	ResultDesc = models.CharField(max_length=150, blank=True, null=True, default='')
	Amount = models.FloatField(blank=True, null=True, default=0.0)
	PhoneNumber = models.CharField(max_length=13, blank=True, null=True, default='')
	TransactionDate = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
