import requests

def vaspro_send_sms(api_key, sender_id, recepient, message):
    request = {
            "apiKey":  api_key,
            "shortCode": sender_id,
            "recipient": recepient,
            "enqueue": 0,
            "message": message,
            "callbackURL":""
        }

    try:
        response = requests.post('https://api.vaspro.co.ke/v3/BulkSMS/api/create', json=request)
        response_data = response.json()
        print(response_data)
        return 0
        
    except Exception as e:
        print(e)
        return 1
