import os
import json
from dotenv import load_dotenv
from mqtt_handler import MQTTHandler
from openai import OpenAI
from email_handler import get_email_summary

# ---------------- Load environment variables ----------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC_SENSOR = os.getenv("MQTT_TOPIC_SENSOR")
MQTT_TOPIC_BACKEND = os.getenv("MQTT_TOPIC_BACKEND")

# ---------------- OpenAI Client ----------------
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---------------- Generate Quote ----------------
def generate_quote(temp, humidity, co2, light):
    """Generate inspirational quote based on sensor data"""
    if not openai_client:
        return "Stay positive and productive! 🌟"
    
    prompt = (
        f"Generate a very short (max 10 words) inspirational quote for someone in a room with: "
        f"Temp: {temp}°C, Humidity: {humidity}%, CO2: {co2}ppm, Light: {light}%."
    )
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=30
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ OpenAI API error: {e}")
        return "Stay focused and energized! ✨"

# ---------------- Email Summary ----------------
def summarize_emails():
    """Get email summary using email_handler"""
    try:
        summary = get_email_summary()
        return summary
    except Exception as e:
        print(f"⚠️ Email summary error: {e}")
        return "Email check unavailable"

# ---------------- MQTT Callback ----------------
def on_message(client, userdata, msg):
    """Handle incoming MQTT messages from ESP32"""
    data = msg.payload.decode()
    print(f"\n📩 Received from ESP32: {data}")
    
    try:
        # Try parsing as JSON first
        try:
            sensor_data = json.loads(data)
            temp = sensor_data.get("temperature")
            humidity = sensor_data.get("humidity")
            co2 = sensor_data.get("co2", 400)  # Default CO2 if not provided
            light = sensor_data.get("light", 50)  # Default light if not provided
            
        except json.JSONDecodeError:
            # If JSON fails, try CSV format
            values = data.split(",")
            if len(values) == 4:
                temp, humidity, co2, light = values
            elif len(values) == 2:
                # Only temperature and humidity provided
                temp, humidity = values
                co2 = 400  # Default CO2
                light = 50  # Default light
                print("⚠️ Only temp & humidity received, using defaults for CO2 & light")
            else:
                raise ValueError(f"Invalid data format: expected 2 or 4 values, got {len(values)}")
        
        # Convert to float
        temp = float(temp)
        humidity = float(humidity)
        co2 = float(co2)
        light = float(light)
        
        print(f"🌡 Temp: {temp}°C | 💧 Hum: {humidity}% | 🌬 CO2: {co2} ppm | 💡 Light: {light}%")

        # Generate quote and email summary
        quote = generate_quote(temp, humidity, co2, light)
        email_summary = summarize_emails()

        # Publish JSON back to MQTT
        message = {
            "temperature": temp,
            "humidity": humidity,
            "co2": co2,
            "light": light,
            "quote": quote,
            "email_summary": email_summary
        }
        
        mqtt_handler.publish(message)
        print(f"✅ Published to backend topic")
        print(f"   📧 Email: {email_summary}")
        print(f"   💬 Quote: {quote}")

    except Exception as e:
        print(f"⚠️ Error processing data: {e}")
        import traceback
        traceback.print_exc()

# ---------------- Initialize MQTT ----------------
mqtt_handler = MQTTHandler(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    topic_sensor=MQTT_TOPIC_SENSOR,
    topic_backend=MQTT_TOPIC_BACKEND,
    on_message_callback=on_message
)

# ---------------- Main ----------------
if __name__ == "__main__":
    print("🚀 AuraLink Backend Starting...")
    print(f"📡 Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"📥 Listening on: {MQTT_TOPIC_SENSOR}")
    print(f"📤 Publishing to: {MQTT_TOPIC_BACKEND}")
    
    mqtt_handler.connect()
    print("✅ Backend running and waiting for sensor data...\n")
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        mqtt_handler.disconnect()