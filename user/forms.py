from organization.models import Organization, OrganizationUser
from django.contrib.auth import authenticate
from django.db import IntegrityError
from user.models import User
from django import forms
import validators

class RegisterForm(forms.Form):
	name = forms.CharField(
		error_messages={'required': 'Please enter your name'},
		widget=forms.TextInput(attrs={'placeholder': 'Name'})
	)
	email = forms.EmailField(
		label='Email address',
		error_messages={'required': 'Please enter a valid email'},
		widget=forms.TextInput(attrs={'placeholder': 'Email address'})
	)
	password = forms.CharField(
		error_messages={'required': 'Please enter your password'},
		widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
	)
	organisation_name = forms.CharField(
		error_messages={'required': 'Please enter your organisation name'},
		widget=forms.TextInput(attrs={'placeholder': 'Organisation name'})
	)
	country = forms.CharField(
		error_messages={'required': 'Please enter your country of operation'},
		widget=forms.TextInput(attrs={'placeholder': 'Country of operation'})
	)
	timezone = forms.CharField(
		error_messages={'required': 'Select your timezone'},
		widget=forms.TextInput(attrs={'placeholder': 'Timezone'})
	)

	def clean(self):
		cleaned_data = super(RegisterForm, self).clean()
		name = cleaned_data.get("name", None)
		email = cleaned_data.get("email", None)
		country = cleaned_data.get("country", None)
		password = cleaned_data.get("password", None)
		timezone = cleaned_data.get("timezone", None)
		organisation_name = cleaned_data.get("organisation_name", None)

		if not validators.truthy(name):
			self._errors["country"] = ["Select your country of operation"]
			return

		if not validators.truthy(name):
			self._errors["name"] = ["Enter a valid name"]
			return


		if not validators.truthy(timezone):
			self._errors["timezone"] = ["Select a valid timezone"]
			return

		if not validators.truthy(email) or not validators.email(email):
			self._errors["email"] = ["Enter a valid email"]
			return

		if not validators.truthy(organisation_name):
			self._errors["organisation_name"] = ["Enter a valid Organisation name"]
			return

		if not validators.truthy(password) or not validators.length(password.strip(), min=6):
			self._errors["password"] = ["Enter a valid password, must be greater than 6 characters"]
			return

		country = country.strip()
		password = password.strip()
		timezone = timezone.strip()
		organisation_name = organisation_name.strip()
		email = email.strip()
		name = name.strip()
		try:
			user = User.objects.get(email=email)
			self._errors["email"] = ["Email already registered"]
			return
		except User.DoesNotExist:
			pass

		try:
			user = User.objects.create_user(email, password, name)
		except IntegrityError:
			self._errors["email"] = ["Something went wrong, please try again"]
			return

		organisation = Organization.objects.create(
			owner = user,
			country = country,
			timezone = timezone,
			name = organisation_name
		)
		self.organisation_user = OrganizationUser.objects.create(
			user = user,
			organization = organisation
		)
		self.user = authenticate(email=email, password=password)

	def get_authenticated_user(self):
		return self.user

	def get_current_organization_user(self):
		return self.organisation_user
		

class LoginForm(forms.Form):
	user = None
	email = forms.EmailField(
		label='Email address',
		error_messages={'required': 'Please enter a valid email'},
		widget=forms.TextInput(attrs={'placeholder': 'Email address'})
	)
	password = forms.CharField(
		error_messages={'required': 'Please enter your password'},
		widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
	)

	def clean(self):
		cleaned_data = super(LoginForm, self).clean()
		email = cleaned_data.get("email", None)
		password = cleaned_data.get("password", None)

		if not validators.truthy(email) or not validators.email(email):
			self._errors["email"] = ["Enter a valid email"]
			return
	
		if not validators.truthy(password) or not validators.length(password, min=6):
			self._errors["password"] = ["Invalid username and/or password provided"]
			return

		email = email.strip()
		password = password.strip()
		user = authenticate(username=email, password=password)

		if user is None:
			self._errors["password"] = ["Invalid username and/or password provided"]
			return

		self.user = user

	def get_authenticated_user(self):
		return self.user

	def get_current_organization_user(self):
		return OrganizationUser.objects.filter(user=self.user, deleted=False, is_active=True).order_by('-modified').first()
