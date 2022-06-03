from sms.tasks import order_created_sms
from django.db import IntegrityError
import validators, datetime
from django import forms
from . import models

class CreateForm(forms.Form):
	pickup_lat = forms.DecimalField(required=False)
	pickup_lng = forms.DecimalField(required=False)
	pickup_email = forms.EmailField(required=False)
	pickup_details = forms.CharField(required=False)
	pickup_address_more = forms.CharField(required=False)
	pickup_name = forms.CharField(error_messages={'required': 'Enter a pickup contact name'})
	pickup_address = forms.CharField(error_messages={'required': 'Enter a pickup location address'})
	pickup_phone_number = forms.IntegerField(error_messages={'required': 'Enter a pickup contact phone number'})

	dropoff_lat = forms.DecimalField(required=False)
	dropoff_lng = forms.DecimalField(required=False)
	dropoff_email = forms.EmailField(required=False)
	dropoff_details = forms.CharField(required=False)
	dropoff_address_more = forms.CharField(required=False)
	dropoff_name = forms.CharField(error_messages={'required': 'Enter a drop-off contact name'})
	dropoff_address = forms.CharField(error_messages={'required': 'Enter a drop-off location address'})
	dropoff_phone_number = forms.IntegerField(error_messages={'required': 'Enter a drop-off contact phone number'})

	ref = forms.CharField(required=False)
	length = forms.DecimalField(required=False)
	width = forms.DecimalField(required=False)
	height = forms.DecimalField(required=False)
	weight = forms.DecimalField(required=False)
	price = forms.DecimalField(required=False)
	payment_method = forms.ChoiceField(choices=models.Order.PAYMENT_METHOD, required=True)
	preffered_delivery_date = forms.DateField(initial=datetime.date.today, required=False)
	preffered_delivery_time = forms.ChoiceField(choices=models.Order.PREFERED_TIME, required=True)


	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop("user")
		self.organization = kwargs.pop("organization")
		super(CreateForm, self).__init__(*args, **kwargs)

	def clean(self):
		cleaned_data = super(CreateForm, self).clean()
		pickup_name = cleaned_data.get("pickup_name", "")
		pickup_lat = cleaned_data.get("pickup_lat", None)
		pickup_lng = cleaned_data.get("pickup_lng", None)
		pickup_email = cleaned_data.get("pickup_email", None)
		pickup_address = cleaned_data.get("pickup_address", None)
		pickup_address_more = cleaned_data.get("pickup_address_more", None)
		pickup_phone_number = cleaned_data.get("pickup_phone_number", None)

		dropoff_name = cleaned_data.get("dropoff_name", "")
		dropoff_lat = cleaned_data.get("dropoff_lat", None)
		dropoff_lng = cleaned_data.get("dropoff_lng", None)
		dropoff_email = cleaned_data.get("dropoff_email", None)
		dropoff_address = cleaned_data.get("dropoff_address", None)
		dropoff_address_more = cleaned_data.get("dropoff_address_more", None)
		dropoff_phone_number = cleaned_data.get("dropoff_phone_number", None)

		ref = cleaned_data.get("ref", None)
		price = cleaned_data.get("price", None)
		width = cleaned_data.get("width", None)
		height = cleaned_data.get("height", None)
		weight = cleaned_data.get("weight", None)
		length = cleaned_data.get("length", None)
		#payment_method = cleaned_data.get("payment_method", None)
		#preffered_delivery_date = cleaned_data.get("preffered_delivery_date", None)

		ref = ref if validators.truthy(ref) else None
		order = models.Order.objects.create(
			ref = ref,

			price = price,
			width = width,
			weight = weight,
			length = length,
			height = height,
			#payment_method = payment_method,
			#preffered_delivery_date = preffered_delivery_date,

			added_by = self.user,
			modified_by = self.user,

			pickup_lat = pickup_lat,
			pickup_lng = pickup_lng,
			pickup_contact_name = pickup_name,
			pickup_contact_email = pickup_email,
			pickup_location_name = pickup_address,
			pickup_location_name_more = pickup_address_more,
			pickup_contact_phone_number = pickup_phone_number,

			dropoff_lat = dropoff_lat,
			dropoff_lng = dropoff_lng,
			dropoff_contact_name = dropoff_name,
			dropoff_contact_email = dropoff_email,
			dropoff_location_name = dropoff_address,
			dropoff_location_name_more = dropoff_address_more,
			dropoff_contact_phone_number = dropoff_phone_number,

			organization = self.organization
		)
		order_created_sms(order)
