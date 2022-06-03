from twilio.rest import Client

def twilio_send_sms(account_sid, auth_token, sender_id, recipient, message):

    recipient = f'+{recipient}'

    client = Client(account_sid, auth_token)

    try:
        message = client.messages.create(
                                    body=message,
                                    from_=sender_id,
                                    to=recipient
                                )

        print(message.sid)
        return 0
        
    except Exception as e:
        print(e)
        return 1
