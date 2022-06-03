from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import DurationField, F, ExpressionWrapper
from django.utils.decorators import method_decorator
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
from . import models
import validators

class VehicleJsonView(PermissionView):
	def get_paginator(self):
		page = self.request.GET.get('page', 1)
		per_page = self.request.GET.get('per_page', 50)
		q = models.Vehicle.objects.filter(
			organization=self.get_current_organization(),
		).order_by('-modified')
		return (Paginator(q, per_page), page)

	def to_json(self):
		paginator, page = self.get_paginator()
		count = paginator.count
		num_pages = paginator.num_pages
		vehicles = []
		try:
			items = paginator.page(page)
		except PageNotAnInteger:
			items = paginator.page(1)
		except EmptyPage:
			items = []

		for item in items:
			vehicles.append(item.to_dict())
		return { 'items' : vehicles, 'count' : count, 'num_pages' : num_pages, 'page' : page }

	def get(self, request):
		return JsonResponse(request, self.to_json())

	def post(self, request):
		return JsonResponse(request, self.to_json())

@method_decorator(xframe_options_sameorigin, name='dispatch')
class CreateView(TemplateView, PermissionView):
	template_name = "vehicle/create_iframe.html"
	success_url = reverse_lazy("vehicle:create-iframe")


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['hours'] = models.Vehicle.HOURS
		context['map_api'] = self.get_map_key()

		return context


	def post(self,request, *args, **kwargs):
		name = self.request.POST.get("name", "")
		width = self.request.POST.get("width", None)
		length = self.request.POST.get("length", None)
		height = self.request.POST.get("height", None)
		weight = self.request.POST.get("weight", None)
		reg_no = self.request.POST.get("reg_no", None)
		hours_end = self.request.POST.get("hours_end", None)
		hours_start = self.request.POST.get("hours_start", None)
		lat = self.request.POST.get("primary_address_lat", None)
		lng = self.request.POST.get("primary_address_lng", None)
		primary_address = self.request.POST.get("primary_address", None)

		vehicle = models.Vehicle()
		vehicle.lat = lat
		vehicle.lng = lng
		vehicle.width = width
		vehicle.weight = weight
		vehicle.length = length
		vehicle.height = height
		vehicle.name = name.strip()
		vehicle.reg_no = reg_no.strip()
		vehicle.address = primary_address
		vehicle.service_end = hours_end
		vehicle.service_start = hours_start

		vehicle.organization = self.get_current_organization()
		vehicle.added_by = self.request.user
		vehicle.modified_by = self.request.user
	
		vehicle.save()
		vehicle.refresh_from_db()
		messages.add_message(request, messages.INFO, f'Vehicle has been added')	
		return HttpResponseRedirect(self.success_url)
