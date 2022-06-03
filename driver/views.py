from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import DurationField, F, ExpressionWrapper
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.core.paginator import PageNotAnInteger
from django.views.generic.edit import DeleteView
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
from order.models import Order
from route.models import Route
from . import models
from . import forms
import validators

class IndexView(ListView, PermissionView):
	template_name = "driver/index.html"

	def get_queryset(self):
		s = self.request.GET.get('s', '').strip()
		page = self.request.GET.get('page', 1)
		order = self.request.GET.get('order', 'desc')
		per_page = self.request.GET.get('per_page', 50)
		end_date = self.request.GET.get('end_date', '')
		start_date = self.request.GET.get('start_date', '')
		order_by = self.request.GET.get('order_by', 'modified')

		_order = '-' if not validators.truthy(order) or order == 'desc' else ''
		_order_by = 'modified' if not validators.truthy(order_by) else order_by
		_order_by =  f'{_order}{_order_by}'
		per_page = 50 if not validators.truthy(per_page) else per_page

		q = models.Driver.objects.filter(deleted=False,organization=self.get_current_organization())
		if validators.truthy(s):
			q = models.Driver.objects.filter(
				(

					Q(first_name__icontains=s) |
					Q(last_name__icontains=s) |
					Q(phone_number__icontains=s)
				)
				& Q(deleted=False)
				& Q(organization=self.get_current_organization())
			)

		query = q.prefetch_related().order_by(_order_by)
		paginator = Paginator(query, per_page)
		try:
			items = paginator.page(page)
		except PageNotAnInteger:
			items = paginator.page(1)
		except EmptyPage:
			items = paginator.page(paginator.num_pages)

		items.current_order = order
		items.current_order_by = order_by

		try:
			items.per_page = int(per_page)
		except ValueError:
			items.per_page = 50

		items.current_search_term = s
		items.order_count = q.count()
		return items

class CreateView(TemplateView, PermissionView):
	template_name = "driver/create.html"
	success_url = reverse_lazy("driver:index")

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['name'] = self.request.POST.get("name", "")
		context['reg_no'] = self.request.POST.get("reg_no", "")
		context['phone_number'] = self.request.POST.get("phone_number", "")
		return context

	def post(self,request, *args, **kwargs):
		name = self.request.POST.get("name", "")
		reg_no = self.request.POST.get("reg_no", "")
		phone_number = self.request.POST.get("phone_number", "")

		try:
			models.Driver.objects.get(phone_number=phone_number,organization=self.get_current_organization())
			messages.add_message(request, messages.ERROR, f'Driver already exists')
			return self.get(request, *args, **kwargs)
		except models.Driver.DoesNotExist:
			pass

		models.Driver.objects.create_new(phone_number, self.get_current_organization(), name, reg_no)
		return HttpResponseRedirect(self.success_url)

class DriverDeleteView(DeleteView, PermissionView):
	template_name = "driver/delete.html"
	success_url = reverse_lazy("driver:index")

	def get_object(self):
		return get_object_or_404(
			models.Driver,
			pk=self.kwargs["pk"],
			organization=self.get_current_organization()
		)

	def delete(self, request, *args, **kwargs):
		driver = self.get_object()
		driver.deleted = True
		driver.save()
		return HttpResponseRedirect(reverse_lazy("driver:index"))


class EditView(DetailView, PermissionView):
	template_name = "driver/edit.html"

	def get_object(self):
		return get_object_or_404(
			models.Driver,
			pk=self.kwargs["pk"],
			organization=self.get_current_organization()
		)

	def post(self,request, *args, **kwargs):
		_object = self.get_object()
		name = self.request.POST.get("name", "")
		reg_no = self.request.POST.get("reg_no", "")
		phone_number = int(self.request.POST.get("phone_number", _object.phone_number))

		if phone_number != _object.phone_number:
			try:
				models.Driver.objects.get(phone_number=phone_number,organization=self.get_current_organization())
				messages.add_message(request, messages.ERROR, f'Driver already exists')
				return self.get(request, *args, **kwargs)
			except models.Driver.DoesNotExist:
				pass

		_object.update(name, phone_number, reg_no)
		return HttpResponseRedirect(reverse_lazy("driver:index", kwargs={'pk' : _object.pk }))



