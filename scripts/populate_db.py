import requests
import random

API_URL = "http://localhost:8000/intents"  # Make sure this matches your FastAPI URL
HEADERS = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "ovos-metrics"}

UTTERANCES = ["hello", "turn on the light", "what's the weather?", "play some music", "stop", "set a timer"]
INTENTS = ["greeting", "light_on", "weather_query", "music_play", "stop", "set_timer"]
LANGUAGES = ["en", "pt", "es", "fr", "de"]

def send_dummy_data():
    for _ in range(50):  # Generate 50 records
        data = {
            "utterance": random.choice(UTTERANCES),
            "intent": random.choice(INTENTS),
            "lang": random.choice(LANGUAGES),
            "match_data": None  # or use an empty string if required
        }
        response = requests.post(API_URL, data=data, headers=HEADERS)
        print(f"Sent: {data} - Response: {response.status_code}")

if __name__ == "__main__":
    send_dummy_data()
