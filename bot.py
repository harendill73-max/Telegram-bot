import os, threading, re, json, logging
import urllib.request, urllib.parse
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

app = Flask(__name__)
@app.route('/')
def home(): return "Nunzio V18 NO CHIOCCIOLA - LIVE"

def get_weather(city):
    try:
        q = urllib.parse.quote(city)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=1&language=it&format=json"
        with urllib.request.urlopen(geo_url, timeout=5) as r:
            geo = json.loads(r.read().decode())
        if not geo.get("results"): return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        name = geo["results"][0]["name"]
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        with urllib.request.urlopen(weather_url, timeout=5) as r:
            w = json.loads(r.read().decode())
        temp = w["current"]["temperature_2m"]
        wind = w["current"]["wind_speed_10m"]
        code = w["current"]["weather_code"]
        tmax = w["daily"]["temperature_2m_max"][0]
        tmin = w["daily"]["temperature_2m_min"][0]
        codes = {0:"Sereno ☀️",1:"Quasi sereno 🌤️",2:"Parz nuvoloso ⛅",3:"Coperto ☁️",45:"Nebbia 🌫️",51:"Pioviggine",61:"Pioggia leggera 🌧️",63:"Pioggia 🌧️",65:"Pioggia forte 🌧️",71:"Neve ❄️",80:"Rovesci 🌦️",95:"Temporale ⛈️"}
        desc = codes.get(code, f"Meteo {code}")
        return f"📍 {name} oggi: {desc}\n🌡️ Ora: {temp}°C (min {tmin}° / max {tmax}°)\n💨 Vento: {wind} km/h"
    except Exception as e:
        print(f"Weather error {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio! Dimmi pure!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    print(f"MSG: '{text}'")
    
    if not text: return
    
    # Pulisci eventuale @nunzio se c'è, ma non è obbligatorio
    text_clean = re.sub(r"@nunzio\w*", "", text, flags=re.IGNORECASE).strip()
    if text_clean.lower().startswith("nunzio"): text_clean = text_clean[6:].strip()
    if not text_clean: text_clean = text

    # 1. METEO - risponde SEMPRE anche senza chiocciola!
    if re.search(r'tempo|meteo', text_clean.lower()) or "bari" in text_clean.lower():
        city = "Bari"
        mm = re.search(r'\b(a|di|per)\s+(