class DriverView(ListView, PermissionView):
	template_name = "driver/detail.html"

	def get_queryset(self):
		try:
		    driver = models.Driver.objects.get(
				pk=self.kwargs['pk'],
				organization=self.get_current_organization()
			)
		except models.Driver.DoesNotExist:
		    raise Http404("Driver does not exist")

		s = self.request.GET.get('s', '')
		page = self.request.GET.get('page', 1)
		order = self.request.GET.get('order', 'desc')
		per_page = self.request.GET.get('per_page', 50)
		order_by = self.request.GET.get('order_by', 'datetime_ordered')

		_order = '-' if not validators.truthy(order) or order == 'desc' else ''
		_order_by = 'datetime_ordered' if not validators.truthy(order_by) else order_by
		_order_by =  f'{_order}{_order_by}'
		per_page = 50 if not validators.truthy(per_page) else per_page

		today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		before_today = today - timedelta(days=7)

		end_date = self.request.GET.get('end_date', today.strftime("%b %d, %Y"))
		start_date = self.request.GET.get('start_date', before_today.strftime("%b %d, %Y"))
		_end_date = timezone.make_aware(datetime.strptime(end_date.strip(), '%b %d, %Y'))
		_start_date = timezone.make_aware(datetime.strptime(start_date.strip(), '%b %d, %Y'))
		date_range = [_start_date,_end_date+timedelta(days=1)]

		q = Order.objects.filter(
			rider=driver,
			datetime_ordered__range=date_range,
			organization=self.get_current_organization(),
		)
		if validators.truthy(s):
			s = s.strip()
			q = Order.objects.filter(
				(
					Q(pk__icontains=s) |
					Q(ref__icontains=s)|
					Q(review__icontains=s)|
					Q(rider__last_name__icontains=s)|
					Q(rider__first_name__icontains=s)|
					Q(ref__icontains=s)
				)
				& Q(rider=driver)
				& Q(datetime_ordered__range=date_range)
				& Q(organization=self.get_current_organization())
			)

		query = q.exclude(rating__isnull=True).prefetch_related().order_by(_order_by)
		paginator = Paginator(query, per_page)
		try:
			items = paginator.page(page)
		except PageNotAnInteger:
			items = paginator.page(1)
		except EmptyPage:
			items = paginator.page(paginator.num_pages)


		items.current_order = order
		items.current_order_by = order_by
		items.current_end_date = end_date
		items.current_start_date = start_date
		items.driver = driver

		try:
			items.per_page = int(per_page)
		except ValueError:
			items.per_page = 50

		items.current_search_term = s.strip()

		items.order_count = q.count()

		items.time_now = timezone.now()

		items.total_orders = Order.objects.filter(rider=driver, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
		items.in_progress_orders = Order.objects.filter(rider=driver, state__lte=Order.ARRAVAL_AT_CLIENT, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
		items.failed_orders = Order.objects.filter(rider=driver, state__lte=Order.FAILED_AT_CLIENT, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
		items.completed_orders = Order.objects.filter(rider=driver, state__lte=Order.DELIVERED, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()

		items.r5_count = Order.objects.filter(rider=driver, rating__gte=5.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
		items.r4_count = Order.objects.filter(rider=driver, rating__gte=4.0, rating__lt=5.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
		items.r3_count = Order.objects.filter(rider=driver, rating__gte=3.0, rating__lt=4.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
		items.r2_count = Order.objects.filter(rider=driver, rating__gte=2.0, rating__lt=3.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
		items.r1_count = Order.objects.filter(rider=driver, rating__gt=0.0, rating__lt=2.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
		items.rating_count = Order.objects.filter(rider=driver, rating__gt=0.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()


		items.h_0_1hrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=0),timedelta(seconds=3600)]).count()

		items.h_1_2hrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=3601),timedelta(seconds=7200)]).count()

		items.h_2_3hrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=7201),timedelta(seconds=10800)]).count()

		items.h_3_4hrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=10801),timedelta(seconds=14400)]).count()

		items.h_4_6hrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=14401),timedelta(seconds=21600)]).count()

		items.h_6_8hrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=21601),timedelta(seconds=28800)]).count()

		items.h_8_12hrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=28801),timedelta(seconds=43200)]).count()

		items.h_12_24hrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=43201),timedelta(seconds=86400)]).count()

		items.h_otherHrs = Order.objects.annotate(
			diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(Order.datetime_ordered.field.name), output_field=DurationField())
		).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__gte=timedelta(seconds=86401)).count()

		return items

