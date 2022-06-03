from sms.tasks import order_assign_sms, order_start_sms, order_complete_sms
from api.utils import new_assignment_driver_push
from organization.models import Organization, OrganizationMpesaDetails
from django.core.paginator import PageNotAnInteger
from django.db.models import Avg, Count, Min, Sum
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from order.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

from order.models import Order, OrderItem
from driver.models import Driver
from api.views import APIView
from route.models import Route
import validators

from organization.mpesa import push_request
from organization.kopokopo import push_stk_request


class DriverStatsView(APIView):
	def get(self, request, format=None):
		return self.process_request(request,format)

	def post(self, request, format=None):
		return self.process_request(request,format)

	def process_request(self, request, format=None):
		user = request.user
		s = self.request.GET.get('s', '')
		page = self.request.GET.get('page', 1)
		states = self.request.GET.getlist('state')
		order = self.request.GET.get('order', 'desc')
		per_page = self.request.GET.get('per_page', 50)
		order_by = self.request.GET.get('order_by', 'datetime_ordered')
		organization_id = self.request.GET.get('organization_id', None)

		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		try:
			driver = Driver.objects.get(
				phone_number=driver_auth.phone_number,
				organization__pk=organization_id,
			)
		except Driver.DoesNotExist:
			return self.send_error('Invalid organization')

		organization = driver.organization

		today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		before_today = today - timedelta(days=7)

		end_date = self.request.GET.get('end_date', today.strftime("%b %d, %Y"))
		start_date = self.request.GET.get('start_date', before_today.strftime("%b %d, %Y"))
		_end_date = timezone.make_aware(datetime.strptime(end_date.strip(), '%b %d, %Y'))
		_start_date = timezone.make_aware(datetime.strptime(start_date.strip(), '%b %d, %Y'))
		date_range = [_start_date,_end_date+timedelta(days=1)]

		state_in = [1,2,3,4,5,6,7,8,9,10,11,12,13] if not validators.truthy(states) else states
		state_in = list(map(int, state_in))

		_order = '-' if not validators.truthy(order) or order == 'desc' else ''
		_order_by = 'datetime_ordered' if not validators.truthy(order_by) else order_by
		_order_by =  f'{_order}{_order_by}'
		per_page = 50 if not validators.truthy(per_page) else per_page

		total_orders = Order.objects.filter(
			datetime_ordered__range = date_range,
			organization = organization,
			rider = driver
		).count()

		orders_completed = Order.objects.filter(
			datetime_ordered__range = date_range,
			organization = organization,
			state__in = [7],
			rider = driver
		).count()

		orders_failed = Order.objects.filter(
			datetime_ordered__range = date_range,
			organization = organization,
			state__in = [5,6],
			rider = driver
		).count()

		orders_in_progress = Order.objects.filter(
			datetime_ordered__range = date_range,
			organization = organization,
			state__in = [1,2,3,4,8,9,10,11,12,13],
			rider = driver
		).count()

		rt = Order.objects.filter(
			datetime_ordered__range = date_range,
			organization = organization,
			rating__gt = 0,
			rider = driver
		).aggregate(_avg=Avg(Order.rating.field.name))
		average_rating = rt['_avg']

		s_date, e_date = date_range
		res = {
			'period' : {
				'start_date' : s_date.strftime("%b %d, %Y"),
				'end_date' : e_date.strftime("%b %d, %Y"),
			},
			'organization' : {
				'ID' : organization.pk,
				'name' : organization.name
			},
			'orders_in_progress' : orders_in_progress,
			'orders_completed' : orders_completed,
			'orders_failed' : orders_failed,
			'total_orders' : total_orders,
			'rating': average_rating,

		}
		return self.send_response(res)


class RouteView(APIView):

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
			routes.append(item.to_dict2())

		res = { 'items' : routes, 'count' : count, 'num_pages' : num_pages, 'page' : page }
		return self.send_response(res)



class IndexView(APIView):
	def get(self, request, pk, format=None):
		return self.process_request(request,pk)

	def post(self, request, pk, format=None):
		return self.process_request(request,pk)

	def process_request(self, request, pk):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		try:
			order = Order.objects.get(pk=pk,rider__phone_number=driver_auth.phone_number)
		except Order.DoesNotExist:
			return self.send_error('Order not found')

		return self.send_response(order.to_dict())


