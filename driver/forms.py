from django.db import IntegrityError
from django import forms
from . import models
import validators

class CreateForm(forms.Form):
	name = forms.CharField(
		error_messages={'required': 'Enter a driver name'},
		widget=forms.TextInput(attrs={'placeholder': 'Name'})
	)
	phone_number = forms.IntegerField(
		error_messages={'required': 'Enter a driver phone number'},
		widget=forms.TextInput(attrs={'placeholder': 'Phone number'})
	)
	def __init__(self, *args, **kwargs):
		self.organization = kwargs.pop("organization")
		super(CreateForm, self).__init__(*args, **kwargs)


	def clean(self):
		cleaned_data = super(CreateForm, self).clean()
		name = cleaned_data.get("name", None)
		phone_number = cleaned_data.get("phone_number", None)

		if not validators.truthy(name):
			self._errors["name"] = ["Enter a valid name"]
			return

		if not validators.truthy(phone_number):
			self._errors["phone_number"] = ["Enter a valid phone number"]
			return

		name = name.strip()
		phone_number = phone_number
		try:
			driver = models.Driver.objects.get(
				phone_number=phone_number,
				organization=self.organization
			)
			self._errors["phone_number"] = ["Phone number already registered"]
			return
		except models.Driver.DoesNotExist:
			pass

		try:
			user = models.Driver.objects.create_new(phone_number, self.organization, name)
		except IntegrityError:
			self._errors["email"] = ["Something went wrong, please try again"]
			return
