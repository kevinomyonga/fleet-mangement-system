import vonage

def vonage_send_sms(api_key, api_secret, sender_id, recepient, message):

    client = vonage.Client(key=api_key, secret=api_secret)
    sms = vonage.Sms(client)

    responseData = sms.send_message(
        {
            "from": sender_id,
            "to": str(recepient),
            "text": message,
        }
    )

    if responseData["messages"][0]["status"] == "0":
        print("Message sent successfully.")
        return 0
        
    else:
        print(f"Message failed with error: {responseData['messages'][0]['error-text']}")
        return 1
