from datetime import datetime
import requests, json

TOKEN = '9eecd4bd8eabd19396da9af0dce0377aa050ca35'
ENDPOINT = 'http://127.0.0.1:8000'


#TOKEN = '10efdb2368075de6dfb2641da2cb1021f12502c5'
#ENDPOINT = 'https://business.getboda.co.ke'

#TOKEN = '7d4f3b2a647952a9a1c27a20286a6c4685a96fa1'
#ENDPOINT = 'https://business.getboda.co.ke'

#TOKEN = '10efdb2368075de6dfb2641da2cb1021f12502c5'
#ENDPOINT = 'https://business.getboda.co.ke'

HEADERS = {'Content-Type' : 'application/json', 'Authorization' : f'Token {TOKEN}' }

#authenticate
url = f'{ENDPOINT}/api/v1/user/profile'
print(url)
print(requests.post(url, headers=HEADERS).json())

url = f'{ENDPOINT}/api/v1/user/organizations'
print(url)
response = requests.post(url, headers=HEADERS).json()
print(response)


org_id = 1

url = f'{ENDPOINT}/api/v1/order/create'
print(url)
now = datetime.now()
order_ref = f'GBT{org_id}-{now.year}{now.month}{now.day}{now.hour}{now.minute}{now.second}'
payload = {
	'organization_id' : org_id,
	'order_ref' : order_ref,
	'pickup' : {
		'location' : {
			'addresss' : 'TRM Drive',
			'apartment' : 'Genesis Court',
			'coords' : {
				'lat': -1.254766,
				'lng': 36.797427
			}

		},
		'contact' : {
			'name' : 'James Atong',
			'email' : 'james@getboda.co.ke',
			'phone_number' : '254704119181'
		},
		'notes' : 'pickup - Dont ring the bell'
	},
	'dropoff' : {
		'location' : {
			'addresss' : 'TRM Drive',
			'apartment' : 'Genesis Court',
			'coords' : {
				'lat': -1.254766,
				'lng': 36.797427
			}

		},
		'contact' : {
			'name' : 'James Atong',
			'email' : 'james@getboda.co.ke',
			'phone_number' : '254704119181'
		},
		'notes' : 'dropoff - Dont ring the bell'
	},
	'notes' : 'Gordon’s (1)\r\nSchweppes Tonic Water (6)\r\nHesketh Bright Young Things Sauvignon Blanc (5)\r\n',
	'price' : 1.1,
	'length': 1.2,
	'width': 1.3,
	'height': 1.4,
	'weight': 1.5,
	'payment_method' : 1,

	'prefered_delivery_date' : '05-03-2021',
	'prefered_delivery_time' : 1,
}
print(payload)
r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
print(r.text)
print(r.json())
data = r.json()
_id = data.get('ID')
url = f'{ENDPOINT}/api/v1/order/{_id}'
print(url)
response = requests.post(url, headers=HEADERS).json()
print(response)
