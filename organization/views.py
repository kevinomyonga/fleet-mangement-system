from . import forms
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import DurationField, F, ExpressionWrapper
from django.views.generic.base import RedirectView, TemplateView
from django.views import View
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.template.loader import get_template
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout, login
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.db import IntegrityError

from sms.infobip import infobip_send_sms
from sms.africastalking import africastalking_send_sms
from sms.vaspro import vaspro_send_sms
from sms.vonage import vonage_send_sms
from sms.twilio import twilio_send_sms
from organization.models import Organization, OrganizationUser, OrganizationInvite, OrganizationSmsProvider
from rest_framework import status
from rest_framework.response import Response
from django.http import Http404

from .kopokopo import push_stk_request
from django.conf import settings


from order.models import STKPushRequest, MpesaPayments
from user.models import User, VerifyEmailToken
from organization.http import PermissionView
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg
from django.conf import settings
from order.models import Order
import validators
import random
import secrets

from .forms import AddMpesaDetailsForm
from .mpesa import push_request
from rest_framework.response import Response
# from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from organization.mpesa import getTime

from api.utils import payment_made_driver_push

from datetime import datetime

import logging
logger = logging.getLogger(__name__)


class DashboardView(TemplateView, PermissionView):
    template_name = "organization/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        if not user.is_email_verified:
            url = reverse_lazy('accounts:verify')
            is_old = True
            try:
                verify_token = VerifyEmailToken.objects.get(user=user)
                is_old = verify_token.is_old()
            except VerifyEmailToken.DoesNotExist:
                verify_token = None

            if is_old:
                messages.add_message(
                    self.request, messages.ERROR, f'You have not verified your email, <a href="{url}">Click here</a> to verify your email')

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

        delivered = Order.objects.filter(
            rider__isnull=False,
            datetime_completed__range=date_range,
            state=Order.DELIVERED,
            organization=self.get_current_organization(),
        ).count()
        failed = Order.objects.filter(
            datetime_ordered__range=date_range,
            state__in=(
                Order.FAILED_AT_CLIENT,
                Order.SUBMITTED_RETURN_TO_WAREHOUSE,
                Order.COMPLETED_TO_WAREHOUSE,
                Order.SUBMITTED_RETURN_TO_VENDOR,
                Order.COMPLETED_TO_VENDOR
            ),
            organization=self.get_current_organization(),
        ).count()
        in_progress = Order.objects.filter(
            datetime_ordered__range=date_range,
            state__in=(
                Order.DRAFT,
                Order.SUBMITTED_PENDING_VENDOR_PICK_UP,
                Order.SUBMITTED_PENDING_FOWARD_DELIVERY,
                Order.DISPATCHED,
                Order.ARRAVAL_AT_CLIENT
            ),
            organization=self.get_current_organization()
        ).count()
        total = Order.objects.filter(
            datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        context['end_date'] = end_date
        context['start_date'] = start_date
        context['total'] = total
        context['failed'] = failed
        context['delivered'] = delivered
        context['in_progress'] = in_progress

        review_count = Order.objects.filter(
            datetime_reviewed__range=date_range,
            organization=self.get_current_organization(),
        ).exclude(rating__isnull=True).count()
        context['review_count'] = review_count

        payment_count = Order.objects.filter(
            paid=False,
            rider__isnull=False,
            datetime_completed__range=date_range,
            state=Order.DELIVERED,
            payment_method=Order.POSTPAID,
            organization=self.get_current_organization(),
        ).count()
        context['payment_count'] = payment_count

        chart_days = []
        chart_counts = []
        for x in range(30, -1, -1):
            _date0 = today-timedelta(days=x)
            _date1 = _date0+timedelta(days=1)
            _date_range = [_date0, _date1]
            _count = Order.objects.filter(
                rider__isnull=False,
                datetime_completed__range=_date_range,
                state=Order.DELIVERED,
                organization=self.get_current_organization(),
            ).count()
            chart_days.append(_date0.strftime("%d %b"))
            chart_counts.append(_count)

        context['dom'] = chart_days
        context['oom'] = chart_counts

        context['r5_count'] = Order.objects.filter(
            rating__gte=5.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        context['r4_count'] = Order.objects.filter(
            rating__gte=4.0, rating__lt=5.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        context['r3_count'] = Order.objects.filter(
            rating__gte=3.0, rating__lt=4.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        context['r2_count'] = Order.objects.filter(
            rating__gte=2.0, rating__lt=3.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        context['r1_count'] = Order.objects.filter(
            rating__gt=0.0, rating__lt=2.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        context['rating_count'] = Order.objects.filter(
            rating__gt=0.0, datetime_ordered__range=date_range, organization=self.get_current_organization()).count()
        rt = Order.objects.filter(rating__gt=0.0, datetime_ordered__range=date_range,
                                  organization=self.get_current_organization()).aggregate(_avg=Avg(Order.rating.field.name))
        average_rating = rt['_avg']
        average_rating = 0.0 if average_rating is None else average_rating
        context['average_rating'] = average_rating

        context['h_0_1hrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=0), timedelta(seconds=3600)]).count()

        context['h_1_2hrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=3601), timedelta(seconds=7200)]).count()

        context['h_2_3hrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=7201), timedelta(seconds=10800)]).count()

        context['h_3_4hrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=10801), timedelta(seconds=14400)]).count()

        context['h_4_6hrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=14401), timedelta(seconds=21600)]).count()

        context['h_6_8hrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=21601), timedelta(seconds=28800)]).count()

        context['h_8_12hrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=28801), timedelta(seconds=43200)]).count()

        context['h_12_24hrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__range=[timedelta(seconds=43201), timedelta(seconds=86400)]).count()

        context['h_otherHrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__gte=timedelta(seconds=86401)).count()

        context['countHrs'] = Order.objects.annotate(
            diff=ExpressionWrapper(F(Order.datetime_completed.field.name) - F(
                Order.datetime_ordered.field.name), output_field=DurationField())
        ).filter(organization=self.get_current_organization(), datetime_ordered__range=date_range, diff__gte=timedelta(seconds=0)).count()

        return context


class CreateView(TemplateView):
    template_name = "organization/create.html"


class ItemView(DetailView):
    template_name = "organization/detail.html"

    def get_object(self):
        return get_object_or_404(
            Organization,
            pk=self.kwargs["pk"],
            owner=self.request.user
        )

    def post(self, request, *args, **kwargs):
        organization = self.get_object()

        order_recieved = self.request.POST.get("order_recieved", None)
        if order_recieved is None:
            organization.send_order_received_sms = False
        else:
            organization.send_order_received_sms = True

        driver_assigned = self.request.POST.get("driver_assigned", None)
        if driver_assigned is None:
            organization.send_driver_assign_sms = False
        else:
            organization.send_driver_assign_sms = True

        driver_reassigned = self.request.POST.get("driver_reassigned", None)
        if driver_reassigned is None:
            organization.send_driver_reassign_sms = False
        else:
            organization.send_driver_reassign_sms = True

        driver_started = self.request.POST.get("driver_started", None)
        if driver_started is None:
            organization.send_driver_start_sms = False
        else:
            organization.send_driver_start_sms = True

        order_completed = self.request.POST.get("order_completed", None)
        if order_completed is None:
            organization.send_driver_complete_sms = False
        else:
            organization.send_driver_complete_sms = True

        # id_allow_driver_to_self_assign_orders
        allow_driver_to_self_assign_orders = self.request.POST.get(
            "allow_driver_to_self_assign_orders", None)
        if allow_driver_to_self_assign_orders is None:
            organization.allow_driver_to_self_assign_orders = False
        else:
            organization.allow_driver_to_self_assign_orders = True

        #order_completed = self.request.POST.get("order_completed", None)

        callback_url = self.request.POST.get("callback_url", None)
        if validators.truthy(callback_url) and validators.url(callback_url):
            organization.callback_url = callback_url
        else:
            organization.callback_url = None

        googlemap_api_key = self.request.POST.get("googlemap_api_key", None)
        if validators.truthy(googlemap_api_key):
            organization.googlemap_api_key = googlemap_api_key
        else:
            organization.googlemap_api_key = None

        organization.save()

        return HttpResponseRedirect(self.request.get_full_path())


class OrganizationJoinView(DetailView):
    template_name = "organization/join.html"

    def get_object(self):
        return get_object_or_404(
            OrganizationInvite,
            token=self.kwargs["token"],
            deleted=False,
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _obj = self.get_object()
        try:
            user = User.objects.get(email=_obj.email)
        except User.DoesNotExist:
            user = None
        context['user'] = user
        return context

    def get(self, request, *args, **kwargs):
        _obj = self.get_object()
        if request.user.is_authenticated and _obj.email != request.user.email:
            email = request.user.email
            logout(request)
            messages.add_message(
                request, messages.ERROR, f'You have been logged out of account - {email}.')

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        _obj = self.get_object()
        organization = _obj.organization

        do_password = request.POST.get("do_password", None)
        if do_password is not None:
            password = self.request.POST.get("password", None)
            confirm_password = self.request.POST.get("confirm_password", None)
            if password is None or confirm_password is None or \
                    len(password.strip()) < 6 or len(confirm_password.strip()) < 6 or \
                    password.strip() != confirm_password.strip():
                messages.add_message(
                    request, messages.ERROR, f'Check your passwords and try again')
                return HttpResponseRedirect(self.request.get_full_path())

            name = _obj.name
            email = _obj.email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(email, password.strip(), name)

            organisation_user, created = OrganizationUser.objects.get_or_create(
                user=user,
                organization=organization
            )
            organisation_user.deleted = False
            organisation_user.is_active = True
            organisation_user.save()

            login(self.request, user)
            self.request.session["organization_user_id"] = organisation_user.pk
            messages.add_message(
                request, messages.INFO, f'You are now a member of <b>{organization.name}</b>')
            return HttpResponseRedirect(reverse_lazy('dashboard'))

        no_do_password = request.POST.get("no_do_password", None)
        if no_do_password is not None:
            email = _obj.email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(email, password.strip(), name)

            organisation_user, created = OrganizationUser.objects.get_or_create(
                user=user,
                organization=organization
            )
            organisation_user.deleted = False
            organisation_user.is_active = True
            organisation_user.save()

            login(self.request, user)
            self.request.session["organization_user_id"] = organisation_user.pk
            messages.add_message(
                request, messages.INFO, f'You are now a member of <b>{organization.name}</b>')
            return HttpResponseRedirect(reverse_lazy('dashboard'))

        return HttpResponseRedirect(self.request.get_full_path())


class OrganizationAddUserView(TemplateView, PermissionView):
    template_name = "organization/add_user.html"

    def post(self, request, *args, **kwargs):
        organization = self.get_current_organization()
        email = self.request.POST.get("email", None)
        if not validators.truthy(email) or not validators.truthy(email):
            messages.add_message(request, messages.ERROR, f'Invalid email')
            return HttpResponseRedirect(self.request.get_full_path())

        name = self.request.POST.get("name", None)
        if not validators.truthy(name):
            messages.add_message(request, messages.ERROR,
                                 f'Enter a valid name')
            return HttpResponseRedirect(self.request.get_full_path())

        email = email.strip()
        try:
            organization_user = OrganizationUser.objects.get(
                organization=organization,
                user__email=email,
                deleted=False,
                is_active=True
            )
        except OrganizationUser.DoesNotExist:
            organization_user = None

        if organization_user is not None:
            messages.add_message(
                request, messages.ERROR, f'<b>{email}</b> is already a member of the organization')
            return HttpResponseRedirect(self.request.get_full_path())

        invite, created = OrganizationInvite.objects.get_or_create(
            email=email,
            organization=self.get_current_organization()
        )
        invite.name = name
        invite.token = secrets.token_hex(16)
        invite.save()

        scheme = self.request.scheme
        host = self.request.META['HTTP_HOST']
        url = f'{scheme}://{host}'
        invited_by = request.user.first_name

        member_join_url = "%s%s" % (url, reverse_lazy(
            'organization:join', kwargs={'token': invite.token}))
        email_template_txt = get_template("organization/email/add_user.txt")
        email_template_html = get_template("organization/email/add_user.html")
        data = {
            'name': name,
            'invited_by': invited_by,
            'member_join_url': member_join_url,
            'organization_name': organization.name
        }
        email_txt = email_template_txt.render(data)
        email_html = email_template_html.render(data)
        subject = f'{invited_by} has invited you to join {organization.name}'

        message = Mail(
            subject=subject,
            to_emails=email,
            html_content=email_html,
            plain_text_content=email_txt,
            from_email=settings.DEFAULT_FROM_EMAIL
        )
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
        except Exception as e:
            messages.add_message(request, messages.ERROR,
                                 f'Something went wrong, please try again later')
            return HttpResponseRedirect(self.request.get_full_path())

        messages.add_message(request, messages.SUCCESS,
                             f'An invite has been sent to <b>{name} - {email}</b>')
        return HttpResponseRedirect(self.request.get_full_path())


class OrganizationAddSmsGateway(PermissionView):
    template_name = "organization/add_sms_gateway.html"
    form_class = forms.AddSmsGatewayForm

    def get(self, request, *args, **kwargs):
        # get the current sms gateway settings
        organization = self.get_current_organization()

        try:
            sms_gateway = OrganizationSmsProvider.objects.get(
                organization=organization)
            form = self.form_class(initial=sms_gateway)
        except Exception as e:
            form = self.form_class(None)

        return render(request, self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        organization = self.get_current_organization()
        code = random.randint(111111, 999999)
        updated_request = request.POST.copy()
        updated_request.update({
            'organization': organization.pk,
            'verification_code': code
        })
        form = self.form_class(updated_request)

        if form.is_valid():
            provider = form.cleaned_data['provider']
            sender_id = form.cleaned_data['sender_id']
            api_key = form.cleaned_data['api_key']
            username = form.cleaned_data['username']
            base_url = form.cleaned_data['base_url']
            api_secret = form.cleaned_data['api_secret']
            account_sid = form.cleaned_data['account_sid']
            auth_token = form.cleaned_data['auth_token']
            phone_number = form.cleaned_data['phone_number']

            message = f'Your verification code is {code}'

            # test gateway settings and save details if the test was successful
            if provider == '1' and api_key and username and sender_id:
                return_value = africastalking_send_sms(
                    api_key, username, sender_id, phone_number, message)

                if return_value == 0:
                    form.save()
                    return redirect('organization:verify_sms_settings')
                else:
                    messages.add_message(
                        request, messages.ERROR, 'Your sms gateway settings are invalid.')

            elif provider == '2' and base_url and api_key and sender_id:
                return_value = infobip_send_sms(
                    base_url, api_key, sender_id, message, phone_number)

                if return_value == 0:
                    form.save()
                    return redirect('organization:verify_sms_settings')
                else:
                    messages.add_message(
                        request, messages.ERROR, 'Your sms gateway settings are invalid.')

            elif provider == '3' and api_key and api_secret and sender_id:
                return_value = vonage_send_sms(
                    api_key, api_secret, sender_id, phone_number, message)

                if return_value == 0:
                    form.save()
                    return redirect('organization:verify_sms_settings')
                else:
                    messages.add_message(
                        request, messages.ERROR, 'Your sms gateway settings are invalid.')

            elif provider == '4' and account_sid and auth_token and sender_id:
                return_value = twilio_send_sms(
                    account_sid, auth_token, sender_id, phone_number, message)

                if return_value == 0:
                    form.save()
                    return redirect('organization:verify_sms_settings')
                else:
                    messages.add_message(
                        request, messages.ERROR, 'Your sms gateway settings are invalid.')

            elif provider == '5' and api_key and sender_id:
                return_value = vaspro_send_sms(
                    api_key, sender_id, phone_number, message)

                if return_value == 0:
                    form.save()
                    return redirect('organization:verify_sms_settings')
                else:
                    messages.add_message(
                        request, messages.ERROR, 'Your sms gateway settings are invalid.')

            else:
                messages.add_message(
                    request, messages.ERROR, 'Please add valid sms gateway settings')

        else:
            print("==================errors========================")
            print(form.errors)
        return render(request, self.template_name, context={'form': form})


class VerifySmsSettings(PermissionView):
    template_name = 'organization/verify_sms_settings.html'
    form_class = forms.SmsDetailsVerificationForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            organization = self.get_current_organization()
            verification_code = form.cleaned_data.get('verification_code')
            try:
                org_sms_settings = OrganizationSmsProvider.objects.get(
                    organization=organization)
            except Exception as e:
                messages.add_message(
                    request, messages.ERROR, 'Sms gateway details does not exist')
                return render(request, self.template_name, {'form': form})

            if verification_code == org_sms_settings.verification_code:
                org_sms_settings.verified = True
                org_sms_settings.save()
                messages.add_message(
                    request, messages.SUCCESS, 'Your sms gateway settings added successfully')
                return HttpResponseRedirect(reverse_lazy('dashboard'))
            else:
                messages.add_message(
                    request, messages.ERROR, 'Please enter a valid code')
        return render(request, self.template_name, {'form': form})


class OrganizationAddMpesaDetails(PermissionView):
    template_name = 'organization/add_mpesa_details.html'
    form_class = AddMpesaDetailsForm

    def get(self, request, *args, **kwargs):
        try:
            form = self.form_class(None)
        except Exception as e:
            form = self.form_class(None)
        return render(request, self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        organization = self.get_current_organization()
        updated_request = request.POST.copy()
        updated_request.update({
            'organization': organization.pk
        })
        form = self.form_class(updated_request)

        if form.is_valid():
            implementation = int(form.cleaned_data.get('implementation'))
            # client_id = form.cleaned_data.get('client_id')
            # client_secret = form.cleaned_data.get('client_secret')
            # till_number = form.cleaned_data.get('till_number')
            # phone_number = form.cleaned_data.get('phone_number')
            # passkey = form.cleaned_data.get('pass_key')
            # consumer_key = form.cleaned_data.get('consumer_key')
            # consumer_secret = form.cleaned_data.get('consumer_secret')
            # business_short_code = form.cleaned_data.get('business_short_code')
            # amount = 1
            # account_reference = '1'
            # transaction_description = f'please to complete your mpesa settings'

            if implementation == 1:
                form.save()
                messages.add_message(
                    request, messages.SUCCESS, 'M-pesa details added successfully')
                return HttpResponseRedirect(reverse_lazy('organization:index'))

                # return_val = push_request(consumer_key, consumer_secret, passkey, business_short_code, amount, phone_number, account_reference, transaction_description)

                # if 'error_code' in return_val.keys():
                # 	messages.add_message(request, messages.ERROR, return_val.get('error_message'))
                # else:
                # 	form.save()
                # 	messages.add_message(request, messages.SUCCESS, 'M-pesa details added successfully')
                # 	return HttpResponseRedirect(reverse_lazy('organization:index'))
            elif implementation == 2:
                # kopokopo
                form.save()
                messages.add_message(
                    request, messages.SUCCESS, 'M-pesa details added successfully')
                return HttpResponseRedirect(reverse_lazy('organization:index'))
            else:
                messages.add_message(
                    request, messages.ERROR, 'Please select a valid implementation')
        else:
            messages.add_message(
                request, messages.ERROR, 'M-pesa details were not added. Please enter valid values')
        return render(request, self.template_name, context={'form': form})


@method_decorator(xframe_options_sameorigin, name='dispatch')
class OrganizationRemoveUserIframeView(DetailView, PermissionView):
    template_name = "organization/remove_user_iframe.html"

    def get_object(self):
        return get_object_or_404(
            OrganizationUser,
            pk=self.kwargs["organization_user_id"],
            organization__owner=self.request.user
        )

    def post(self, request, *args, **kwargs):
        remove = self.request.POST.get("remove", None)
        if validators.truthy(remove):
            _obj = self.get_object()
            _obj.deleted = True
            _obj.is_active = False
            _obj.save()

            messages.add_message(
                request, messages.SUCCESS, f'<b>{_obj.user.email}</b> has been removed from your organization <b>{_obj.organization.name}</b>')

        return HttpResponseRedirect(self.request.get_full_path())


class SwitchView(DetailView):
    def get_object(self):
        return get_object_or_404(OrganizationUser, user=self.request.user, pk=self.kwargs["organization_user_id"], deleted=False)

    def get(self, request, *args, **kwargs):
        _obj = self.get_object()
        organization_user_id = None
        if "organization_user_id" in self.request.session:
            organization_user_id = self.request.session['organization_user_id']

        request.session["organization_user_id"] = _obj.pk
        messages.add_message(
            request, messages.ERROR, f'Current organization is <b>{_obj.organization.name}</b>')
        return HttpResponseRedirect(reverse_lazy('dashboard'))


class RedirectView(RedirectView):
    permanent = False
    url = reverse_lazy('dashboard')

    def get_redirect_url(self, *args, **kwargs):
        if "organization_user_id" in self.request.session:
            organization_user_id = self.request.session['organization_user_id']

        return super().get_redirect_url(*args, **kwargs)


class STKPushCallback(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = {}
        data['MerchantRequestID'] = request.data['Body']['stkCallback']['MerchantRequestID']
        data['CheckoutRequestID'] = request.data['Body']['stkCallback']['CheckoutRequestID']
        data['ResultCode'] = request.data['Body']['stkCallback']['ResultCode']
        data['ResultDesc'] = request.data['Body']['stkCallback']['ResultDesc']

        if int(data['ResultCode']) > 0:
            return Response(data, status=status.HTTP_417_EXPECTATION_FAILED)

        else:
            items = request.data['Body']['stkCallback']['CallbackMetadata']['Item']

            for item in items:
                data[item.get('Name')] = item.get('Value')
            data["TransactionDate"] = getTime(data["TransactionDate"])

            MerchantRequestID = data['MerchantRequestID']
            CheckoutRequestID = data['CheckoutRequestID']

            # get order instance
            try:
                push_request = STKPushRequest.objects.get(
                    MerchantRequestID=MerchantRequestID,
                    CheckoutRequestID=CheckoutRequestID)
            except STKPushRequest.DoesNotExist:
                raise Http404

            order_id = push_request.AccountReference

            try:
                order = Order.objects.get(pk=order_id)
            except Order.DoesNotExist:
                raise Http404

            # update order paid flag

            payment = MpesaPayments()

            payment.MpesaReceiptNumber = data.get('MpesaReceiptNumber')
            payment.MerchantRequestID = data.get('MerchantRequestID')
            payment.CheckoutRequestID = data.get('CheckoutRequestID')
            payment.ResultCode = data.get('ResultCode')
            payment.ResultDesc = data.get('ResultDesc')
            payment.Amount = data.get('Amount')
            payment.PhoneNumber = data.get('PhoneNumber')
            payment.TransactionDate = getTime(data.get('TransactionDate'))
            payment.save()

            payment_made_driver_push(order)

            return Response({"desc": "success"}, status=status.HTTP_200_OK)


class KopokopoCallback(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        attributes = request.data.get('data').get('attributes')
        metadata = attributes.get('metadata')
        resource = attributes.get('event').get('resource')

        order_id = metadata.get('order_id')
        logger.debug(f'attributes {attributes}')

        if(attributes.get('status') == 'Success'):
            try:
                order = Order.objects.get(pk=order_id)
            except Order.DoesNotExist:
                raise Http404

            payment = MpesaPayments()
            payment.order = order
            payment.MpesaReceiptNumber = resource.get('reference')
            payment.Amount = resource.get('amount')
            payment.PhoneNumber = resource.get('sender_phone_number')
            payment.TransactionDate = datetime.fromisoformat(
                resource.get('origination_time'))
            payment.save()

            payment_made_driver_push(order, payment)

            return Response({"desc": "success"}, status=status.HTTP_200_OK)
        else:
            error = attributes.get('event')
            return Response(error, status=status.HTTP_412_PRECONDITION_FAILED)
