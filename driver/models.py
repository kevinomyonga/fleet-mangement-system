from organization.models import Organization
from django.utils import timezone
from django.conf import settings
from passlib.hash import scram
import random, re, validators
from user.models import User
from django.db import models

class InvalidPasswordException(Exception):
	pass

class InvalidPhoneNumberException(Exception):
	pass

class DriverNotFoundException(Exception):
	pass


class DriverManager(models.Manager):

	def get_by_phone_number(self, phone_number, organization):
		try:
			phone_number = int(phone_number)
		except ValueError:
			return None

		if not validators.between(phone_number, 100000000, 99999999999999):
			return None

		try:
			return self.get(phone_number=phone_number, organization=organization)
		except self.model.DoesNotExist:
			return None

	def create_new(self, phone_number, organization, name, reg_no):
		names = re.sub(' +', ' ', name).strip().split(' ')
		first_name = names[0]
		last_name = names[1] if len(names) > 1 else ''

		driver = self.model(
			reg_no = reg_no,
			last_name = last_name,
			first_name = first_name,
			phone_number = phone_number,
			organization = organization
		)
		driver.save(using=self._db)
		return driver

class DriverAuthManager(models.Manager):

	def create_new(self, phone_number, password):
		phone_number = int(phone_number)
		if not validators.between(phone_number, 100000000, 99999999999999):
			raise InvalidPhoneNumberException()

		if not validators.truthy(password) or len(password.strip()) < 6:
			raise InvalidPasswordException()

		driver = self.model(
			password_hash = scram.hash(password),
			phone_number = phone_number
		)
		driver.save(using=self._db)
		return driver

	def get_by_phone_number(self, phone_number):
		try:
			phone_number = int(phone_number)
		except ValueError:
			return None

		if not validators.between(phone_number, 100000000, 99999999999999):
			return None

		try:
			return self.get(phone_number=phone_number)
		except self.model.DoesNotExist:
			return None

	def auth(self, phone_number, password):
		phone_number = int(phone_number)
		if not validators.between(phone_number, 100000000, 999999999999):
			return None

		if not validators.truthy(password) or len(password.strip()) < 6:
			return None

		driver = self.get_by_phone_number(phone_number)
		if driver is None:
			return None

		password = password.strip()
		if scram.verify(password, driver.password_hash):
			return driver

		return None


class Coords:
	lat = None
	lng = None

