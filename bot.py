import os, threading, time, json
import urllib.request, urllib.parse
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

app = Flask(__name__)
@app.route('/')
def home(): return "Nunzio V16 STABILE - OK"

def get_weather(city):
    try:
        q = urllib.parse.quote(city)
        geo_url = "https://geocoding-api.open-meteo.com/v1/search?name=" + q + "&count=1&language=it&format=json"
        with urllib.request.urlopen(geo_url, timeout=5) as r:
            geo = json.loads(r.read().decode())
        if not geo.get("results"): return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        name = geo["results"][0]["name"]
        weather_url = "https://api.open-meteo.com/v1/forecast?latitude=" + str(lat) + "&longitude=" + str(lon) + "&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        with urllib.request.urlopen(weather_url, timeout=5) as r:
            w = json.loads(r.read().decode())
        temp = w["current"]["temperature_2m"]
        wind = w["current"]["wind_speed_10m"]
        code = w["current"]["weather_code"]
        tmax = w["daily"]["temperature_2m_max"][0]
        tmin = w["daily"]["temperature_2m_min"][0]
        if code == 0: desc = "Sereno"
        elif code == 1: desc = "Quasi sereno"
        elif code == 2: desc = "Parz nuvoloso"
        elif code == 3: desc = "Coperto"
        elif code == 95: desc = "Temporale"
        else: desc = "Meteo"
        return name + " oggi: " + desc + "\nOra: " + str(temp) + "C (min " + str(tmin) + " / max " + str(tmax) + ")\nVento: " + str(wind) + " km/h"
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    low = text.lower()
    print("MSG: " + text)

    # METEO - con o senza @
    if "tempo" in low or "meteo" in low:
        city = "Bari"
        if "bari" in low: city = "Bari"
        if "roma" in low: city = "Roma"
        meteo = get_weather(city)
        if meteo:
            await update.message.reply_text(meteo)
        else:
            await update.message.reply_text("Non trovo meteo per " + city)
        return

    # In gruppo risponde solo se taggato o se gli rispondi
    chat_type = update.effective_chat.type
    if chat_type in ["group", "supergroup"]:
       
