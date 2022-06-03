from django.db import models
from user.models import User
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=75)
    country = models.CharField(max_length=255)
    timezone = models.CharField(max_length=75)
    is_active = models.BooleanField(default=True)
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    callback_url = models.URLField(max_length=2048, null=True)
    sync_callback_url = models.URLField(max_length=2048, null=True)
    googlemap_api_key = models.CharField(max_length=255, null=True)
    send_order_received_sms = models.BooleanField(default=True)
    send_driver_assign_sms = models.BooleanField(default=True)
    send_driver_reassign_sms = models.BooleanField(default=True)
    send_driver_start_sms = models.BooleanField(default=False)
    send_driver_complete_sms = models.BooleanField(default=True)
    allow_driver_to_self_assign_orders = models.BooleanField(default=False)

    order_received_sms = models.CharField(
        max_length=150, default="Hi {{first_name}}, your order #{{order_ref}} has be been received and will be dispatched shortly.")
    driver_assign_sms = models.CharField(
        max_length=150, default="A rider has been assigned to your order #{{order_ref}}. {{rider_name}} will contact you on  {{rider_phone}}")
    driver_reassign_sms = models.CharField(
        max_length=150, default="A different rider has been assigned to your order #{{order_ref}}. {{rider_name}} will contact you on  {{rider_phone}}")
    driver_start_sms = models.CharField(
        max_length=150, default="Your rider is on the way. {{rider_name}} will contact you on {{rider_phone}}")
    driver_complete_sms = models.CharField(
        max_length=150, default="Thank you. How was your experience. Leave us a rating.")

    def members(self):
        return OrganizationUser.objects.filter(organization=self, deleted=False)

    def mpesa_details(self):
        return OrganizationMpesaDetails.objects.get(organization=self)


class OrganizationUser(models.Model):
    deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'organization']


class OrganizationInvite(models.Model):
    name = models.CharField(max_length=75)
    email = models.EmailField(max_length=255)
    deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=48, unique=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['email', 'organization']


class OrganizationSmsProvider(models.Model):
    AFRICASTALKING = 1
    INFOBIP = 2
    VONAGE = 3
    TWILIO = 4
    VASPRO = 5
    PROVIDERS = [
        (AFRICASTALKING, 'Africa\'s talking'),
        (INFOBIP, 'Infobip'),
        (VONAGE, 'Vonage'),
        (TWILIO, 'Twilio'),
        (VASPRO, 'Vaspro'),
    ]

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
    provider = models.PositiveSmallIntegerField(
        choices=PROVIDERS, default=None)
    sender_id = models.CharField(max_length=150)
    api_key = models.CharField(max_length=200, null=True, blank=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    base_url = models.URLField(null=True, blank=True)
    api_secret = models.CharField(max_length=200, null=True, blank=True)
    account_sid = models.CharField(max_length=200, null=True, blank=True)
    auth_token = models.CharField(max_length=200, null=True, blank=True)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    verified = models.BooleanField(default=False)


class OrganizationMpesaDetails(models.Model):
    DARAJA = 1
    KOPOKOPO = 2
    IMPLEMENTATIONS = [
        (DARAJA, 'Daraja'),
        (KOPOKOPO, 'Kopokopo'),
    ]
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
    implementation = models.PositiveSmallIntegerField(
        choices=IMPLEMENTATIONS, default=None)
    business_short_code = models.CharField(
        max_length=20, null=True, blank=True)
    consumer_key = models.CharField(max_length=300, null=True, blank=True)
    consumer_secret = models.CharField(max_length=300, null=True, blank=True)
    pass_key = models.CharField(max_length=300, null=True, blank=True)
    client_id = models.CharField(max_length=300, null=True, blank=True)
    client_secret = models.CharField(max_length=300, null=True, blank=True)
    till_number = models.CharField(max_length=20, null=True, blank=True)
