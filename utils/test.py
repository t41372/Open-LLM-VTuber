import requests
import json as JSON

def send_message_to_broadcast(message):
    url = "http://127.0.0.1:8000/broadcast"

    payload = {"type" : "full-text", "text": message}


    data = {"message": JSON.dumps(payload)}
    response = requests.post(url, json=data)
    print(f"Response Status Code: {response.status_code}")
    if response.ok:
        print("Message successfully sent to the broadcast route.")
    else:
        print("Failed to send message to the broadcast route.")

# 使用例
while True: 
    send_message_to_broadcast(input("(大人, 请广播🙏) >> "))