class Driver(models.Model):
	phone_number = models.BigIntegerField()
	deleted = models.BooleanField(default=False)

	last_name = models.CharField(max_length=75, null=True)
	first_name = models.CharField(max_length=75, null=True)

	reg_no = models.CharField(max_length=12, null=True)
	rating = models.DecimalField(max_digits=2, decimal_places=1, null=True)

	modified = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)

	organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

	added_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="driver_added_by")
	modified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="driver_modified_by")

	prev_id = models.BigIntegerField(null=True, db_index=True)
	prev_id_external = models.BigIntegerField(null=True, db_index=True)

	objects = DriverManager()

	class Meta:
		unique_together = [['phone_number', 'organization']]

	def update(self, name, phone_number, reg_no):
		names = re.sub(' +', ' ', name).strip().split(' ')
		first_name = names[0]
		last_name = names[1] if len(names) > 1 else ''

		self.last_name = last_name
		self.first_name = first_name
		self.phone_number = phone_number
		self.reg_no = reg_no
		self.save()

	def get_thumbnail(self):
		driver_auth = self.get_driver_auth()
		if driver_auth is not None and validators.truthy(driver_auth.thumbnail):
			return driver_auth.thumbnail
		else:
			mod = self.pk % 5
			return f'{settings.STATIC_URL}theme/images/driver-default{mod}.png'

	def get_driver_location(self):
		driver_auth = self.get_driver_auth()
		if driver_auth is not None and \
			validators.truthy(driver_auth.lat) and \
			validators.truthy(driver_auth.lng) and \
			validators.between(driver_auth.lng, -180.0, 180.0) and \
			validators.between(driver_auth.lat, -90.0, 90.0):
			c = Coords()
			c.lat = driver_auth.lat
			c.lng = driver_auth.lng
			return c

		return None



	def get_driver_auth(self):
		from driver.models import DriverAuth
		try:
			driver_auth = DriverAuth.objects.get(phone_number=self.phone_number)
		except DriverAuth.DoesNotExist:
			driver_auth = None

		return driver_auth



	def full_names(self):
		if validators.truthy(self.first_name) and validators.truthy(self.last_name):
			f_name = self.first_name.strip()
			l_name = self.last_name.strip()
			return f'{f_name} {l_name}'

		if validators.truthy(self.first_name):
			f_name = self.first_name.strip()
			return f_name

		if validators.truthy(self.last_name):
			l_name = self.last_name.strip()
			return l_name

		return self.phone_number


	def completed_orders(self):
		from order.models import Order
		return Order.objects.filter(rider=self,state=Order.DELIVERED).count()

	def total_orders(self):
		from order.models import Order
		return Order.objects.filter(rider=self).count()

	def in_progress_orders(self):
		from order.models import Order
		return Order.objects.filter(rider=self,state__lte=Order.ARRAVAL_AT_CLIENT).count()

	def failed_orders(self):
		from order.models import Order
		return Order.objects.filter(rider=self,state=Order.FAILED_AT_CLIENT).count()



	def to_dict(self):
		c = self.get_driver_location()
		return {
			'ID' : self.pk,
			'rating' : self.rating,
			'name' : self.full_names(),
			'thumbnail' : self.get_thumbnail(),
			'phone_number' : self.phone_number,
			'failed_orders' : self.failed_orders(),
			'in_progress_orders' : self.in_progress_orders(),
			'completed_orders' : self.completed_orders(),
			'location' : { 'lat' : c.lat, 'lng' : c.lng } if c is not None else None
		}



class DriverAuth(models.Model):
	modified = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)
	password_hash = models.CharField(max_length=2048)
	is_password = models.BooleanField(default=False)

	last_name = models.CharField(max_length=75, null=True)
	first_name = models.CharField(max_length=75, null=True)

	location_update_time = models.DateTimeField(null=True)
	lat = models.DecimalField(max_digits=22, decimal_places=16, null=True)
	lng = models.DecimalField(max_digits=22, decimal_places=16, null=True)

	avatar = models.URLField(max_length=2048, null=True)
	thumbnail = models.URLField(max_length=2048, null=True)

	phone_number = models.BigIntegerField(primary_key=True)
	code_send_count = models.PositiveIntegerField(default=0)
	verification_code = models.PositiveIntegerField(null=True)
	verification_time = models.DateTimeField(default=timezone.now)
	verification_tries = models.PositiveSmallIntegerField(default=0)

	objects = DriverAuthManager()

	def set_password(self, password):
		if not validators.truthy(password) or len(password.strip()) < 6:
			raise InvalidPasswordException()

		password = password.strip()
		self.password_hash = scram.hash(password)
		self.save()

	def get_fcms(self):
		from driver.models import DriverAuthFCM
		return DriverAuthFCM.objects.filter(driver_auth=self, is_valid=True).order_by('-modified')


class DriverAuthToken(models.Model):
	modified = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)
	token = models.CharField(max_length=2048,unique=True)

	is_valid = models.BooleanField(default=True)
	driver_auth = models.ForeignKey(DriverAuth, on_delete=models.CASCADE)

	class Meta:
		unique_together = [['driver_auth', 'token']]


class DriverAuthFCM(models.Model):
	token = models.CharField(max_length=2048)
	modified = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)

	is_valid = models.BooleanField(default=True)
	last_fail_time = models.DateTimeField(null=True)
	failed_tries = models.PositiveSmallIntegerField(default=0)
	driver_auth = models.ForeignKey(DriverAuth, on_delete=models.CASCADE)

	class Meta:
		unique_together = [['driver_auth', 'token']]
