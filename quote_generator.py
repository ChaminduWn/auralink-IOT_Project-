# quote_generator.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# Make sure .env is loaded before creating the OpenAI client
load_dotenv()  # <-- important

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in environment variables. Check your .env file!")

client = OpenAI(api_key=api_key)

def generate_quote(temp, humidity):
    # Example: Use the OpenAI client to generate a quote based on temp/humidity
    prompt = f"Generate a short literature-style quote inspired by temperature {temp}°C and humidity {humidity}%."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=50
    )
    return response.choices[0].message.content.strip()
