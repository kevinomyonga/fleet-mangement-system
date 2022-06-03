from django.conf import settings
from organization.models import OrganizationSmsProvider
from .infobip import infobip_send_sms
from .africastalking import africastalking_send_sms
from .vaspro import vaspro_send_sms
from .vonage import vonage_send_sms
from .twilio import twilio_send_sms

def send_sms(organization, phone_number, message):

    # check if the organization has a custom sms gateway
    has_custom_gateway = OrganizationSmsProvider.objects.filter(organization=organization).exists()

    # AFRICASTALKING = 1
    # INFOBIP = 2
    # VONAGE = 3
    # TWILIO = 4
    # VASPRO = 5
    if has_custom_gateway:

        provider_details = OrganizationSmsProvider.objects.get(organization=organization)
        provider = provider_details.provider
        sender_id = provider_details.sender_id
        api_key = provider_details.api_key
        username = provider_details.username
        base_url = provider_details.base_url
        api_secret = provider_details.api_secret
        account_sid = provider_details.account_sid
        auth_token = provider_details.auth_token

        if 	provider == 1 and api_key and username and sender_id:
            africastalking_send_sms(api_key, username, sender_id, phone_number, message )

        elif provider == 2 and base_url and api_key and sender_id:
            infobip_send_sms(base_url, api_key, sender_id, message, phone_number)	

        elif provider == 3 and api_key and api_secret and sender_id:
            vonage_send_sms(api_key, api_secret, sender_id, phone_number, message)

        elif provider == 4 and account_sid and auth_token and sender_id:
            twilio_send_sms(account_sid, auth_token, sender_id, phone_number, message)

        elif provider == 5 and api_key and sender_id:
            vaspro_send_sms(api_key, sender_id, phone_number, message)

        else:
            api_key = settings.DEFAULT_AFRICASTALKING_API_KEY
            username = settings.DEFAULT_AFRICASTALKING_USERNAME
            sender_id = settings.DEFAULT_AFRICASTALKING_SENDER_ID

            africastalking_send_sms(api_key, username, sender_id, phone_number, message )

    else:
        api_key = settings.DEFAULT_AFRICASTALKING_API_KEY
        username = settings.DEFAULT_AFRICASTALKING_USERNAME
        sender_id = settings.DEFAULT_AFRICASTALKING_SENDER_ID

        africastalking_send_sms(api_key, username, sender_id, phone_number, message )
