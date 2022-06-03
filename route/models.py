from organization.models import Organization
from order.models import Order, OrderItem
from vehicle.models import Vehicle
from driver.models import Driver
from django.db import models
from user.models import User
import validators



class Route(models.Model):
	NOT_STARTED = 1
	STARTED = 2
	COMPETED = 3
	FAILED = 4

	STATUSES = (
		(NOT_STARTED,' Not Started'),
		(STARTED,'Started'),
		(COMPETED,'Completed'),
		(FAILED,'Failed'),
	)
	details = models.JSONField()
	geometry = models.TextField(null=True)
	orders = models.ManyToManyField(Order)
	cost = models.PositiveIntegerField(default=0)
	distance = models.PositiveIntegerField(default=0)
	duration = models.PositiveIntegerField(default=0)
	modified = models.DateTimeField(auto_now=True)
	created = models.DateTimeField(auto_now_add=True)
	order_count = models.PositiveSmallIntegerField(default=0)
	driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
	end_lat = models.DecimalField(max_digits=12, decimal_places=9, null=True)
	end_lng = models.DecimalField(max_digits=12, decimal_places=9, null=True)
	start_lat = models.DecimalField(max_digits=12, decimal_places=9, null=True)
	start_lng = models.DecimalField(max_digits=12, decimal_places=9, null=True)
	status = models.PositiveSmallIntegerField(choices=STATUSES,default=NOT_STARTED)
	added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="route_added_by")
	modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="route_modified_by")

	def to_dict_list(self):
		result = {
			'ID' : self.pk,
			'cost' : self.cost,
			'status' : self.status,
			'distance' : self.distance,
			'duration' : self.duration,
			'vehicle' : self.vehicle.to_dict(),
			'created' : self.created.isoformat(),
			'modified' : self.modified.isoformat(),
			'status_display' : self.get_status_display(),
			'order_count' : RouteItem.objects.filter(route=self).distinct('order').count(),
			'orders_completed' : Order.objects.filter(state__in=[5,6,7], pk__in=RouteItem.objects.filter(route=self).distinct('order').values_list("order")).count(),
		}
		return result

	def to_dict(self):
		from route.models import RouteItem
		result = self.to_dict_list()
		order_items = []
		for order_item in RouteItem.objects.filter(route=self).order_by('eta'):
			order_items.append(order_item.to_dict())
		result['items'] = order_items
		result['geometry'] = self.geometry
		result['locations'] = {
			'end' : {'lat' : self.end_lat, 'lng' : self.end_lng },
			'start' : {'lat' : self.start_lat, 'lng' : self.start_lng },
		}
		return result

	def to_dict2(self):
		result = {
			'ID' : self.pk,
			'details' : self.details,
			'driver' : self.driver.to_dict(),
			'vehicle' : self.vehicle.to_dict(),
			'created' : self.created.isoformat(),
			'modified' : self.modified.isoformat(),
		}
		order_items = []
		for order in self.orders.all():
			order_items.append(order.to_dict())
		result['orders'] = order_items
		return result


class RouteItem(models.Model):
	NOT_STARTED = 1
	STARTED = 2
	COMPETED = 3
	FAILED = 4

	STATUSES = (
		(NOT_STARTED,' Not Started'),
		(STARTED,'Started'),
		(COMPETED,'Completed'),
		(FAILED,'Failed'),
	)

	PICK_UP = 1
	DROP_OFF = 2

	_TYPES = (
		(PICK_UP,'Pickup'),
		(DROP_OFF,'Dropoff'),
	)
	eta = models.DateTimeField(null=True)
	distance = models.PositiveIntegerField(default=0)
	duration = models.PositiveIntegerField(default=0)
	service_time = models.PositiveIntegerField(default=0)
	waiting_time = models.PositiveIntegerField(default=0)
	_type = models.PositiveSmallIntegerField(choices=_TYPES)
	lat = models.DecimalField(max_digits=12, decimal_places=9, null=True)
	lng = models.DecimalField(max_digits=12, decimal_places=9, null=True)
	status = models.PositiveSmallIntegerField(choices=STATUSES,default=NOT_STARTED)
	route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="orderitem_route")
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orderitem_order")

	def to_dict(self):
		result = {
			'ID' : self.pk,
			'type' : self._type,
			'status' : self.status,
			'distance' : self.distance,
			'duration' : self.duration,
			'order' : self.order.to_dict(),
			'service_time' : self.service_time,
			'waiting_time' : self.waiting_time,
			'type_display' : self.get__type_display(),
			'status_display' : self.get_status_display(),
			'location' : {'lat' : self.lat, 'lng' : self.lng },
			'eta' : self.eta.isoformat() if self.eta is not None else None,
		}
		return result
