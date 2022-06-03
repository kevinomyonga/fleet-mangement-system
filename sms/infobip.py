from infobip_api_client.api_client import ApiClient, Configuration
from infobip_api_client.model.sms_advanced_textual_request import SmsAdvancedTextualRequest
from infobip_api_client.model.sms_destination import SmsDestination
from infobip_api_client.model.sms_response import SmsResponse
from infobip_api_client.model.sms_textual_message import SmsTextualMessage
from infobip_api_client.api.send_sms_api import SendSmsApi
from infobip_api_client.exceptions import ApiException
import requests, json

def infobip_send_sms(base_url, api_key, sender_id, message, recepient):
	payload = {
	  "messages": [
		{
		  "from": sender_id,
		  "destinations": [{"to": recepient}],
		  "text": message,
		  "flash": False
		},
	  ],
	}
	url = f"{base_url}/sms/2/text/advanced"
	authorization = f'App {api_key}'
	headers = {
		'Content-Type': 'application/json',
		'Authorization' : authorization,
		'Accept': 'application/json'
	}
	return requests.post(url, data=json.dumps(payload), headers=headers)
