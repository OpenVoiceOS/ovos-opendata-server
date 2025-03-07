import requests
import random

API_URL = "http://localhost:8000/collect"
HEADERS = {"Content-Type": "application/json", "User-Agent": "ovos-core-metrics"}

UTTERANCES = ["hello", "turn on the light", "what's the weather?", "play some music", "stop", "set a timer"]
INTENTS = ["greeting", "light_on", "weather_query", "music_play", "stop", "set_timer"]
LANGUAGES = ["en", "pt", "es", "fr", "de"]

def send_dummy_data():
    for _ in range(50):  # Generate 50 records
        data = {
            "utterance": random.choice(UTTERANCES),
            "intent": random.choice(INTENTS),
            "language": random.choice(LANGUAGES)
        }
        response = requests.post(API_URL, json=data, headers=HEADERS)
        print(f"Sent: {data} - Response: {response.status_code}")

if __name__ == "__main__":
    send_dummy_data()