class FilterView(APIView):
	def get(self, request, format=None):
		return self.process_request(request,format)

	def post(self, request, format=None):
		return self.process_request(request,format)

	def process_request(self, request, format=None):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		s = self.request.GET.get('s', '')
		page = self.request.GET.get('page', 1)
		states = self.request.GET.getlist('state')
		order = self.request.GET.get('order', 'desc')
		per_page = self.request.GET.get('per_page', 50)
		order_by = self.request.GET.get('order_by', 'created')
		organization_id = self.request.GET.get('organization_id', None)

		# filter by preffered_delivery_date preffered_delivery_period
		preffered_delivery_date = self.request.GET.get('preffered_delivery_date', '')
		preffered_delivery_period = self.request.GET.get('preffered_delivery_period', 1)


		datetime_failed = self.request.GET.get('datetime_failed', '')
		datetime_completed = self.request.GET.get('datetime_completed', '')

		if not validators.truthy(organization_id):
			return self.send_error('Invalid organization')

		try:
			organization_id = int(organization_id)
		except ValueError:
			return self.send_error('Invalid organization')

		try:
			driver = Driver.objects.get(
				phone_number=driver_auth.phone_number,
				organization__pk=organization_id
			)
		except Driver.DoesNotExist:
			return self.send_error('Invalid organization')

		organization = driver.organization


		today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		before_today = today - timedelta(days=60)

		end_date = self.request.GET.get('end_date', today.strftime("%b %d, %Y"))
		start_date = self.request.GET.get('start_date', before_today.strftime("%b %d, %Y"))
		_end_date = timezone.make_aware(datetime.strptime(end_date.strip(), '%b %d, %Y'))
		_start_date = timezone.make_aware(datetime.strptime(start_date.strip(), '%b %d, %Y'))
		date_range = [_start_date,_end_date+timedelta(days=1)]

		state_in = [1,2,3,4,5,6,7,8,9,10,11,12] if not validators.truthy(states) else states
		state_in = list(map(int, state_in))

		_order = '-' if not validators.truthy(order) or order == 'desc' else ''
		_order_by = 'created' if not validators.truthy(order_by) else order_by
		_order_by =  f'{_order}{_order_by}'
		per_page = 50 if not validators.truthy(per_page) else per_page


		q = Order.objects.filter(
			rider = driver,
			state__in=state_in,
			created__range=date_range,
			organization=organization
		)

		if validators.truthy(preffered_delivery_date):
			_preffered_delivery_date = timezone.make_aware(datetime.strptime(preffered_delivery_date.strip(), '%Y-%m-%d'))
			q = Order.objects.filter(
				rider = driver,
				state__in=state_in,
				created__range=date_range,
				organization=organization,
				preffered_delivery_date = _preffered_delivery_date,
				preffered_delivery_period = preffered_delivery_period
			)

		if validators.truthy(datetime_failed):
			_datetime_failed  = datetime.strptime(datetime_failed.strip(), '%Y-%m-%d').date()
			q = Order.objects.filter(
				rider = driver,
				state__in=state_in,
				created__range=date_range,
				organization=organization,
				datetime_failed__date = _datetime_failed
			)

		if validators.truthy(datetime_completed):
			_datetime_completed  = datetime.strptime(datetime_completed.strip(), '%Y-%m-%d').date()
			q = Order.objects.filter(
				rider = driver,
				state__in=state_in,
				created__range=date_range,
				organization=organization,
				datetime_completed__date = _datetime_completed
			)

		if validators.truthy(s):
			s = s.strip()
			q = Order.objects.filter(
				(
					Q(pk__icontains=s) |
					Q(ref__icontains=s)
				)
				& Q(rider = driver)
				& Q(state__in=state_in)
				& Q(created__range=date_range)
				& Q(organization=organization)
			)

		query = q.prefetch_related().order_by(_order_by)
		paginator = Paginator(query, per_page)
		try:
			items = paginator.page(page)
		except PageNotAnInteger:
			items = paginator.page(1)
		except EmptyPage:
			items = []

		results = []
		for item in items:
			results.append(item.to_dict())

		return self.send_response({'count' : str(paginator.count), 'page' : page, 'items' : results})



