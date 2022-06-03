from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone
from django.conf import settings
from django.db import models
import validators
import re


class UserManager(BaseUserManager):
	def create_user(self, email, password, name):
		if not email or not validators.truthy(email) or not validators.email(email):
			raise ValueError('Users must have an email address')

		if not name or not validators.truthy(name):
			raise ValueError('Users must have a name')

		names = re.sub(' +', ' ', name).strip().split(' ')
		first_name = names[0]
		last_name = names[1] if len(names) > 1 else ''

		user = self.model(email=self.normalize_email(email))
		user.first_name = first_name
		user.last_name = last_name
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password):
		if not email or not validators.truthy(email) or not validators.email(email):
			raise ValueError('Users must have an email address')

		user = self.model(email=self.normalize_email(email))
		user.first_name = ''
		user.last_name = ''
		user.set_password(password)
		user.save(using=self._db)
		return user


class User(AbstractBaseUser):
	email = models.EmailField(
		verbose_name='email address',
		max_length=75,
		unique=True,
	)
	first_name = models.CharField(max_length=25)
	last_name = models.CharField(max_length=25, null=True)
	is_email_verified = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	is_admin = models.BooleanField(default=False)

	objects = UserManager()

	USERNAME_FIELD = 'email'

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

	def __str__(self):
		return self.email

	def has_perm(self, perm, obj=None):
		"Does the user have a specific permission?"
		# Simplest possible answer: Yes, always
		return True

	def has_module_perms(self, app_label):
		"Does the user have permissions to view the app `app_label`?"
		# Simplest possible answer: Yes, always
		return True

	@property
	def is_staff(self):
		"Is the user a member of staff?"
		# Simplest possible answer: All admins are staff
		return self.is_admin

	def get_thumbnail(self):
		mod = self.pk % 5
		return f'{settings.STATIC_URL}theme/images/driver-default{mod}.png'


class VerifyEmailToken(models.Model):
	deleted = models.BooleanField(default=False)
	modified = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)
	token = models.CharField(max_length=255, null=True)
	user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)

	def is_old(self):
		d = timezone.now() - self.modified
		return d.seconds > 600
