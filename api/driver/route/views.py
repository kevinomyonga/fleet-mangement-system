from sms.tasks import order_assign_sms, order_start_sms, order_complete_sms
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from datetime import datetime, timedelta
from django.utils import timezone

from order.models import Order, OrderItem
from route.models import Route, RouteItem
from driver.models import Driver
from api.views import APIView
import validators

class StartRouteView(APIView):
	def get(self, request, pk, format=None):
		return self.process_request(request,pk)

	def post(self, request, pk, format=None):
		return self.process_request(request,pk)

	def process_request(self, request, pk):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		try:
			route = Route.objects.get(pk=pk)
		except Route.DoesNotExist:
			return self.send_error('Invalid route')

		try:
			driver = Driver.objects.get(
				organization=route.organization,
				phone_number=driver_auth.phone_number,
			)
		except Driver.DoesNotExist:
			return self.send_error('Invalid organization')

		Order.objects.filter(
			state__in=[5,6,7],
			pk__in=RouteItem.objects.filter(route=route).distinct('order').values_list("order")
		).update(state=Order.DISPATCHED)
		route.status = Route.STARTED
		route.save()

		return self.send_response(route.to_dict())

class RouteView(APIView):
	def get(self, request, pk, format=None):
		return self.process_request(request,pk)

	def post(self, request, pk, format=None):
		return self.process_request(request,pk)

	def process_request(self, request, pk):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		try:
			route = Route.objects.get(pk=pk)
		except Route.DoesNotExist:
			return self.send_error('Invalid route')

		try:
			driver = Driver.objects.get(
				organization=route.organization,
				phone_number=driver_auth.phone_number,
			)
		except Driver.DoesNotExist:
			return self.send_error('Invalid organization')

		return self.send_response(route.to_dict())


class RoutesView(APIView):

	def get_paginator(self, driver):
		page = self.request.GET.get('page', 1)
		per_page = self.request.GET.get('per_page', 50)
		organization_id = self.request.GET.get('organization_id', None)

		q = Route.objects.filter(
			driver = driver,
			organization__pk=organization_id,
		).order_by('-modified')
		return (Paginator(q, per_page), page)

	def get(self, request):
		return self.process_request(request)

	def post(self, request):
		return self.process_request(request)

	def process_request(self, request):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		organization_id = self.request.GET.get('organization_id', None)
		try:
			driver = Driver.objects.get(
				phone_number=driver_auth.phone_number,
				organization__pk=organization_id,
			)
		except Driver.DoesNotExist:
			return self.send_error('Invalid organization')

		paginator, page = self.get_paginator(driver)
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
			routes.append(item.to_dict_list())

		res = { 'items' : routes, 'count' : count, 'num_pages' : num_pages, 'page' : page }
		return self.send_response(res)
