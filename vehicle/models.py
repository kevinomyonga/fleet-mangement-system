from organization.models import Organization
from django.db import models
from user.models import User
import validators

class Vehicle(models.Model):
	HOURS = (
		(0, '12:00AM'),
		(1, '01:00AM'),
		(2, '02:00AM'),
		(3, '03:00AM'),
		(4, '04:00AM'),
		(5, '05:00AM'),
		(6, '06:00AM'),
		(7, '07:00AM'),
		(8, '08:00AM'),
		(9, '09:00AM'),
		(10, '10:00AM'),
		(11, '11:00AM'),
		(12, '12:00PM'),
		(13, '01:00PM'),
		(14, '02:00PM'),
		(15, '03:00PM'),
		(16, '04:00PM'),
		(17, '05:00PM'),
		(18, '06:00PM'),
		(19, '07:00PM'),
		(20, '08:00PM'),
		(21, '09:00PM'),
		(22, '10:00PM'),
		(23, '11:00PM'),
	)

	modified = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)

	name = models.CharField(max_length=255, null=True)
	reg_no = models.CharField(max_length=255, null=True)
	width = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	weight = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	length = models.DecimalField(max_digits=12, decimal_places=2, null=True)
	height = models.DecimalField(max_digits=12, decimal_places=2, null=True)

	service_start = models.PositiveSmallIntegerField(choices=HOURS,default=8)
	service_end = models.PositiveSmallIntegerField(choices=HOURS,default=17)

	organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

	address = models.CharField(max_length=255)
	lat = models.DecimalField(max_digits=22, decimal_places=16)
	lng = models.DecimalField(max_digits=22, decimal_places=16)

	added_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="vehicle_added_by") 
	modified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="vehicle_modified_by")

	def get_name(self):
		if validators.truthy(self.name) and validators.truthy(self.reg_no):
			name = self.name.strip()
			reg_no = self.reg_no.strip()
			return f'{name} {reg_no}'

		if validators.truthy(self.name):
			return self.name.strip()

		if validators.truthy(self.reg_no):
			return self.reg_no.strip()

		return f'{self.pk}'


	def to_dict(self):
		return {
			'ID' : self.pk,
			'name' : self.get_name(),
			'service' : {
				'start' : self.service_start,
				'end' : self.service_end,
				'end_display' : self.get_service_end_display(),
				'start_display' : self.get_service_start_display(),
			},
			'address' : {
				'name' : self.address,
				'lat' : str(self.lat),
				'lng' : str(self.lng),
			},
			'width' : str(self.width) if self.width is not None else None,
			'weight' : str(self.weight) if self.weight is not None else None,
			'length' : str(self.length) if self.length is not None else None,
			'height' : str(self.height) if self.height is not None else None	
		}



