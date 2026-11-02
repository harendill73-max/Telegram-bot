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
def home(): return "Nunzio V19 SENZA CHIOCCIOLA OK"

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
        if code == 0: desc = "Sereno sole"
        elif code == 1: desc = "Quasi sereno"
        elif code == 2: desc = "Parz nuvoloso"
        elif code == 3: desc = "Coperto"
        elif code == 95: desc = "Temporale"
        else: desc = "Meteo " + str(code)
        return name + " oggi: " + desc + "\nOra: " + str(temp) + "C (min " + str(tmin) + " / max " + str(tmax) + ")\nVento: " + str(wind) + " km/h"
    except Exception as e:
        print("Weather error")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    print("MSG: " + text)
    low = text.lower()
    
    # togli chiocciola se c e ma non serve
    low_clean = low.replace("@nunzio", "").replace("@Nunzio", "").strip()
    if low_clean.startswith("nunzio"): low_clean = low_clean[6:].strip()
    
    # METEO senza chiocciola!
    if "tempo" in low_clean or "meteo" in low_clean or "bari" in low_clean:
        city = "Bari"
        if "roma" in low_clean: city = "Roma"
        if "milano" in low_clean: city = "Milano"
        if "napoli" in low_clean: city = "Napoli"
        if "bari" in low_clean: city = "Bari"
        meteo = get_weather(city)
        if meteo:
            await update.message.reply_text(meteo)
        else:
            await update.message.reply_text("Non trovo meteo per " + city)
        return

    # chat normale senza chiocciola!
    if client:
        try:
            resp=client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role":"system","content":"Sei Nunzio, amico simpatico, italiano breve, naturale. Non dire mai E quindi? Non dire Ti ascolto! a caso. Rispondi utile."},
                    {"role":"user","content": text}
                ],
                max_tokens=200, temperature=0.7
            )
            content=resp.choices[0].message.content
            if content and content.strip():
                await update.message.reply_text(content.strip()[:1000])
                return
        except Exception as e:
            print("Groq error")

    await update.message.reply_text("Ciao! Sono qui!")

def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN mancante!")
        return
    while True:
        try:
            print("Avvio bot...")
            b=ApplicationBuilder().token(BOT_TOKEN).build()
            b.add_handler(CommandHandler("start",start))
            b.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat))
            print("Bot ONLINE senza chiocciola!")
            b.run_polling(drop_pending_updates=True)
        except Exception as e:
            print("Crash bot, riavvio")
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