class FilterAssignView(APIView):
	def get(self, request, format=None):
		return self.process_request(request,format)

	def post(self, request, format=None):
		return self.process_request(request,format)

	def process_request(self, request, format=None):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		s = self.request.GET.get('s', '')
		page = self.request.GET.get('page', 1)
		states = self.request.GET.getlist('state')
		order = self.request.GET.get('order', 'desc')
		per_page = self.request.GET.get('per_page', 50)
		order_by = self.request.GET.get('order_by', 'created')
		organization_id = self.request.GET.get('organization_id', None)

		# filter by preffered_delivery_date preffered_delivery_period
		preffered_delivery_date = self.request.GET.get('preffered_delivery_date', '')
		preffered_delivery_period = self.request.GET.get('preffered_delivery_period', 1)

		datetime_failed = self.request.GET.get('datetime_failed', '')
		datetime_completed = self.request.GET.get('datetime_completed', '')

		if not validators.truthy(organization_id):
			return self.send_error('Invalid organization')

		try:
			organization_id = int(organization_id)
		except ValueError:
			return self.send_error('Invalid organization')

		try:
			driver = Driver.objects.get(
				phone_number=driver_auth.phone_number,
				organization__pk=organization_id
			)
		except Driver.DoesNotExist:
			return self.send_error('Invalid organization')

		organization = driver.organization


		today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		before_today = today - timedelta(days=60)

		end_date = self.request.GET.get('end_date', today.strftime("%b %d, %Y"))
		start_date = self.request.GET.get('start_date', before_today.strftime("%b %d, %Y"))
		_end_date = timezone.make_aware(datetime.strptime(end_date.strip(), '%b %d, %Y'))
		_start_date = timezone.make_aware(datetime.strptime(start_date.strip(), '%b %d, %Y'))
		date_range = [_start_date,_end_date+timedelta(days=1)]

		state_in = [1,2,3,4,5,6,7,8,9,10,11,12] if not validators.truthy(states) else states
		state_in = list(map(int, state_in))

		_order = '-' if not validators.truthy(order) or order == 'desc' else ''
		_order_by = 'created' if not validators.truthy(order_by) else order_by
		_order_by =  f'{_order}{_order_by}'
		per_page = 50 if not validators.truthy(per_page) else per_page


		q = Order.objects.filter(
			state__in=state_in,
			created__range=date_range,
			organization=organization
		)

		if validators.truthy(preffered_delivery_date):
			_preffered_delivery_date = timezone.make_aware(datetime.strptime(preffered_delivery_date.strip(), '%Y-%m-%d'))
			q = Order.objects.filter(
				state__in=state_in,
				created__range=date_range,
				organization=organization,
				preffered_delivery_date = _preffered_delivery_date,
				preffered_delivery_period = preffered_delivery_period
			)

		if validators.truthy(datetime_failed):
			_datetime_failed  = datetime.strptime(datetime_failed.strip(), '%Y-%m-%d').date()
			q = Order.objects.filter(
				state__in=state_in,
				created__range=date_range,
				organization=organization,
				datetime_failed__date = _datetime_failed
			)

		if validators.truthy(datetime_completed):
			_datetime_completed  = datetime.strptime(datetime_completed.strip(), '%Y-%m-%d').date()
			q = Order.objects.filter(
				state__in=state_in,
				created__range=date_range,
				organization=organization,
				datetime_completed__date = _datetime_completed
			)

		if validators.truthy(s):
			s = s.strip()
			q = Order.objects.filter(
				(
					Q(pk__icontains=s) |
					Q(ref__icontains=s)
				)
				& Q(state__in=state_in)
				& Q(organization=organization)
			)

		query = q.prefetch_related().order_by(_order_by)
		paginator = Paginator(query, per_page)
		try:
			items = paginator.page(page)
		except PageNotAnInteger:
			items = paginator.page(1)
		except EmptyPage:
			items = []

		results = []
		for item in items:
			results.append(item.to_dict())

		return self.send_response({'count' : str(paginator.count), 'page' : page, 'items' : results})

