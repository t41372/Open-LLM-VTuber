import requests

def send_message_to_broadcast(message):
    url = "http://127.0.0.1:8000/broadcast"
    data = {"message": message}
    response = requests.post(url, json=data)
    print(f"Response Status Code: {response.status_code}")
    if response.ok:
        print("Message successfully sent to the broadcast route.")
    else:
        print("Failed to send message to the broadcast route.")

# 使用範例
while True: 
    send_message_to_broadcast(input("(大人, 请广播🙏) >> "))