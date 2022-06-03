from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

from organization.models import OrganizationUser
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from order.models import Order, OrderItem
from api.views import TokenAPIView
from types import SimpleNamespace
from . import replica_utils
from . import sync_utils
import validators, json

class ReplicateOrderView(TokenAPIView):

	def post(self, request, format=None):
		user = request.user
		self.handle_params()

		organization_id = self.request.GET.get('organization_id', None)
		if not validators.truthy(organization_id):
			raise ParseError('Invalid organization')

		try:
			organization_id = int(organization_id)
		except ValueError:
			raise ParseError('Invalid organization')

		try:
			organization_user = OrganizationUser.objects.get(
				user=user,
				organization__pk=organization_id
			)
		except OrganizationUser.DoesNotExist:
			raise ParseError('Invalid organization')

		organization = organization_user.organization

		order = replica_utils.process_order(
		    organization,
			json.loads(json.dumps(self.get_param("order")), object_hook=lambda d: SimpleNamespace(**d)),
			json.loads(json.dumps(self.get_param("rider")), object_hook=lambda d: SimpleNamespace(**d)),
			json.loads(json.dumps(self.get_param("failures")), object_hook=lambda d: SimpleNamespace(**d)),
			json.loads(json.dumps(self.get_param("order_items")), object_hook=lambda d: SimpleNamespace(**d))
		)
		return Response(order.to_dict())

class SyncOrderView(TokenAPIView):

	def post(self, request, format=None):
		user = request.user
		self.handle_params()

		organization_id = self.request.GET.get('organization_id', None)
		if not validators.truthy(organization_id):
			raise ParseError('Invalid organization')

		try:
			organization_id = int(organization_id)
		except ValueError:
			raise ParseError('Invalid organization')

		try:
			organization_user = OrganizationUser.objects.get(
				user=user,
				organization__pk=organization_id
			)
		except OrganizationUser.DoesNotExist:
			raise ParseError('Invalid organization')

		organization = organization_user.organization
		order = sync_utils.process_order(
		    organization, self.get_param("order"),
			self.get_param("shipping"), self.get_param("customer"),
			self.get_param("rider"), self.get_param("user"),
			self.get_param("failures")
		)
		return Response(order.to_dict())



