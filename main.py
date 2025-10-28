import os
import json
import requests
import datetime
from dotenv import load_dotenv
from mqtt_handler import MQTTHandler
from email_handler import get_email_summary

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash"  # Corrected model name (was 2.5, which doesn't exist)
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC_SENSOR = os.getenv("MQTT_TOPIC_SENSOR")
MQTT_TOPIC_BACKEND = os.getenv("MQTT_TOPIC_BACKEND")

def generate_quote(temp, humidity, co2, light):
    if not GEMINI_API_KEY:
        return "Stay positive! 🌟"

    prompt = (
        f"Generate a short (max 10 words) poetic quote inspired by: "
        f"Temp {temp}°C, Humidity {humidity}%, CO₂ {co2}ppm, Light {light}%."
    )

    try:
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 50}
        }

        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text or "Breathe easy, stay inspired! ✨"

    except Exception as e:
        print(f"Gemini error: {e}")
        return "Focus and thrive! 💡"

def summarize_emails():
    try:
        return get_email_summary()
    except Exception as e:
        print(f"Email error: {e}")
        return "Email check failed"

def on_message(client, userdata, msg):
    data = msg.payload.decode()
    print(f"\nReceived: {data}")

    try:
        if data.startswith('{'):
            # Handle occasional JSON input (e.g., from another source)
            doc = json.loads(data)
            temp = float(doc.get("temperature", 0))
            humidity = float(doc.get("humidity", 0))
            co2 = float(doc.get("co2", 400))
            light = float(doc.get("light", 50))
        else:
            # Standard CSV
            values = [float(x) for x in data.split(",")]
            temp = values[0]
            humidity = values[1]
            co2 = values[2] if len(values) > 2 else 400
            light = values[3] if len(values) > 3 else 50

        print(f"Temp: {temp}°C | Hum: {humidity}% | CO₂: {co2}ppm | Light: {light}%")

        # Log
        with open("sensor_log.txt", "a") as f:
            f.write(f"{datetime.datetime.now()} - T:{temp}, H:{humidity}, C:{co2}, L:{light}\n")

        quote = generate_quote(temp, humidity, co2, light)
        email_summary = summarize_emails()

        urgency = "high" if any(word in email_summary.lower() for word in ["urgent", "asap", "important"]) else "low"

        message = {
            "temperature": temp,
            "humidity": humidity,
            "co2": co2,
            "light": light,
            "quote": quote,
            "email_summary": email_summary,
            "urgency": urgency
        }

        mqtt_handler.publish(message)
        print(f"Quote: {quote}")
        print(f"Email: {email_summary}")
        print(f"Urgency: {urgency}")

    except Exception as e:
        print(f"Error: {e}")

mqtt_handler = MQTTHandler(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    topic_sensor=MQTT_TOPIC_SENSOR,
    topic_backend=MQTT_TOPIC_BACKEND,
    on_message_callback=on_message,
)

if __name__ == "__main__":
    print("AuraLink Backend Starting...")
    mqtt_handler.connect()
    print("Backend running...")
    try:
        while True: pass
    except KeyboardInterrupt:
        mqtt_handler.disconnect()