from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import DurationField, F, ExpressionWrapper
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from django.core.paginator import PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from organization.http import PermissionView
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.views.generic import ListView
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.urls import reverse_lazy
from order.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from vehicle.models import Vehicle
from driver.models import Driver
from order.models import Order
from . import models
import validators, json

class JsonView(PermissionView):
	def get_paginator(self):
		page = self.request.GET.get('page', 1)
		per_page = self.request.GET.get('per_page', 50)
		q = models.Route.objects.filter(
			organization=self.get_current_organization(),
		).order_by('-modified')
		return (Paginator(q, per_page), page)

	def to_json(self):
		paginator, page = self.get_paginator()
		count = paginator.count
		num_pages = paginator.num_pages
		routes = []
		try:
			items = paginator.page(page)
		except PageNotAnInteger:
			items = paginator.page(1)
		except EmptyPage:
			items = []

		for item in items:
			routes.append(item.to_dict())
		return { 'items' : routes, 'count' : count, 'num_pages' : num_pages, 'page' : page }

	def get(self, request):
		return JsonResponse(request, self.to_json())

	def post(self, request):
		return JsonResponse(request, self.to_json())


@method_decorator(csrf_exempt, name='dispatch')
class CreateJsonView(PermissionView):

	def get(self, request):
		return JsonResponse(request, {})

	def post(self, request):
		organization=self.get_current_organization()
		route = self.request.POST.get('route')
		driver_id = self.request.POST.get('driver_id')
		vehicle_id = self.request.POST.get('vehicle_id')
		driver = Driver.objects.get(pk=driver_id, organization=organization)
		vehicle = Vehicle.objects.get(pk=vehicle_id, organization=organization)
		route = json.loads(route)
		steps = []
		for step in route.get('steps'):
			if step.get('type') == 'start':
				if step.get("location"):
					start_lng, start_lat = step.get("location")

			if step.get('type').lower() == 'pickup' or step.get('type').lower() == "delivery":
				steps.append(step)

			if step.get('type') == 'end':
				if step.get("location"):
					end_lng, end_lat = step.get("location")

		route_obj = models.Route()
		route_obj.end_lat = end_lat
		route_obj.end_lng = end_lng
		route_obj.start_lat = start_lat
		route_obj.start_lng = start_lng
		route_obj.details = route
		route_obj.driver = driver
		route_obj.vehicle = vehicle
		route_obj.added_by = request.user
		route_obj.modified_by = request.user
		route_obj.organization = organization
		route_obj.cost = route.get("cost")
		route_obj.geometry = route.get("geometry")
		route_obj.distance = route.get("distance")
		route_obj.duration = route.get("duration")
		route_obj.save()

		for step in steps:
			order_id = step.get("id")
			order = Order.objects.get(pk=order_id, organization=organization)
			order.rider = driver
			order.save()
			route_item = models.RouteItem()

			route_item.distance = step.get("distance")
			route_item.duration = step.get("duration")
			route_item.service_time = step.get("service")
			route_item.waiting_time = step.get("waiting_time")
			route_item.route = route_obj
			route_item.order = order

			if step.get("location"):
				lng, lat = step.get("location")
				route_item.lat = lat
				route_item.lng = lng

			if step.get("arrival"):
				arrival = int(step.get("arrival"))
				route_item.eta = timezone.make_aware(datetime.fromtimestamp(arrival))

			if step.get('type') == 'pickup':
				route_item._type = models.RouteItem.PICK_UP
			if step.get('type') == 'delivery':
				route_item._type = models.RouteItem.DROP_OFF


			route_item.save()

			route_obj.orders.add(order)
		route_obj.order_count = RouteItem.objects.filter(route=route_obj).distinct('order').count()
		route_obj.save()

		return JsonResponse(request, {'id' : route_obj.pk})