class AcceptOrderView(APIView):
	def get(self, request, format=None):
		return self.send_error('Method not allowed')

	def post(self, request, format=None):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		self.handle_params()

		orders = []
		ids = self.get_param("ids")
		if not validators.truthy(ids):
			return self.send_error('No orders')

		for _id in ids:
			try:
				order = Order.objects.get(pk=_id,rider__phone_number=driver_auth.phone_number)

				if not validators.truthy(order.datetime_accepted):
					order.datetime_accepted = timezone.now()
					order.save()
					order.refresh_from_db()

				if order.state < Order.DISPATCHED:
					order.state = Order.DISPATCHED
					order.save()
					order.refresh_from_db()

				order.refresh_from_db()
				orders.append(order.to_dict())
			except Order.DoesNotExist:
				pass

		return self.send_response(orders)


class StartOrderView(APIView):
	def get(self, request, format=None):
		return self.send_error('Method not allowed')

	def post(self, request, format=None):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		self.handle_params()

		orders = []
		ids = self.get_param("ids")
		if not validators.truthy(ids):
			return self.send_error('No orders')

		for _id in ids:
			try:
				order = Order.objects.get(pk=_id,rider__phone_number=driver_auth.phone_number)

				if not validators.truthy(order.datetime_accepted):
					order.datetime_accepted = timezone.now()
					order.save()
					order.refresh_from_db()

				if not validators.truthy(order.datetime_started):
					order.datetime_started = timezone.now()
					order.save()
					order.refresh_from_db()
					order_start_sms(order)

				if order.state < Order.DISPATCHED:
					order.state = Order.DISPATCHED
					order.save()
					order.refresh_from_db()

				orders.append(order.to_dict())
			except Order.DoesNotExist:
				pass

		return self.send_response(orders)

class ArrivedOrderView(APIView):
	def get(self, request, pk, format=None):
		return self.process_request(request,pk)

	def post(self, request, pk, format=None):
		return self.process_request(request,pk)

	def process_request(self, request, pk):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		try:
			order = Order.objects.get(pk=pk,rider__phone_number=driver_auth.phone_number)

			if not validators.truthy(order.datetime_arrived):
				order.datetime_arrived = timezone.now()
				order.save()
				order.refresh_from_db()

			if order.state < Order.ARRAVAL_AT_CLIENT:
				order.state = Order.ARRAVAL_AT_CLIENT
				order.save()
				order.refresh_from_db()

		except Order.DoesNotExist:
			return self.send_error('Order does not exist')

		return self.send_response(order.to_dict())


class ChangePayView(APIView):
	def get(self, request, pk, format=None):
		return self.send_error('Method not allowed')

	def post(self, request, pk, format=None):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		try:
			order = Order.objects.get(pk=pk,rider__phone_number=driver_auth.phone_number)
		except Order.DoesNotExist:
			return self.send_error('Order does not exist')

		payment_method = self.get_param("payment_method")
		if not validators.truthy(payment_method):
			raise ParseError('Invalid payment method')


		try:
			payment_method = int(payment_method)
		except ValueError:
			raise ParseError('Invalid payment method')

		if payment_method < 1 or payment_method > 4:
			raise ParseError('Invalid payment method')


		order.payment_method = payment_method
		order.save()

		return self.send_response(order.to_dict())


class CompleteOrderView(APIView):
	def get(self, request, format=None):
		return self.send_error('Method not allowed')

	def post(self, request, pk, format=None):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		lat = self.get_param("lat")
		lng = self.get_param("lng")

		items = self.get_param("items")
		signature = self.get_param("signature")
		pod_images = self.get_param("pod_images")
		payment_notes = self.get_param("payment_notes")

		try:
			order = Order.objects.get(pk=pk,rider__phone_number=driver_auth.phone_number)

			if not validators.truthy(order.datetime_completed):
				order.datetime_completed = timezone.now()
				order.save()
				order_complete_sms(order)

				if validators.truthy(lat) and validators.truthy(lng):
					order.complete_lat = lat
					order.complete_lng = lng
					order.save()

				if validators.truthy(signature):
					order.signature = signature
					order.save()

				if validators.truthy(pod_images):
					order.pod_images = pod_images
					order.save()

			if order.state < Order.DELIVERED:
				order.state = Order.DELIVERED
				order.save()

			if validators.truthy(items):
				for item in items:
					try:
						order_item = OrderItem.objects.get(pk=item)
						order_item.paid = True
						order_item.save()
					except OrderItem.DoesNotExist:
						pass

			pn = order.payment_notes if validators.truthy(order.payment_notes) else ""
			payment_notes = payment_notes if validators.truthy(payment_notes) else ""
			order.payment_notes = f'{pn} {payment_notes}'
			order.save()


			order.refresh_from_db()

		except Order.DoesNotExist:
			return self.send_error('Order does not exist')

		return self.send_response(order.to_dict())


