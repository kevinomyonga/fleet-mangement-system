from django.views.decorators.clickjacking import xframe_options_sameorigin
from sms.tasks import order_assign_sms, order_reassign_sms, order_created_sms
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.core.paginator import PageNotAnInteger
from django.db.models import Avg, Count, Min, Sum
from api.utils import new_assignment_driver_push
import validators
import pandas
import csv
import requests
import json
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta, date
from django.http import StreamingHttpResponse
from django.views.generic import TemplateView
from organization.http import PermissionView
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.views.generic import ListView
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.contrib import messages
from vehicle.models import Vehicle
from django.utils import timezone
from django.db.models import Avg
from driver.models import Driver
from .http import JsonResponse
from order.models import Order, OrderStatusLog
from django.views import View
from . import models
from . import utils
from . import forms


class IndexView(ListView, PermissionView):
    template_name = "order/index.html"

    def get_queryset(self):
        s = self.request.GET.get('s', '')
        page = self.request.GET.get('page', 1)
        states = self.request.GET.getlist('state')
        order = self.request.GET.get('order', 'desc')
        per_page = self.request.GET.get('per_page', 50)
        order_by = self.request.GET.get('order_by', 'datetime_ordered')

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        before_today = today - timedelta(days=7)

        end_date = self.request.GET.get(
            'end_date', today.strftime("%b %d, %Y"))
        start_date = self.request.GET.get(
            'start_date', before_today.strftime("%b %d, %Y"))
        _end_date = timezone.make_aware(
            datetime.strptime(end_date.strip(), '%b %d, %Y'))
        _start_date = timezone.make_aware(
            datetime.strptime(start_date.strip(), '%b %d, %Y'))
        date_range = [_start_date, _end_date+timedelta(days=1)]

        states = list(filter(None, states))
        state_in = [1, 2, 3, 4, 5, 8, 9, 10, 11, 12,
                    13] if not validators.truthy(states) else states
        state_in = list(state_in)
        state_in = [int(si) for si in state_in]

        _order = '-' if not validators.truthy(order) or order == 'desc' else ''
        _order_by = 'datetime_ordered' if not validators.truthy(
            order_by) else order_by
        _order_by = f'{_order}{_order_by}'
        per_page = 50 if not validators.truthy(per_page) else per_page

        q = models.Order.objects.filter(
            state__in=state_in,
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        )

        if validators.truthy(s):
            s = s.strip()
            q = models.Order.objects.filter(
                (
                    Q(pk__icontains=s) |
                    Q(ref__icontains=s) |
                    Q(sid__icontains=s) |
                    Q(pickup_contact_name__icontains=s) |
                    Q(pickup_contact_email__icontains=s) |
                    Q(pickup_location_name__icontains=s) |
                    Q(pickup_location_details__icontains=s) |
                    Q(pickup_location_name_more__icontains=s) |
                    Q(pickup_contact_phone_number__icontains=s) |
                    Q(dropoff_contact_name__icontains=s) |
                    Q(dropoff_contact_email__icontains=s) |
                    Q(dropoff_location_name__icontains=s) |
                    Q(dropoff_location_details__icontains=s) |
                    Q(dropoff_location_name_more__icontains=s) |
                    Q(dropoff_contact_phone_number__icontains=s)
                )
                & Q(state__in=state_in)
                & Q(datetime_ordered__range=date_range)
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

        items.current_states = state_in
        items.current_order = order
        items.current_order_by = order_by
        items.current_end_date = end_date
        items.current_start_date = start_date

        items.delivered = models.Order.objects.filter(
            state__in=[7],
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        ).count()
        items.failed = models.Order.objects.filter(
            state__in=[6],
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        ).count()

        try:
            items.per_page = int(per_page)
        except ValueError:
            items.per_page = 50

        items.current_search_term = s.strip()

        items.order_count = q.count()
        items.states = models.Order.DELIVERY_STATE

        items.time_now = timezone.now()
        items.time_zone = 'Europe/Paris'
        return items


class ReviewsView(ListView, PermissionView):
    template_name = "order/reviews.html"

    def get_queryset(self):
        s = self.request.GET.get('s', '')
        page = self.request.GET.get('page', 1)
        order = self.request.GET.get('order', 'desc')
        per_page = self.request.GET.get('per_page', 50)
        order_by = self.request.GET.get('order_by', 'datetime_ordered')

        _order = '-' if not validators.truthy(order) or order == 'desc' else ''
        _order_by = 'datetime_ordered' if not validators.truthy(
            order_by) else order_by
        _order_by = f'{_order}{_order_by}'
        per_page = 50 if not validators.truthy(per_page) else per_page

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        before_today = today - timedelta(days=7)

        end_date = self.request.GET.get(
            'end_date', today.strftime("%b %d, %Y"))
        start_date = self.request.GET.get(
            'start_date', before_today.strftime("%b %d, %Y"))
        _end_date = timezone.make_aware(
            datetime.strptime(end_date.strip(), '%b %d, %Y'))
        _start_date = timezone.make_aware(
            datetime.strptime(start_date.strip(), '%b %d, %Y'))
        date_range = [_start_date, _end_date+timedelta(days=1)]

        q = models.Order.objects.filter(
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        )
        if validators.truthy(s):
            s = s.strip()
            q = models.Order.objects.filter(
                (
                    Q(pk__icontains=s) |
                    Q(ref__icontains=s) |
                    Q(review__icontains=s) |
                    Q(rider__last_name__icontains=s) |
                    Q(rider__first_name__icontains=s) |
                    Q(ref__icontains=s) |
                    Q(sid__icontains=s)
                )
                & Q(datetime_ordered__range=date_range)
                & Q(organization=self.get_current_organization())
            )

        query = q.exclude(
            rating__isnull=True).prefetch_related().order_by(_order_by)
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

        try:
            items.per_page = int(per_page)
        except ValueError:
            items.per_page = 50

        items.current_search_term = s.strip()

        items.order_count = q.count()

        items.time_now = timezone.now()

        items.r5_count = Order.objects.filter(
            rating__gte=5.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        items.r4_count = Order.objects.filter(
            rating__gte=4.0, rating__lt=5.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        items.r3_count = Order.objects.filter(
            rating__gte=3.0, rating__lt=4.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        items.r2_count = Order.objects.filter(
            rating__gte=2.0, rating__lt=3.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        items.r1_count = Order.objects.filter(
            rating__gt=0.0, rating__lt=2.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        items.rating_count = Order.objects.filter(
            rating__gt=0.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        return items


class PaymentsView(ListView, PermissionView):
    template_name = "order/payments.html"

    def get_queryset(self):
        s = self.request.GET.get('s', '')
        page = self.request.GET.get('page', 1)
        order = self.request.GET.get('order', 'desc')
        per_page = self.request.GET.get('per_page', 50)
        order_by = self.request.GET.get('order_by', 'datetime_ordered')

        _order = '-' if not validators.truthy(order) or order == 'desc' else ''
        _order_by = 'datetime_ordered' if not validators.truthy(
            order_by) else order_by
        _order_by = f'{_order}{_order_by}'
        per_page = 50 if not validators.truthy(per_page) else per_page

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        before_today = today - timedelta(days=7)

        end_date = self.request.GET.get(
            'end_date', today.strftime("%b %d, %Y"))
        start_date = self.request.GET.get(
            'start_date', before_today.strftime("%b %d, %Y"))
        _end_date = timezone.make_aware(
            datetime.strptime(end_date.strip(), '%b %d, %Y'))
        _start_date = timezone.make_aware(
            datetime.strptime(start_date.strip(), '%b %d, %Y'))
        date_range = [_start_date, _end_date+timedelta(days=1)]

        # mpesa payments
        mpesa_payments = models.MpesaPayments.objects.filter(
            (
                Q(pk__icontains=s) |
                Q(MpesaReceiptNumber__icontains=s)
            )
            & Q(TransactionDate__range=date_range)
            & Q(order__organization=self.get_current_organization())
        ).aggregate(Sum('Amount'))

        q = models.Order.objects.filter(
            state=models.Order.DELIVERED,
            payment_method__in=[models.Order.POSTPAID,
                                models.Order.POSTPAID_MM],
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        )
        if validators.truthy(s):
            s = s.strip()
            q = models.Order.objects.filter(
                (
                    Q(pk__icontains=s) |
                    Q(ref__icontains=s) |
                    Q(sid__icontains=s) |
                    Q(rider__last_name__icontains=s) |
                    Q(rider__first_name__icontains=s) |
                    Q(rider__pk__icontains=s) |
                    Q(rider__phone_number__icontains=s) |
                    Q(mpesapayments__MpesaReceiptNumber__icontains=s)
                )
                & Q(state=models.Order.DELIVERED)
                & Q(payment_method__in=[models.Order.POSTPAID, models.Order.POSTPAID_MM])
                & Q(datetime_ordered__range=date_range)
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
        items.current_end_date = end_date
        items.current_start_date = start_date

        items.total = q.aggregate(Sum('price'))
        items.total_paid = q.exclude(paid=False).aggregate(Sum('price'))
        items.total_unpaid = q.exclude(paid=True).aggregate(Sum('price'))
        items.mpesa = mpesa_payments

        try:
            items.per_page = int(per_page)
        except ValueError:
            items.per_page = 50

        items.current_search_term = s.strip()

        items.order_count = q.count()

        items.time_now = timezone.now()
        return items

    def post(self, request, *args, **kwargs):
        order_id = self.request.POST.get("order_id", None)
        if validators.truthy(order_id):
            order = models.Order.objects.get(
                pk=order_id, organization=self.get_current_organization())
            order.paid = True
            order.save()
        return HttpResponseRedirect(self.request.get_full_path())


class CreateView(TemplateView, PermissionView):
    template_name = "order/create.html"
    success_url = reverse_lazy("order:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pickup_lat'] = self.request.POST.get("pickup_lat", "")
        context['pickup_lng'] = self.request.POST.get("pickup_lng", "")
        context['pickup_address'] = self.request.POST.get("pickup_address", "")
        context['pickup_details'] = self.request.POST.get("pickup_details", "")
        context['pickup_address_more'] = self.request.POST.get(
            "pickup_address_more", "")
        context['pickup_contact_name'] = self.request.POST.get(
            "pickup_contact_name", "")
        context['pickup_contact_email'] = self.request.POST.get(
            "pickup_contact_email", "")
        context['pickup_contact_phone_number'] = self.request.POST.get(
            "pickup_contact_phone_number", "")

        context['dropoff_lat'] = self.request.POST.get("dropoff_lat", "")
        context['dropoff_lng'] = self.request.POST.get("dropoff_lng", "")
        context['dropoff_address'] = self.request.POST.get(
            "dropoff_address", "")
        context['dropoff_details'] = self.request.POST.get(
            "dropoff_details", "")
        context['dropoff_address_more'] = self.request.POST.get(
            "dropoff_address_more", "")
        context['dropoff_contact_name'] = self.request.POST.get(
            "dropoff_contact_name", "")
        context['dropoff_contact_email'] = self.request.POST.get(
            "dropoff_contact_email", "")
        context['dropoff_contact_phone_number'] = self.request.POST.get(
            "dropoff_contact_phone_number", "")
        print(context['dropoff_contact_phone_number'])

        context['width'] = self.request.POST.get("width", "")
        context['price'] = self.request.POST.get("price", "")
        context['length'] = self.request.POST.get("length", "")
        context['height'] = self.request.POST.get("height", "")
        context['weight'] = self.request.POST.get("weight", "")
        context['delivery_date'] = self.request.POST.get("delivery_date", "")
        context['delivery_time'] = self.request.POST.get("delivery_time", "")
        context['payment_method'] = self.request.POST.get("payment_method", "")

        context['payment_methods'] = Order.PAYMENT_METHOD
        context['delivery_times'] = Order.PREFERED_TIME
        context['map_api'] = self.get_map_key()

        return context

    def post(self, request, *args, **kwargs):

        pickup_lat = self.request.POST.get("pickup_lat", None)
        pickup_lng = self.request.POST.get("pickup_lng", None)
        pickup_address = self.request.POST.get("pickup_address", None)
        pickup_details = self.request.POST.get("pickup_details", None)
        pickup_address_more = self.request.POST.get(
            "pickup_address_more", None)
        pickup_contact_name = self.request.POST.get(
            "pickup_contact_name", None)
        pickup_contact_email = self.request.POST.get(
            "pickup_contact_email", None)
        pickup_contact_phone_number = self.request.POST.get(
            "pickup_contact_phone_number", None)

        dropoff_lat = self.request.POST.get("dropoff_lat", None)
        dropoff_lng = self.request.POST.get("dropoff_lng", None)
        dropoff_address = self.request.POST.get("dropoff_address", None)
        dropoff_details = self.request.POST.get("dropoff_details", None)
        dropoff_address_more = self.request.POST.get(
            "dropoff_address_more", None)
        dropoff_contact_name = self.request.POST.get(
            "dropoff_contact_name", None)
        dropoff_contact_email = self.request.POST.get(
            "dropoff_contact_email", None)
        dropoff_contact_phone_number = self.request.POST.get(
            "dropoff_contact_phone_number", None)
        order_ref = self.request.POST.get("order_ref", None)
        order_sid = self.request.POST.get("order_sid", None)
        width = self.request.POST.get("width", None)
        price = self.request.POST.get("price", None)
        length = self.request.POST.get("length", None)
        height = self.request.POST.get("height", None)
        weight = self.request.POST.get("weight", None)
        delivery_date = self.request.POST.get("delivery_date", "")
        delivery_time = self.request.POST.get("delivery_time", 1)
        payment_method = self.request.POST.get("payment_method", 1)

        order = Order()
        log = OrderStatusLog()
        if validators.truthy(order_ref):
            order_ref = order_ref.strip()
            try:
                models.Order.objects.get(
                    ref=order_ref, organization=self.get_current_organization())
                messages.add_message(
                    request, messages.ERROR, f'Order ref already exists')
                return self.get(request, *args, **kwargs)
            except models.Order.DoesNotExist:
                order.ref = order_ref

        if validators.truthy(order_sid):
            order_sid = order_sid.strip()
            try:
                models.Order.objects.get(
                    sid=order_sid, organization=self.get_current_organization())
                messages.add_message(
                    request, messages.ERROR, f'Order sid already exists')
                return self.get(request, *args, **kwargs)
            except models.Order.DoesNotExist:
                order.sid = order_sid

        try:
            order.price = int(price)
        except ValueError:
            pass

        try:
            order.width = int(width)
        except ValueError:
            pass

        try:
            order.length = int(length)
        except ValueError:
            pass

        try:
            order.height = int(height)
        except ValueError:
            pass

        try:
            order.weight = int(weight)
        except ValueError:
            pass

        try:
            order.payment_method = int(payment_method)
        except ValueError:
            pass

        try:
            order.preffered_delivery_period = int(delivery_time)
        except ValueError:
            pass

        order.pickup_lat = pickup_lat
        order.pickup_lng = pickup_lng
        order.pickup_location_name = pickup_address
        order.pickup_location_details = pickup_details
        order.pickup_contact_name = pickup_contact_name
        order.pickup_contact_email = pickup_contact_email
        order.pickup_location_name_more = pickup_address_more
        order.pickup_contact_phone_number = pickup_contact_phone_number

        order.dropoff_location_details = dropoff_details
        order.dropoff_location_name = dropoff_address
        order.dropoff_contact_phone_number = dropoff_contact_phone_number
        order.dropoff_contact_name = dropoff_contact_name
        order.dropoff_contact_email = dropoff_contact_email
        order.dropoff_location_name_more = dropoff_address_more
        order.dropoff_lat = dropoff_lat
        order.dropoff_lng = dropoff_lng

        if validators.truthy(delivery_date):
            try:
                order.preffered_delivery_date = datetime.strptime(
                    delivery_date, '%m/%d/%Y')
            except ValueError:
                pass

        order.organization = self.get_current_organization()
        order.added_by = self.request.user
        order.modified_by = self.request.user

        order.save()
        order.refresh_from_db()
        order_created_sms(order)
        return HttpResponseRedirect(self.success_url)


class OrderView(DetailView, PermissionView):
    template_name = "order/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['map_api'] = self.get_map_key()
        context["logs"] = models.OrderStatusLog.objects.filter(
            order_id=self.get_object())

        return context

    def get_object(self):
        return get_object_or_404(
            models.Order,
            pk=self.kwargs["pk"],
            organization=self.get_current_organization()
        )


class OrderPartialView(DetailView, PermissionView):
    template_name = "order/partials/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['map_api'] = self.get_map_key()

        return context

    def get_object(self):
        return get_object_or_404(
            models.Order,
            pk=self.kwargs["pk"],
            organization=self.get_current_organization()
        )


@method_decorator(xframe_options_sameorigin, name='dispatch')
class OrderTrackingIframeView(ListView, PermissionView):
    template_name = "order/tracking_iframe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['map_api'] = self.get_map_key()

        return context

    def get_queryset(self):
        s = self.request.GET.get('s', '')
        page = self.request.GET.get('page', 1)
        states = self.request.GET.getlist('state')
        order = self.request.GET.get('order', 'desc')
        per_page = self.request.GET.get('per_page', 50)
        order_by = self.request.GET.get('order_by', 'datetime_ordered')

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        before_today = today - timedelta(days=7)

        end_date = self.request.GET.get(
            'end_date', today.strftime("%b %d, %Y"))
        start_date = self.request.GET.get(
            'start_date', before_today.strftime("%b %d, %Y"))
        _end_date = timezone.make_aware(
            datetime.strptime(end_date.strip(), '%b %d, %Y'))
        _start_date = timezone.make_aware(
            datetime.strptime(start_date.strip(), '%b %d, %Y'))
        date_range = [_start_date, _end_date+timedelta(days=1)]

        states = list(filter(None, states))
        state_in = [1, 2, 3, 4, 5, 8, 9, 10, 11, 12,
                    13] if not validators.truthy(states) else states
        state_in = list(map(int, state_in))

        _order = '-' if not validators.truthy(order) or order == 'desc' else ''
        _order_by = 'datetime_ordered' if not validators.truthy(
            order_by) else order_by
        _order_by = f'{_order}{_order_by}'
        per_page = 50 if not validators.truthy(per_page) else per_page

        q = models.Order.objects.filter(
            state__in=state_in,
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        )
        if validators.truthy(s):
            s = s.strip()
            q = models.Order.objects.filter(
                (
                    Q(pk__icontains=s) |
                    Q(ref__icontains=s)
                )
                & Q(state__in=state_in)
                & Q(datetime_ordered__range=date_range)
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

        items.current_states = state_in
        items.current_order = order
        items.current_order_by = order_by
        items.current_end_date = end_date
        items.current_start_date = start_date

        items.delivered = models.Order.objects.filter(
            state__in=[7],
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        ).count()
        items.failed = models.Order.objects.filter(
            state__in=[6],
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        ).count()

        try:
            items.per_page = int(per_page)
        except ValueError:
            items.per_page = 50

        items.current_search_term = s.strip()

        items.order_count = q.count()
        items.states = models.Order.DELIVERY_STATE

        items.time_now = timezone.now()
        return items


@method_decorator(xframe_options_sameorigin, name='dispatch')
class DropoffIframeView(DetailView, PermissionView):
    template_name = "order/dropoff_iframe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['map_api'] = self.get_map_key()

        return context

    def get_object(self):
        return get_object_or_404(
            models.Order,
            pk=self.kwargs["pk"],
            organization=self.get_current_organization()
        )


class PlanView(TemplateView, PermissionView):
    template_name = "order/plan_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['map_api'] = self.get_map_key()

        return context


class MapView(TemplateView, PermissionView):
    template_name = "order/map_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['map_api'] = self.get_map_key()

        return context


@method_decorator(xframe_options_sameorigin, name='dispatch')
class PickupIframeView(DetailView, PermissionView):
    template_name = "order/pickup_iframe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['map_api'] = self.get_map_key()

        return context

    def get_object(self):
        return get_object_or_404(
            models.Order,
            pk=self.kwargs["pk"],
            organization=self.get_current_organization()
        )


@method_decorator(xframe_options_sameorigin, name='dispatch')
class MultiAssignIframeView(ListView, PermissionView):
    template_name = "order/assign_iframe.html"

    def get_queryset(self):
        s = self.request.GET.get('s', '')
        page = self.request.GET.get('page', 1)
        order = self.request.GET.get('order', 'desc')
        per_page = self.request.GET.get('per_page', 50)
        order_by = self.request.GET.get('order_by', 'modified')

        _order = '-' if not validators.truthy(order) or order == 'desc' else ''
        _order_by = 'modified' if not validators.truthy(order_by) else order_by
        _order_by = f'{_order}{_order_by}'
        per_page = 50 if not validators.truthy(per_page) else per_page

        q = Driver.objects.filter(
            deleted=False, organization=self.get_current_organization())
        if validators.truthy(s):
            s = s.strip()
            q = Driver.objects.filter(
                (
                    Q(pk__icontains=s) |
                    Q(phone_number__icontains=s) |
                    Q(user__last_name__icontains=s) |
                    Q(user__first_name__icontains=s) &
                    Q(deleted=False) &
                    Q(organization=self.get_current_organization())
                )
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

        items.current_search_term = s.strip()

        items.order_count = q.count()
        items.current_search_term = s
        return items

    def post(self, request, *args, **kwargs):
        rider_id = self.request.POST.get("rider_id", None)
        order_ids = self.request.GET.getlist('order_id')
        if validators.truthy(rider_id) and validators.truthy(order_ids):
            for order_id in order_ids:
                order = models.Order.objects.get(
                    pk=order_id, organization=self.get_current_organization())
                prev_rider = order.rider
                get_rider = Driver.objects.get(pk=rider_id)
                order.rider = get_rider
                order.state = models.Order.SUBMITTED_PENDING_FOWARD_DELIVERY
                order.modified_by = request.user
                order.datetime_assigned = timezone.now()
                order.order_status_logs.create(
                    order_id=order.id, action=f"Order assigned to {order.rider.full_names} for delivery")
                order.save()
                if not validators.truthy(prev_rider):
                    order_assign_sms(order)
                else:
                    order_reassign_sms(order)
                new_assignment_driver_push(order)
            messages.add_message(
                request, messages.INFO, f'Order has been assigned to <b>{get_rider.full_names()}</b>, refresh page to see changes')
        return HttpResponseRedirect(self.request.get_full_path())


@method_decorator(xframe_options_sameorigin, name='dispatch')
class AssignIframeView(ListView, PermissionView):
    template_name = "order/assign_iframe.html"

    def get_queryset(self):
        order_obj = get_object_or_404(
            models.Order,
            pk=self.kwargs["pk"],
            organization=self.get_current_organization()
        )

        s = self.request.GET.get('s', '')
        page = self.request.GET.get('page', 1)
        order = self.request.GET.get('order', 'desc')
        per_page = self.request.GET.get('per_page', 50)
        order_by = self.request.GET.get('order_by', 'modified')

        _order = '-' if not validators.truthy(order) or order == 'desc' else ''
        _order_by = 'modified' if not validators.truthy(order_by) else order_by
        _order_by = f'{_order}{_order_by}'
        per_page = 50 if not validators.truthy(per_page) else per_page

        q = Driver.objects.filter(
            deleted=False, organization=self.get_current_organization())
        if validators.truthy(s):
            s = s.strip()
            q = Driver.objects.filter(
                (
                    Q(pk__icontains=s) |
                    Q(phone_number__icontains=s) |
                    Q(last_name__icontains=s) |
                    Q(first_name__icontains=s) &
                    Q(deleted=False) &
                    Q(organization=self.get_current_organization())
                )
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
        items.order_obj = order_obj

        try:
            items.per_page = int(per_page)
        except ValueError:
            items.per_page = 50

        items.current_search_term = s.strip()

        items.order_count = q.count()
        items.current_search_term = s
        return items

    def post(self, request, *args, **kwargs):
        rider_id = self.request.POST.get("rider_id", None)
        unassign_id = self.request.POST.get("unassign_id", None)
        if validators.truthy(unassign_id):
            order = models.Order.objects.get(
                pk=self.kwargs["pk"], organization=self.get_current_organization())
            get_rider = Driver.objects.get(pk=unassign_id)
            if order.rider == get_rider:
                order.rider = None
                order.state = models.Order.SUBMITTED_PENDING_VENDOR_PICK_UP
                order.modified_by = request.user
                order.save()
            messages.add_message(
                request, messages.INFO, f'Order has been unassigned, refresh page to see changes')

            return HttpResponseRedirect(self.request.get_full_path())

        if validators.truthy(rider_id):
            order = models.Order.objects.get(
                pk=self.kwargs["pk"], organization=self.get_current_organization())
            prev_rider = order.rider
            get_rider = Driver.objects.get(pk=rider_id)
            order.rider = get_rider
            order.state = models.Order.SUBMITTED_PENDING_FOWARD_DELIVERY
            order.modified_by = request.user
            order.datetime_assigned = timezone.now()
            order.save()
            if not validators.truthy(prev_rider):
                order_assign_sms(order)
            else:
                order_reassign_sms(order)
            new_assignment_driver_push(order)
            messages.add_message(
                request, messages.INFO, f'Order has been assigned to <b>{get_rider.full_names()}</b>, refresh page to see changes')
        return HttpResponseRedirect(self.request.get_full_path())


@method_decorator(xframe_options_sameorigin, name='dispatch')
class AjaxAssignIframeView(ListView, PermissionView):
    template_name = "order/ajax_assign_iframe.html"

    def get_queryset(self):
        s = self.request.GET.get('s', '')
        page = self.request.GET.get('page', 1)
        order = self.request.GET.get('order', 'desc')
        per_page = self.request.GET.get('per_page', 50)
        order_by = self.request.GET.get('order_by', 'modified')

        _order = '-' if not validators.truthy(order) or order == 'desc' else ''
        _order_by = 'modified' if not validators.truthy(order_by) else order_by
        _order_by = f'{_order}{_order_by}'
        per_page = 50 if not validators.truthy(per_page) else per_page

        q = Driver.objects.filter(
            deleted=False, organization=self.get_current_organization())
        if validators.truthy(s):
            s = s.strip()
            q = Driver.objects.filter(
                (
                    Q(pk__icontains=s) |
                    Q(phone_number__icontains=s) |
                    Q(user__last_name__icontains=s) |
                    Q(user__first_name__icontains=s) &
                    Q(deleted=False) &
                    Q(organization=self.get_current_organization())
                )
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

        items.current_search_term = s.strip()
        items.route_id = self.kwargs["route_id"]
        items.vehicle_id = self.kwargs["vehicle_id"]
        items.order_count = q.count()
        items.current_search_term = s
        return items


@method_decorator(xframe_options_sameorigin, name='dispatch')
class StateIframeView(DetailView, PermissionView):
    template_name = "order/state_change_iframe.html"

    def get_object(self):
        return get_object_or_404(
            models.Order,
            pk=self.kwargs["pk"],
            organization=self.get_current_organization()
        )

    def post(self, request, *args, **kwargs):
        state = self.request.POST.get("state", 0)
        state = int(state)
        if validators.between(state, min=1, max=13):
            order = models.Order.objects.get(pk=self.kwargs["pk"])
            if state < order.state:
                messages.add_message(request, messages.INFO,
                                     f'Invalid status change')
            else:
                order.state = state
                order.save()
                messages.add_message(
                    request, messages.INFO, f'Order has been changed to <b>{order.get_state_display()}</b>, refresh page to see changes')
        else:
            messages.add_message(request, messages.INFO,
                                 f'Invalid status change')

        return HttpResponseRedirect(self.request.get_full_path())


class CSVBuffer:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def error_serializer(o):
    return [
        o.ref,
        o.pickup_location_name, o.pickup_location_name_more,
        o.pickup_lat, o.pickup_lng,
        o.pickup_contact_name, o.pickup_contact_phone_number, o.pickup_contact_email,
        o.dropoff_location_name, o.dropoff_location_name_more,
        o.dropoff_lat, o.dropoff_lng,
        o.dropoff_contact_name, o.dropoff_contact_phone_number, o.dropoff_contact_email,
        o.length, o.width, o.height, o.weight, o.price,
        o.payment_method,
        o.preffered_delivery_date, o.preffered_delivery_period,
        o.notes, o.error
    ]


def iter_error_items(items, pseudo_buffer):
    writer = csv.writer(pseudo_buffer)
    yield writer.writerow(
        [
            "Order Ref",
            "Pickup address", "Pickup - Road/Apartment/Hse. No",
            "Pickup latitude", "Pickup longitude",
            "Pickup Contact Name", "Pickup Contact Phone", "Pickup contact email",
            "Dropoff address", "Dropoff - Road/Apartment/Hse. No",
            "Dropoff latitude", "Dropoff longitude",
            "Dropoff Contact Name", "Dropoff Contact Phone", "Dropoff contact email",
            "Length", "Width", "Height", "Weight", "Price",
            "Payment method(Credit/Prepaid/COD)",
            "Delivery date(YYYY-MM-DD)", "Delivery period (Anytime/Morning/Afternoon)",
            "Notes", "Error"
        ]
    )
    for item in items:
        yield writer.writerow(error_serializer(item))


def export_serializer(o):
    pickup_coords = f'{o.pickup_lat},{o.pickup_lng}'
    pickup_address = o.pickup_location_name
    if validators.truthy(o.pickup_location_name_more):
        pickup_address = f'{pickup_address} - {o.pickup_location_name_more}'

    dropoff_coords = f'{o.dropoff_lat},{o.dropoff_lng}'
    dropoff_address = o.dropoff_location_name
    if validators.truthy(o.dropoff_location_name_more):
        dropoff_address = f'{dropoff_address} - {o.dropoff_location_name_more}'

    driver_name = ""
    driver_phone = ""
    if o.rider:
        driver_name = o.rider.full_names()
        driver_phone = o.rider.phone_number
    payment_method = o.get_payment_method_display()
    if o.payment_method == Order.POSTPAID:
        if o.paid:
            payment_method = f'{payment_method} - PAID'
        else:
            payment_method = f'{payment_method} - NOT PAID'

    datetime_completed = '' if o.datetime_completed is None else o.datetime_completed.isoformat()

    return [
        o.pk, o.ref, o.get_state_display(), o.datetime_ordered.isoformat(),
        pickup_address, pickup_coords,
        o.pickup_contact_name, o.pickup_contact_phone_number, o.pickup_contact_email,
        dropoff_address, dropoff_coords,
        o.dropoff_contact_name, o.dropoff_contact_phone_number, o.dropoff_contact_email,
        driver_name, driver_phone, o.get_vehicle_type_display(),
        o.length, o.width, o.height, o.weight, o.price,
        payment_method,
        datetime_completed,
        o.rating, o.review,
        o.notes
    ]


def iter_export_items(iterator, pseudo_buffer):
    writer = csv.writer(pseudo_buffer)

    yield writer.writerow(
        [
            "Order ID", "Order Ref", "Status", "Order datetime",
            "Pickup address", "Pickup - coordinates",
            "Pickup Contact Name", "Pickup Contact Phone", "Pickup contact email",
            "Dropoff address", "Dropoff - coordinates",
            "Dropoff Contact Name", "Dropoff Contact Phone", "Dropoff contact email",
            "Driver name", "Driver phone number", "Vehicle Type",
            "Length", "Width", "Height", "Weight", "Price",
            "Payment method",
            "Order complete time",
            "Rating", "Review",
            "Notes"
        ]
    )
    for item in iterator:
        yield writer.writerow(export_serializer(item))


def dump_errors_csv(orders):
    response = StreamingHttpResponse(streaming_content=(iter_error_items(orders, CSVBuffer())),
                                     content_type="text/csv")

    t = timezone.now()
    export_name = f'errors-{t.year}-{t.month}-{t.day}-{t.hour}-{t.minute}-{t.second}.csv'
    response['Content-Disposition'] = f'attachment; filename="{export_name}"'
    return response


class ExportOrdersView(PermissionView):

    def get(self, request, *args, **kwargs):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        before_today = today - timedelta(days=7)

        states = self.request.GET.getlist('state')
        end_date = self.request.GET.get(
            'end_date', today.strftime("%b %d, %Y"))
        start_date = self.request.GET.get(
            'start_date', before_today.strftime("%b %d, %Y"))

        _end_date = timezone.make_aware(
            datetime.strptime(end_date.strip(), '%b %d, %Y'))
        _start_date = timezone.make_aware(
            datetime.strptime(start_date.strip(), '%b %d, %Y'))
        date_range = [_start_date, _end_date+timedelta(days=1)]

        states = list(filter(None, states))
        state_in = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                    13] if not validators.truthy(states) else states
        state_in = list(map(int, state_in))

        iterator = Order.objects.filter(
            datetime_ordered__range=date_range,
            state__in=state_in,
            organization=self.get_current_organization()
        ).order_by('-datetime_ordered').iterator()
        response = StreamingHttpResponse(streaming_content=(
            iter_export_items(iterator, CSVBuffer())), content_type="text/csv")

        t = timezone.now()
        export_name = f'export-{t.year}-{t.month}-{t.day}-{t.hour}-{t.minute}-{t.second}.csv'
        response['Content-Disposition'] = f'attachment; filename="{export_name}"'
        return response


class ExportReviewsView(PermissionView):

    def get(self, request, *args, **kwargs):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        before_today = today - timedelta(days=7)

        states = self.request.GET.getlist('state')
        end_date = self.request.GET.get(
            'end_date', today.strftime("%b %d, %Y"))
        start_date = self.request.GET.get(
            'start_date', before_today.strftime("%b %d, %Y"))

        _end_date = timezone.make_aware(
            datetime.strptime(end_date.strip(), '%b %d, %Y'))
        _start_date = timezone.make_aware(
            datetime.strptime(start_date.strip(), '%b %d, %Y'))
        date_range = [_start_date, _end_date+timedelta(days=1)]

        states = list(filter(None, states))
        state_in = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                    13] if not validators.truthy(states) else states
        state_in = list(map(int, state_in))

        iterator = Order.objects.filter(
            datetime_ordered__range=date_range,
            state__in=state_in,
            organization=self.get_current_organization()
        ).exclude(rating__isnull=True).order_by('-datetime_ordered').iterator()
        response = StreamingHttpResponse(streaming_content=(
            iter_export_items(iterator, CSVBuffer())), content_type="text/csv")

        t = timezone.now()
        export_name = f'export-{t.year}-{t.month}-{t.day}-{t.hour}-{t.minute}-{t.second}.csv'
        response['Content-Disposition'] = f'attachment; filename="{export_name}"'
        return response


class ExportDriverReviewsView(PermissionView):

    def get(self, request, *args, **kwargs):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        before_today = today - timedelta(days=7)

        states = self.request.GET.getlist('state')
        rider_id = self.request.GET.get('rider_id', -1)
        end_date = self.request.GET.get(
            'end_date', today.strftime("%b %d, %Y"))
        start_date = self.request.GET.get(
            'start_date', before_today.strftime("%b %d, %Y"))

        _end_date = timezone.make_aware(
            datetime.strptime(end_date.strip(), '%b %d, %Y'))
        _start_date = timezone.make_aware(
            datetime.strptime(start_date.strip(), '%b %d, %Y'))
        date_range = [_start_date, _end_date+timedelta(days=1)]

        states = list(filter(None, states))
        state_in = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                    13] if not validators.truthy(states) else states
        state_in = list(map(int, state_in))

        driver = Driver.objects.get(pk=rider_id)

        iterator = Order.objects.filter(
            datetime_ordered__range=date_range,
            state__in=state_in,
            rider=driver,
            organization=self.get_current_organization()
        ).exclude(rating__isnull=True).order_by('-datetime_ordered').iterator()
        response = StreamingHttpResponse(streaming_content=(
            iter_export_items(iterator, CSVBuffer())), content_type="text/csv")

        t = timezone.now()
        export_name = f'export-{t.year}-{t.month}-{t.day}-{t.hour}-{t.minute}-{t.second}.csv'
        response['Content-Disposition'] = f'attachment; filename="{export_name}"'
        return response


@method_decorator(xframe_options_sameorigin, name='dispatch')
class UploadOrdersIframeView(TemplateView, PermissionView):
    template_name = "order/upload_orders_iframe.html"

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file').file
        doc = pandas.read_csv(csv_file)
        print(doc.head())

        start_row = -1
        row_count, col_count = doc.shape

        slugged_cols = [
            'rdrrf',
            'pckpddrss', 'pckprdprtmnthsn', 'pckplttd', 'pckplngtd', 'pckpcntctnm', 'pckpcntctphn', 'pckpcntctml',
            'drpffddrss', 'drpffrdprtmnthsn', 'drpfflttd', 'drpfflngtd', 'drpffcntctnm', 'drpffcntctphn', 'drpffcntctml',
            'lngth', 'wdth', 'hght', 'wght', 'prc',
            'pymntmthdcrdtprpdpstpdcshpstpdmm', 'dlvrydtyyyymmdd', 'dlvryprdnytmmrnngftrnn', 'nts'
        ]

        headers = {
            'ref': -1,
            'pickup_address': -1,
            'pickup_road': -1,
            'pickup_lat': -1,
            'pickup_lng': -1,
            'pickup_contact_name': -1,
            'pickup_contact_phone_number': -1,
            'pickup_contact_email': -1,
            'dropoff_address': -1,
            'dropoff_road': -1,
            'dropoff_lat': -1,
            'dropoff_lng': -1,
            'dropoff_contact_name': -1,
            'dropoff_contact_phone_number': -1,
            'dropoff_contact_email': -1,
            'length': -1,
            'width': -1,
            'height': -1,
            'weight': -1,
            'price': -1,
            'payment_method': -1,
            'delivery_date': -1,
            'delivery_period': -1,
            'notes': -1,
        }

        col_num = 0
        for col in doc.columns:
            if not validators.truthy(col):
                continue

            val = utils.csv_header_to_slug(col)
            if val == 'rdrrf':
                headers['ref'] = col_num
            if val == 'pckpddrss':
                headers['pickup_address'] = col_num
            if val == 'pckprdprtmnthsn':
                headers['pickup_road'] = col_num
            if val == 'pckplttd':
                headers['pickup_lat'] = col_num
            if val == 'pckplngtd':
                headers['pickup_lng'] = col_num
            if val == 'pckpcntctnm':
                headers['pickup_contact_name'] = col_num
            if val == 'pckpcntctphn':
                headers['pickup_contact_phone_number'] = col_num
            if val == 'pckpcntctml':
                headers['pickup_contact_email'] = col_num
            if val == 'drpffddrss':
                headers['dropoff_address'] = col_num
            if val == 'drpffrdprtmnthsn':
                headers['dropoff_road'] = col_num
            if val == 'drpfflttd':
                headers['dropoff_lat'] = col_num
            if val == 'drpfflngtd':
                headers['dropoff_lng'] = col_num
            if val == 'drpffcntctnm':
                headers['dropoff_contact_name'] = col_num
            if val == 'drpffcntctphn':
                headers['dropoff_contact_phone_number'] = col_num
            if val == 'drpffcntctml':
                headers['dropoff_contact_email'] = col_num
            if val == 'lngth':
                headers['length'] = col_num
            if val == 'wdth':
                headers['width'] = col_num
            if val == 'hght':
                headers['height'] = col_num
            if val == 'wght':
                headers['width'] = col_num
            if val == 'prc':
                headers['price'] = col_num
            if val == 'pymntmthdcrdtprpdpstpdcshpstpdmm':
                headers['payment_method'] = col_num
            if val == 'dlvrydtyyyymmdd':
                headers['delivery_date'] = col_num
            if val == 'dlvryprdnytmmrnngftrnn':
                headers['delivery_period'] = col_num
            if val == 'nts':
                headers['notes'] = col_num

            col_num = col_num + 1

        errors = []
        for x in range(0, row_count):
            o = Order()
            print(headers['notes'])
            if headers['notes'] != -1:
                o.notes = utils.process_cell(doc, x, headers['notes'])

            if headers['ref'] != -1:
                ref = utils.process_cell(doc, x, headers['ref'])
                if validators.truthy(ref):
                    o.ref = ref

            if headers['payment_method'] != -1:
                pm = utils.process_cell(doc, x, headers['payment_method'])
                print(pm)
                if validators.truthy(pm):
                    if pm.lower() == 'credit':
                        o.payment_method = Order.CREDIT
                    if pm.lower() == 'postpaid-cash':
                        o.payment_method = Order.POSTPAID
                    if pm.lower() == 'postpaid-mm':
                        o.payment_method = Order.POSTPAID_MM
                    if pm.lower() == 'prepaid':
                        o.payment_method = Order.PREPAID
            print(o.payment_method)

            if headers['price'] != -1:
                o.price = utils.process_cell(doc, x, headers['price'])
            if headers['width'] != -1:
                o.width = utils.process_cell(doc, x, headers['width'])
            if headers['weight'] != -1:
                o.weight = utils.process_cell(doc, x, headers['weight'])
            if headers['length'] != -1:
                o.length = utils.process_cell(doc, x, headers['length'])
            if headers['height'] != -1:
                o.height = utils.process_cell(doc, x, headers['height'])

            if headers['pickup_address'] != -1:
                o.pickup_location_name = utils.process_cell(
                    doc, x, headers['pickup_address'])

            if headers['pickup_road'] != -1:
                o.pickup_location_name_more = utils.process_cell(
                    doc, x, headers['pickup_road'])

            if headers['pickup_contact_name'] != -1:
                o.pickup_contact_name = utils.process_cell(
                    doc, x, headers['pickup_contact_name'])

            if headers['pickup_contact_email'] != -1:
                o.pickup_contact_email = utils.process_cell(
                    doc, x, headers['pickup_contact_email'])

            if headers['pickup_contact_phone_number'] != -1:
                o.pickup_contact_phone_number = int(
                    float(utils.process_cell(doc, x, headers['pickup_contact_phone_number'])))

            if headers['pickup_lng'] != -1:
                o.pickup_lng = utils.process_cell(
                    doc, x, headers['pickup_lng'])

            if headers['pickup_lat'] != -1:
                o.pickup_lat = utils.process_cell(
                    doc, x, headers['pickup_lat'])

            if headers['dropoff_address'] != -1:
                o.dropoff_location_name = utils.process_cell(
                    doc, x, headers['dropoff_address'])

            if headers['dropoff_road'] != -1:
                o.dropoff_location_name_more = utils.process_cell(
                    doc, x, headers['dropoff_road'])

            if headers['dropoff_contact_name'] != -1:
                o.dropoff_contact_name = utils.process_cell(
                    doc, x, headers['dropoff_contact_name'])

            if headers['dropoff_contact_email'] != -1:
                o.dropoff_contact_email = utils.process_cell(
                    doc, x, headers['dropoff_contact_email'])

            if headers['dropoff_contact_phone_number'] != -1:
                o.dropoff_contact_phone_number = int(
                    float(utils.process_cell(doc, x, headers['dropoff_contact_phone_number'])))

            if headers['dropoff_lng'] != -1:
                o.dropoff_lng = utils.process_cell(
                    doc, x, headers['dropoff_lng'])

            if headers['dropoff_lat'] != -1:
                o.dropoff_lat = utils.process_cell(
                    doc, x, headers['dropoff_lat'])

            o.organization = self.get_current_organization()
            o.added_by = self.request.user
            o.modified_by = self.request.user

            #datetime_ordered = models.DateTimeField(default=timezone.now)
            #vehicle_type = models.PositiveSmallIntegerField(choices=VEHICLE_TYPES, default=TBD)
            #preffered_delivery_date = models.DateField(default=datetime.date.today)
            #preffered_delivery_period = models.PositiveSmallIntegerField(default=ANYTIME, choices=PREFERED_TIME)

            try:
                o.save()
            except Exception as e:
                o.error = str(e)
                errors.append(o)

        if len(errors):
            messages.add_message(
                request, messages.SUCCESS, f'There were some errors, could not upload some orders')
            return dump_errors_csv(errors)

        messages.add_message(request, messages.SUCCESS, f'Orders uploaded')
        return HttpResponseRedirect(self.request.get_full_path())


@method_decorator(xframe_options_sameorigin, name='dispatch')
class ReviewView(DetailView, PermissionView):
    template_name = "order/review.html"

    def get_object(self):
        return get_object_or_404(models.Order, public_id=self.kwargs["public_id"])

    def post(self, request, *args, **kwargs):
        rating = self.request.POST.get("rating", None)
        comment = self.request.POST.get("comment", None)
        if rating is not None:
            rating = int(rating)
            order = self.get_object()
            order.rating = rating
            order.review = comment
            order.datetime_reviewed = timezone.now()
            order.save()

            rider = order.rider
            if rider:
                rt = Order.objects.filter(rider=rider, rating__gt=0).aggregate(
                    _avg=Avg(Order.rating.field.name))
                average_rating = rt['_avg']
                average_rating = 0.0 if average_rating is None else average_rating

                rider.rating = average_rating
                rider.save()

            messages.add_message(request, messages.SUCCESS,
                                 f'Thank you for your feedback')
        return HttpResponseRedirect(self.request.get_full_path())


class OrdersJsonView(PermissionView):
    def get_paginator(self):
        s = self.request.GET.get('s', '')
        page = self.request.GET.get('page', 1)
        order = self.request.GET.get('order', 'desc')
        per_page = self.request.GET.get('per_page', 100)
        order_by = self.request.GET.get('order_by', 'modified')

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        before_today = today - timedelta(days=7)

        end_date = self.request.GET.get(
            'end_date', today.strftime("%b %d, %Y"))
        start_date = self.request.GET.get(
            'start_date', before_today.strftime("%b %d, %Y"))
        _end_date = timezone.make_aware(
            datetime.strptime(end_date.strip(), '%b %d, %Y'))
        _start_date = timezone.make_aware(
            datetime.strptime(start_date.strip(), '%b %d, %Y'))
        date_range = [_start_date, _end_date+timedelta(days=1)]

        _order = '-' if not validators.truthy(order) or order == 'desc' else ''
        _order_by = 'modified' if not validators.truthy(order_by) else order_by
        _order_by = f'{_order}{_order_by}'
        per_page = 100 if not validators.truthy(per_page) else per_page

        q = models.Order.objects.filter(
            rider__isnull=True,
            datetime_ordered__range=date_range,
            organization=self.get_current_organization(),
        )
        if validators.truthy(s):
            s = s.strip()
            q = models.Order.objects.filter(
                (
                    Q(pk__icontains=s) |
                    Q(ref__icontains=s) |
                    Q(pickup_location_name__icontains=s) |
                    Q(pickup_location_name_more__icontains=s) |
                    Q(dropoff_location_name__icontains=s) |
                    Q(dropoff_location_name_more__icontains=s)
                )
                & Q(rider__isnull=True)
                & Q(datetime_ordered__range=date_range)
                & Q(organization=self.get_current_organization())
            )

        query = q.prefetch_related().order_by(_order_by)
        paginator = Paginator(query, per_page)
        return (paginator, page, per_page, start_date, end_date, order, order_by, s)

    def to_json(self):
        paginator, page, per_page, start_date, end_date, order, order_by, s = self.get_paginator()
        count = paginator.count
        num_pages = paginator.num_pages
        orders = []
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = []

        for item in items:
            orders.append(item.to_dict())
        return {
            'items': orders,
            'count': count,
            'num_pages': num_pages,
            'page': page,
            'per_page': per_page,
            'start_date': start_date,
            'end_date': end_date,
            'order': order,
            'order_by': order_by,
            's': s
        }

    def get(self, request):
        return JsonResponse(request, self.to_json())

    def post(self, request):
        return JsonResponse(request, self.to_json())


@method_decorator(csrf_exempt, name='dispatch')
class RouteJsonView(PermissionView):

    def get(self, request):
        return JsonResponse(request, {})

    def post(self, request):
        order_ids = self.request.POST.getlist('orders[]')
        order_ids = list(filter(None, order_ids))
        order_ids = list(set(order_ids))

        vehicle_ids = self.request.POST.getlist('vehicles[]')
        vehicle_ids = list(filter(None, vehicle_ids))
        vehicle_ids = list(set(vehicle_ids))

        orders = Order.objects.filter(pk__in=order_ids)
        vehicles = Vehicle.objects.filter(pk__in=vehicle_ids)

        dts = self.request.POST.get('delivery_start_time', None)
        midnight = datetime.strptime(dts, '%d.%m.%Y %H:%M') if validators.truthy(
            dts) else datetime.combine(date.today(), datetime.min.time())

        lt = self.request.POST.get('loading_time', None)
        loading_time = int(lt) * 60 if validators.truthy(lt) else 300

        ss_end = self.request.POST.get('ss_end', None)
        ss_end = int(ss_end) if validators.truthy(ss_end) else -1
        ss_start = self.request.POST.get('ss_start', None)
        ss_start = int(ss_start) if validators.truthy(ss_start) else -1

        mo = self.request.POST.get('maximum_orders', None)
        maximum_orders = int(mo) if validators.truthy(mo) else 10

        vo = self.request.POST.get('vehicle_option', None)
        vehicle_option = int(vo) if validators.truthy(vo) else 3

        jobs = []
        x = 0
        shipments = []
        maximum_orders = maximum_orders if maximum_orders > 0 else 100
        for order in orders:
            if (
                    not validators.truthy(order.pickup_lat) or
                    not validators.truthy(order.pickup_lng) or
                    not validators.truthy(order.dropoff_lat) or
                    not validators.truthy(order.dropoff_lng)
            ):
                continue

            lat = float(order.pickup_lat)
            lng = float(order.pickup_lng)
            pickup = {
                'id': order.pk,
                'location': [lng, lat],
                'service': loading_time,
                'description': f'{order.pk} P'
            }
            # jobs.append({"id":x,"location":[lng,lat], "delivery" : [1], 'description' : f'order.pickup_location_name - pickup Order #{order.pk}'})
            lat = float(order.dropoff_lat)
            lng = float(order.dropoff_lng)
            # jobs.append({"id":x,"location":[lng,lat], "delivery" : [1], 'description' : f'{order.dropoff_location_name} - dropoff Order #{order.pk}'})
            delivery = {
                'id': order.pk,
                'location': [lng, lat],
                'service': loading_time,
                'description': f'{order.pk} D'
            }
            width = max(int(order.width), 1) if validators.truthy(
                order.width) else 1
            weight = max(int(order.weight), 1) if validators.truthy(
                order.weight) else 1
            length = max(int(order.length), 1) if validators.truthy(
                order.length) else 1
            height = max(int(order.height), 1) if validators.truthy(
                order.height) else 1

            shipments.append({"amount": [
                             1, weight, length, width, height], 'pickup': pickup, "delivery": delivery})
            print(1, weight, length, width, height)

        _vehicles = []
        time0 = int(datetime.timestamp(midnight))
        for vehicle in vehicles:
            service_window_end = ss_end if ss_end > -1 else vehicle.service_end
            service_window_start = ss_start if ss_start > -1 else vehicle.service_start
            time1 = time0 + (service_window_start * 3600)
            time2 = time0 + (service_window_end * 3600)

            width = max(int(vehicle.width), 1)
            weight = max(int(vehicle.weight), 1)
            length = max(int(vehicle.length), 1)
            height = max(int(vehicle.height), 1)

            print(maximum_orders, weight, length, width, height)
            _vehicle = {
                'description': f'{vehicle.pk} V',
                'capacity': [maximum_orders, weight, length, width, height],
                'id': vehicle.pk,
                'time_window': [time1, time2]
            }
            if vehicle_option == 1:
                _vehicle['start'] = [vehicle.lng, vehicle.lat]
            elif vehicle_option == 2:
                _vehicle['end'] = [vehicle.lng, vehicle.lat]
            else:
                _vehicle['start'] = [vehicle.lng, vehicle.lat]
                _vehicle['end'] = [vehicle.lng, vehicle.lat]

            _vehicles.append(_vehicle)

        url = f"http://192.241.146.193:3000"
        HEADERS = {'Content-Type': 'application/json'}

        data = {"vehicles": _vehicles,
                "shipments": shipments, "options": {"g": True}}
        print(data)
        r = requests.post(url, headers=HEADERS, json=data)
        print(r.text)
        return JsonResponse(request, r.json())