class CreateView(TokenAPIView):


	def post(self, request, format=None):
		user = request.user
		self.handle_params()

		order = Order()
		organization_id = self.get_param("organization_id")
		if not validators.truthy(organization_id):
			raise ParseError('Invalid organization id')

		try:
			organization_user = OrganizationUser.objects.get(user=user,organization__pk=organization_id)
		except OrganizationUser.DoesNotExist:
			raise ParseError('Invalid organization id')

		organization = organization_user.organization

		order.organization = organization


		notes = self.get_param("notes")
		if not validators.truthy(notes):
			notes = ''
		else:
			notes = f'\r\n{notes}'

		order_ref = self.get_param("order_ref")
		if validators.truthy(order_ref):
			order_ref = order_ref.strip()
			try:
				Order.objects.get(ref=order_ref, organization=organization)
				raise ParseError('Order ref already exists')
			except Order.DoesNotExist:
				pass
			order.ref = order_ref

		order_sid = self.get_param("order_sid")
		if validators.truthy(order_sid):
			order_sid = order_sid.strip()
			try:
				Order.objects.get(ref=order_sid, organization=organization)
				raise ParseError('Order sid already exists')
			except Order.DoesNotExist:
				pass
			order.sid = order_sid

		pickup = self.get_param("pickup")
		if not validators.truthy(pickup):
			raise ParseError('Missing pickup details')


		try:
			pickup_address = pickup['location']['addresss']
		except (KeyError, ValueError, AttributeError) as e:
			raise ParseError('Missing pickup address')

		order.pickup_location_name = pickup_address

		try:
			pickup_lat = pickup['location']['coords']['lat']
			pickup_lng = pickup['location']['coords']['lng']
		except (KeyError, ValueError, AttributeError) as e:
			raise ParseError('Missing pickup coords')

		order.pickup_lat = pickup_lat
		order.pickup_lng = pickup_lng

		pickup_notes = pickup.get('notes')
		order.pickup_location_details = f'{pickup_notes} {notes}' if validators.truthy(pickup_notes) else notes

		try:
			pickup_apt = pickup['location']['apartment']
		except (KeyError, ValueError, AttributeError) as e:
			pickup_apt = None

		order.pickup_location_name_more = pickup_apt

		try:
			pickup_name = pickup['contact']['name']
			pickup_phone = pickup['contact']['phone_number']
		except (KeyError, ValueError, AttributeError) as e:
			raise ParseError('Missing pickup contact details')

		order.pickup_contact_name = pickup_name
		order.pickup_contact_phone_number = pickup_phone

		try:
			pickup_email = pickup['contact']['email']
		except (KeyError, ValueError, AttributeError) as e:
			pickup_email = None


		order.pickup_contact_email = pickup_email


		dropoff = self.get_param("dropoff")
		if not validators.truthy(dropoff):
			raise ParseError('Missing dropoff details')

		try:
			dropoff_address = dropoff['location']['addresss']
		except (KeyError, ValueError, AttributeError) as e:
			raise ParseError('Missing dropoff address')

		order.dropoff_location_name = dropoff_address

		try:
			dropoff_lat = dropoff['location']['coords']['lat']
			dropoff_lng = dropoff['location']['coords']['lng']
		except (KeyError, ValueError, AttributeError) as e:
			raise ParseError('Missing dropoff coords')

		order.dropoff_lat = dropoff_lat
		order.dropoff_lng = dropoff_lng

		dropoff_notes = dropoff.get('notes')
		order.dropoff_location_details = f'{dropoff_notes} {notes}' if validators.truthy(dropoff_notes) else notes

		try:
			dropoff_apt = dropoff['location']['apartment']
		except (KeyError, ValueError, AttributeError) as e:
			dropoff_apt = None

		order.dropoff_location_name_more = dropoff_apt

		try:
			dropoff_name = dropoff['contact']['name']
			dropoff_phone = dropoff['contact']['phone_number']
		except (KeyError, ValueError, AttributeError) as e:
			raise ParseError('Missing dropoff contact details')

		order.dropoff_contact_name = dropoff_name
		order.dropoff_contact_phone_number = dropoff_phone

		try:
			dropoff_email = dropoff['contact']['email']
		except (KeyError, ValueError, AttributeError) as e:
			dropoff_email = None


		order.dropoff_contact_email = dropoff_email

		price = self.get_param("price")
		if validators.truthy(price):
			try:
				price = float(price)
				order.price = price
			except ValueError:
				raise ParseError('Invalid price')

		width = self.get_param("width")
		if validators.truthy(width):
			try:
				width = float(width)
				order.width = width
			except ValueError:
				raise ParseError('Invalid width')


		length = self.get_param("length")
		if validators.truthy(length):
			try:
				length = float(length)
				order.length = length
			except ValueError:
				pass


		height = self.get_param("height")
		if validators.truthy(height):
			try:
				height = float(height)
				order.height = height
			except ValueError:
				raise ParseError('Invalid height')


		weight = self.get_param("weight")
		if validators.truthy(weight):
			try:
				weight = float(weight)
				order.weight = weight
			except ValueError:
				raise ParseError('Invalid weight')

		payment_method = self.get_param("payment_method")
		if validators.truthy(payment_method):
			try:
				payment_method = int(payment_method)
				order.payment_method = payment_method
			except ValueError:
				raise ParseError('Invalid payment method')

		prefered_delivery_date = self.get_param("prefered_delivery_date")
		if validators.truthy(prefered_delivery_date):
			try:
				order.preffered_delivery_date = datetime.strptime(prefered_delivery_date, '%m-%d-%Y').date()
			except (ValueError, TypeError) as e:
				raise ParseError('Invalid delivery date')

		prefered_delivery_time = self.get_param("prefered_delivery_time")
		if validators.truthy(prefered_delivery_time):
			try:
				prefered_delivery_time = int(prefered_delivery_time)
				order.prefered_delivery_time = prefered_delivery_time
			except ValueError:
				raise ParseError('Invalid delivery time, must be int, 1,2,3')

		try:
			_date_ordered = self.get_param("ordered_date")
			print(_date_ordered)
			if validators.truthy(_date_ordered):
				date_ordered = datetime.strptime(_date_ordered.strip(), '%Y-%m-%dT%H:%M:%S%Z')
				dt = timezone.make_aware(date_ordered, timezone=timezone.utc)
				order.datetime_ordered = dt
		except ValueError:
			raise ParseError('Invalid order date')

		order.added_by = user
		order.modified_by = user
		try:
			order.save()
		except Exception as e:
			raise ParseError(e)

		items = self.get_param("items")
		if validators.truthy(items):
			for item in items:
				price = item.get('price')
				name = item.get('name')
				if not validators.truthy(price) or not validators.truthy(name):
					continue
				order_item = OrderItem.objects.create(price=price, name=name)
				order.items.add(order_item)

		order.refresh_from_db()
		return Response(order.to_dict())