class FailedOrderView(APIView):
	def get(self, request, pk, format=None):
		return self.send_error('Method not allowed')

	def post(self, request, pk, format=None):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		lat = self.get_param("lat")
		lng = self.get_param("lng")
		reason = self.get_param("reason")


		try:
			order = Order.objects.get(pk=pk,rider__phone_number=driver_auth.phone_number)

			if not validators.truthy(order.datetime_failed):
				order.datetime_failed = timezone.now()
				order.save()
				order.refresh_from_db()

				if validators.truthy(lat) and validators.truthy(lng):
					order.complete_lat = lat
					order.complete_lng = lng
					order.save()

				if validators.truthy(reason):
					order.failure_reason = reason
					order.save()

			if order.state < Order.FAILED_AT_CLIENT:
				order.state = Order.FAILED_AT_CLIENT
				order.save()
				order.refresh_from_db()

		except Order.DoesNotExist:
			return self.send_error('Order does not exist')

		return self.send_response(order.to_dict())


class SelfAssignView(APIView):
	def get(self, request, *args, **kwargs):
		return self.send_error('Method not allowed')

	def post(self,request, *args, **kwargs):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		order_id = self.get_param("order_id")

		organization_id = self.get_param('organization_id')

		if not validators.truthy(organization_id):
			return self.send_error('Invalid organization')

		try:
			organization_id = int(organization_id)
		except ValueError:
			return self.send_error('Invalid organization')

		try:
			organization = Organization.objects.get(pk=organization_id)
		except ValueError:
			return self.send_error('Organization does not exist')

		if(organization.allow_driver_to_self_assign_orders):

			try:
				order = Order.objects.get(pk=order_id, organization__pk=organization_id, state__in = [Order.DRAFT, Order.SUBMITTED_PENDING_VENDOR_PICK_UP], rider=None)
			except:
				return self.send_error('Order does not exist')

			rider = Driver.objects.get(phone_number=driver_auth.phone_number, organization__pk=organization_id)
			order.rider=rider
			order.state = Order.SUBMITTED_PENDING_FOWARD_DELIVERY
			order.save()
			order_assign_sms(order)
			new_assignment_driver_push(order)

			return self.send_response(order.to_dict())
		else:
			return self.send_error('This organization does not allow self assignment of orders')

class SendSTKPush(APIView):
	def get(self, request):
		return self.send_error('Method not allowed')

	def post(self, request):
		driver_auth = self.get_driver_auth()
		if driver_auth is None:
			return self.send_error('Invalid authentication')

		order_id =  self.get_param("order_id")
		amount =  self.get_param('amount')
		phone_number = self.get_param('phone_number')

		try:
			order = Order.objects.get(pk=order_id, rider__phone_number=driver_auth.phone_number)
		except Order.DoesNotExist:
			return self.send_error('Order does not exist')

		organization = order.organization

		try:
			mpesa_details = OrganizationMpesaDetails.objects.get(organization=organization)
		except OrganizationMpesaDetails.DoesNotExist:
			return self.send_error('mpesa details does not exist')

		if mpesa_details.implementation == 1:
			transaction_description = f'payment for {order_id}'
			ret_val = push_request(mpesa_details.consumer_key, mpesa_details.consumer_secret, mpesa_details.pass_key, mpesa_details.business_short_code, float(amount), phone_number, account_reference=str(order_id), transaction_description=transaction_description)
		else:
			ret_val = push_stk_request(mpesa_details.client_id, mpesa_details.client_secret, amount, mpesa_details.till_number, phone_number, order_id)
			print(ret_val)

		return self.send_response(ret_val)


class OrderHistory(APIView):
	# Return a list of orders that have the driver id in them
	def get(self, request, format=None):
		previous_orders = []
		return Response(previous_orders)