@method_decorator(xframe_options_sameorigin, name='dispatch')
class DriverTrackingIframeView(ListView, PermissionView):
	template_name = "driver/tracking_iframe.html"
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['map_api'] = self.get_map_key()

		return context

	def get_queryset(self):
		return models.Driver.objects.filter(deleted=False,organization=self.get_current_organization())


@method_decorator(xframe_options_sameorigin, name='dispatch')
class DriverOrdersIframeView(ListView, PermissionView):
	template_name = "driver/orders_iframe.html"

	def get_queryset(self):
		page = self.request.GET.get('page', 1)
		per_page = self.request.GET.get('per_page', 200)
		driver_id = self.request.GET.get("driver_id", None)

		order_id = self.request.GET.get("order_id", None)
		if validators.truthy(order_id):
			try:
				order = Order.objects.get(
					pk=order_id,
					rider__pk=driver_id,
					state__lte=Order.ARRAVAL_AT_CLIENT,
					organization=self.get_current_organization()
				)
				order.state = Order.CANCELLED
				order.datetime_failed = timezone.now()
				order.failure_reason = f'Failed by Admin - {self.request.user.full_names()}'
				order.save()
				messages.add_message(self.request, messages.ERROR, f'Order #{order.pk} has been cancelled')
			except Order.DoesNotExist:
				pass

		query = Order.objects.filter(
			rider__pk=driver_id,
			state__lte=Order.ARRAVAL_AT_CLIENT,
			organization=self.get_current_organization()
		).order_by('-modified')
		paginator = Paginator(query, per_page)
		try:
			items = paginator.page(page)
		except PageNotAnInteger:
			items = paginator.page(1)
		except EmptyPage:
			items = paginator.page(paginator.num_pages)
		return items


class DriversJsonView(PermissionView):
	def get_paginator(self):
		page = self.request.GET.get('page', 1)
		per_page = self.request.GET.get('per_page', 50)
		print(self.get_current_organization())
		q = models.Driver.objects.filter(
			pk__in= Order.objects.filter(
				rider__isnull=False,
				organization=self.get_current_organization()
			).distinct('rider').values('rider')
		).order_by('-modified')
		print(q.count())
		return (Paginator(q, per_page), page)

	def to_json(self):
		paginator, page = self.get_paginator()
		count = paginator.count
		num_pages = paginator.num_pages
		drivers = []
		try:
			items = paginator.page(page)
		except PageNotAnInteger:
			items = paginator.page(1)
		except EmptyPage:
			items = []

		for item in items:
			driver = item.to_dict()
			driver['assigned_orders'] = Order.objects.filter(
				rider=item,
				state__lte=Order.ARRAVAL_AT_CLIENT,
				organization=self.get_current_organization()
			).count()
			driver['started_orders'] = Order.objects.filter(
				rider=item,
				datetime_started__isnull=False,
				organization=self.get_current_organization()
			).count()
			orders = []
			for order in Order.objects.filter(rider=item,state__lte=Order.ARRAVAL_AT_CLIENT,organization=self.get_current_organization()):
				orders.append(order.to_dict())
			driver['orders'] = orders
			drivers.append(driver)
		return {'items' : drivers, 'count' : count, 'num_pages' : num_pages, 'page' : page}

	def get(self, request):
		return JsonResponse(request, self.to_json())

	def post(self, request):
		return JsonResponse(request, self.to_json())
