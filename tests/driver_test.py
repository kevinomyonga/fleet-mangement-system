import requests, json, secrets

PHONE_NUMBER = 254704119181

ENDPOINT = 'https://business.getboda.co.ke/api/v1'
token = '1dcf80ba34b11151b8cbc9daead36a92dee6d7df3eeb53c6df6a3effec67529c'

ENDPOINT = 'http://127.0.0.1:8000/api/v1'
token = '1ff6820cba140265c20af4896d56321372ecf9e0e465e0b138fdd2c984fceb56'

# Getting the verifcation code
# /driver/phone/code

headers = {'Content-Type' : 'application/json'}
'''
url = f'{ENDPOINT}/driver/phone/code'
print(url)
payload = {'phone_number' : PHONE_NUMBER}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

code = input('Enter code: ')
url = f'{ENDPOINT}/driver/phone/verify'
print(url)
payload = {'phone_number' : PHONE_NUMBER, 'code' : code}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)
token = r['tokens']['server_token']
'''

headers = {'Content-Type' : 'application/json', 'Authorization' : f'Token {token}' }
print(headers)
url = f'{ENDPOINT}/driver/profile'
print(url)
r = requests.get(url, headers=headers).json()
print(r)

'''
password = "Test#1234"
#password = secrets.token_hex(4)
print("Password is ", password)

url = f'{ENDPOINT}/driver/passwd'
print(url)
payload = {'password' : password, 'confirm_password' : password}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
token = r['tokens']['server_token']
headers = {'Content-Type' : 'application/json', 'Authorization' : f'Token {token}' }

url = f'{ENDPOINT}/driver/profile/update'
print(url)
payload = {'first_name' : "James", 'last_name' : 'Atong'}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)


password = "101e9006"
#password = 'Test#1234'
print("Password is ", password)

headers = {'Content-Type' : 'application/json'}
url = f'{ENDPOINT}/driver/auth'
print(url)
payload = {'password' : password, 'phone_number' : PHONE_NUMBER}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)


token = r['tokens']['server_token']
headers = {'Content-Type' : 'application/json', 'Authorization' : f'Token {token}' }



'''
url = f'{ENDPOINT}/driver/profile'
print(url)
r = requests.post(url, headers=headers).json()
print(r)

organizations = r['organizations']
print(organizations)
for organization in organizations:
	organization_id = organization['ID']
	payload = {}
	url = f'{ENDPOINT}/driver/order/stats?organization_id={organization_id}'
	print(url)
	payload = {}
	r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
	print(r)
	url = f'{ENDPOINT}/driver/order/routes?organization_id={organization_id}'
	payload = {'token': "TEST-TOKEN"}
	r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
	print(r)




payload = {}
url = f'{ENDPOINT}/driver/location/update'
print(url)
payload = {
	'lat': -1.254766,
	'lng': 36.797427
}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

url = f'{ENDPOINT}/driver/profile'
print(url)
r = requests.post(url, headers=headers).json()
print(r)

organizations = r['organizations']
print(organizations)
for organization in organizations:
	organization_id = organization['ID']
	url = f'{ENDPOINT}/driver/order/routes?organization_id={organization_id}'
	payload = {'token': "TEST-TOKEN"}
	r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
	print(r)

exit()

url = f'{ENDPOINT}/driver/fcm/update'
payload = {'token': "TEST-TOKEN"}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)


payload = {'ids' : [3465]}
url = f'{ENDPOINT}/driver/order/accept'
print(url)
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

payload = {'ids' : [3465]}
url = f'{ENDPOINT}/driver/order/start'
print(url)
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)


payload = {'payment_method' : 1}
url = f'{ENDPOINT}/driver/order/3465/change-payment-method'
print(url)
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

payload = {'payment_method' : 2}
url = f'{ENDPOINT}/driver/order/3465/change-payment-method'
print(url)
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

payload = {'payment_method' : 3}
url = f'{ENDPOINT}/driver/order/3465/change-payment-method'
print(url)
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

payload = {'payment_method' : 4}
url = f'{ENDPOINT}/driver/order/3465/change-payment-method'
print(url)
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)


payload = {}
url = f'{ENDPOINT}/driver/order/3465/arrived'
print(url)
r = requests.get(url, headers=headers, data=json.dumps(payload)).json()
print(r)

payload = {}
url = f'{ENDPOINT}/driver/order/3465/complete'
print(url)
payload = {
	'signature' : 'https://homepages.cae.wisc.edu/~ece533/images/airplane.png',
	'pod_images' :  ['https://homepages.cae.wisc.edu/~ece533/images/arctichare.png', 'https://homepages.cae.wisc.edu/~ece533/images/barbara.png'],
	'lat': -1.254766,
	'lng': 36.797427,
	'payment_notes' : 'Mpesa Code: PPBBPPBPBO57'
}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

exit()


url = f'{ENDPOINT}/driver/profile'
print(url)
r = requests.post(url, headers=headers).json()
print(r)

organizations = r['organizations']
print(organizations)
for organization in organizations:
	organization_id = organization['ID']
	url = f'{ENDPOINT}/driver/order/filter?organization_id={organization_id}'
	print(url)
	r = requests.post(url, headers=headers).json()
	print(r)

	orders = r['items']
	for order in orders:
		order_id = order['ID']
		url = f'{ENDPOINT}/driver/order/{order_id}'
		print(url)
		r = requests.get(url, headers=headers).json()
		print(r)


payload = {'ids' : [174]}
url = f'{ENDPOINT}/driver/order/accept'
print(url)
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

payload = {'ids' : [174]}
url = f'{ENDPOINT}/driver/order/start'
print(url)
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)


payload = {}
url = f'{ENDPOINT}/driver/order/174/arrived'
print(url)
r = requests.get(url, headers=headers, data=json.dumps(payload)).json()
print(r)

payload = {}
url = f'{ENDPOINT}/driver/order/174/complete'
print(url)
payload = {
	'signature' : 'https://homepages.cae.wisc.edu/~ece533/images/airplane.png',
	'pod_images' :  ['https://homepages.cae.wisc.edu/~ece533/images/arctichare.png', 'https://homepages.cae.wisc.edu/~ece533/images/barbara.png'],
	'lat': -1.254766,
	'lng': 36.797427,
	'payment_notes' : 'Mpesa Code: PPBBPPBPBO57'
}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

payload = {}
url = f'{ENDPOINT}/driver/order/148/fail'
print(url)
payload = {
	'reason': 'too far',
	'lat': -1.254766,
	'lng': 36.797427
}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

url = f'{ENDPOINT}/driver/location/update'
print(url)
payload = {
	'lat': -1.254766,
	'lng': 36.797427
}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)

url = f'{ENDPOINT}/driver/profile/update'
print(url)
payload = {
	'first_name' : "John",
	'last_name' : 'Doe',
	'avatar' : 'https://homepages.cae.wisc.edu/~ece533/images/arctichare.png',
	'thumbnail' : 'https://homepages.cae.wisc.edu/~ece533/images/airplane.png'
}
r = requests.post(url, headers=headers, data=json.dumps(payload)).json()
print(r)
