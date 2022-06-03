import africastalking

def africastalking_send_sms(api_key, username, sender_id, recipient, message):
    africastalking.initialize(
        username=username,
        api_key=api_key
    )
    sms = africastalking.SMS

    recipient = f'+{recipient}'

    try:
        response = sms.send(message, [recipient], sender_id)
        print(response)
        return 0
        
    except Exception as e:
        print(e)
        return 1