class CancelView(TokenAPIView):
	def get(self, request, pk, format=None):
		return self.process_request(request,pk)

	def post(self, request, pk, format=None):
		return self.process_request(request,pk)

	def process_request(self, request, pk):
		user = request.user
		try:
			order = Order.objects.get(pk=pk)
		except Order.DoesNotExist:
			raise ParseError('Order not found')

		try:
			OrganizationUser.objects.get(user=user,organization=order.organization)
		except OrganizationUser.DoesNotExist:
			raise ParseError('Order not found')

		order.state = Order.CANCELLED
		order.save()
		order.refresh_from_db()
		return Response(order.to_dict())


class IndexView(TokenAPIView):
	def get(self, request, pk, format=None):
		return self.process_request(request,pk)

	def post(self, request, pk, format=None):
		return self.process_request(request,pk)

	def process_request(self, request, pk):
		user = request.user
		try:
			order = Order.objects.get(pk=pk)
		except Order.DoesNotExist:
			raise ParseError('Order not found')

		try:
			OrganizationUser.objects.get(user=user,organization=order.organization)
		except OrganizationUser.DoesNotExist:
			raise ParseError('Order not found')

		return Response(order.to_dict())

class RefView(TokenAPIView):
	def get(self, request, format=None):
		return self.process_request(request)

	def post(self, request, pk, format=None):
		return self.process_request(request)

	def process_request(self, request):
		user = request.user
		order_ref = self.request.GET.get('order_ref', None)
		organization_id = self.request.GET.get('organization_id', None)
		if not validators.truthy(order_ref) or not validators.truthy(organization_id):
			raise ParseError('Invalid parameters')

		order_ref = order_ref.strip()
		organization_id = organization_id.strip()

		try:
			order = Order.objects.get(organization__pk=organization_id, ref=order_ref)
		except Order.DoesNotExist:
			raise ParseError('Order not found')

		try:
			OrganizationUser.objects.get(user=user,organization=order.organization)
		except OrganizationUser.DoesNotExist:
			raise ParseError('Order not found')

		return Response(order.to_dict())


class FilterView(TokenAPIView):
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
		if not validators.truthy(organization_id):
			raise ParseError('Invalid organization')

		try:
			organization_id = int(organization_id)
		except ValueError:
			raise ParseError('Invalid organization')

		try:
			organization_user = OrganizationUser.objects.get(
				user=user,
				organization__pk=organization_id
			)
		except OrganizationUser.DoesNotExist:
			raise ParseError('Invalid organization')

		organization = organization_user.organization


		today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		before_today = today - timedelta(days=7)

		end_date = self.request.GET.get('end_date', today.strftime("%b %d, %Y"))
		start_date = self.request.GET.get('start_date', before_today.strftime("%b %d, %Y"))
		_end_date = timezone.make_aware(datetime.strptime(end_date.strip(), '%b %d, %Y'))
		_start_date = timezone.make_aware(datetime.strptime(start_date.strip(), '%b %d, %Y'))
		date_range = [_start_date,_end_date+timedelta(days=1)]

		state_in = [1,2,3,4,5,6,7,8,9,10,11,12] if not validators.truthy(states) else states
		state_in = list(map(int, state_in))

		_order = '-' if not validators.truthy(order) or order == 'desc' else ''
		_order_by = 'datetime_ordered' if not validators.truthy(order_by) else order_by
		_order_by =  f'{_order}{_order_by}'
		per_page = 50 if not validators.truthy(per_page) else per_page

		q = Order.objects.filter(
			state__in=state_in,
			datetime_ordered__range=date_range,
			organization=organization,
		)
		if validators.truthy(s):
			s = s.strip()
			q = Order.objects.filter(
				(
					Q(pk__icontains=s) |
					Q(ref__icontains=s)
				)
				& Q(state__in=state_in)
				& Q(datetime_ordered__range=date_range)
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

		return Response({'count' : str(paginator.count), 'page' : page, 'items' : results})
