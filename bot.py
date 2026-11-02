import os, threading, random, time, re, math, json, logging
import urllib.request, urllib.parse
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from groq import Groq

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
BOT_USERNAME = None

app = Flask(__name__)
@app.route('/')
def home(): return "Nunzio V16 STABILE - OK"

games = {}

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
        codes = {0:"Sereno sole",1:"Quasi sereno",2:"Parz nuvoloso",3:"Coperto",45:"Nebbia",51:"Pioviggine",61:"Pioggia leggera",63:"Pioggia",65:"Pioggia forte",71:"Neve",80:"Rovesci",95:"Temporale"}
        desc = codes.get(code, f"Meteo {code}")
        return f"{name} oggi: {desc}\nOra: {temp}C (min {tmin} / max {tmax})\nVento: {wind} km/h"
    except Exception as e:
        print(f"Weather error {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_USERNAME
    try: BOT_USERNAME = (await context.bot.get_me()).username
    except: pass
    await update.message.reply_text("Ciao! Sono Nunzio! /snake /pacman /tetris - Taggami per meteo!")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    snake=[(3,3),(2,3),(1,3)]; food=(random.randint(0,7),random.randint(0,7))
    games[chat_id]={"type":"snake","snake":snake,"food":food,"dir":(1,0)}
    kb=[[InlineKeyboardButton("SU",callback_data="snake_up")],[InlineKeyboardButton("SX",callback_data="snake_left"),InlineKeyboardButton("GIU",callback_data="snake_down"),InlineKeyboardButton("DX",callback_data="snake_right")]]
    await update.message.reply_text(f"SNAKE\nScore 0",reply_markup=InlineKeyboardMarkup(kb))

async def pacman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    dots=[(x,y) for y in range(9) for x in range(9) if x%2==0]
    games[chat_id]={"type":"pacman","score":0}
    kb=[[InlineKeyboardButton("SU",callback_data="pac_up")],[InlineKeyboardButton("SX",callback_data="pac_left"),InlineKeyboardButton("GIU",callback_data="pac_down"),InlineKeyboardButton("DX",callback_data="pac_right")]]
    await update.message.reply_text(f"PACMAN Score:0 - Premi",reply_markup=InlineKeyboardMarkup(kb))

async def tetris_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    board=[[0]*10 for _ in range(10)]
    games[chat_id]={"type":"tetris","board":board,"score":0}
    kb=[[InlineKeyboardButton("Ruota",callback_data="tet_rot"),InlineKeyboardButton("Giu",callback_data="tet_down")],[InlineKeyboardButton("SX",callback_data="tet_left"),InlineKeyboardButton("DX",callback_data="tet_right")]]
    await update.message.reply_text(f"TETRIS Score:0",reply_markup=InlineKeyboardMarkup(kb))

async def move_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.edit_message_text("Gioco! Usa /snake /pacman /tetris per rigiocare")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_USERNAME
    if not BOT_USERNAME:
        try: BOT_USERNAME = (await context.bot.get_me()).username
        except: BOT_USERNAME = "Nunzio"
    text = update.message.text or ""
    chat_type = update.effective_chat.type
    is_group = chat_type in ["group", "supergroup"]
    if is_group:
        is_reply_to_bot = False
        if update.message.reply_to_message:
            try: is_reply_to_bot = update.message.reply_to_message.from_user.id == context.bot.id
            except: pass
        is_mentioned = (BOT_USERNAME and f"@{BOT_USERNAME}" in text) or text.lower().strip().startswith("nunzio")
        is_math = bool(re.search(r'\d+\s*[\+\-\*\/x]\s*\d+|sqrt|tabell', text.lower()))
        is_weather = bool(re.search(r'tempo|meteo', text.lower()))
        if not (is_reply_to_bot or is_mentioned or is_math or is_weather):
            return
        if BOT_USERNAME: text = text.replace(f"@{BOT_USERNAME}", "").strip()
        if text.lower().startswith("nunzio"): text = text[6:].strip()
        if not text: text = "ciao"

    if re.search(r'tempo|meteo', text.lower()):
        city = "Bari"
        mm = re.search(r'\b(a|di|per)\s+([a-zA-Z]{2,})', text.lower())
        if mm: city = mm.group(2)
        if "bari" in text.lower(): city = "Bari"
        meteo = get_weather(city)
        if meteo: await update.message.reply_text(meteo)
        else: await update.message.reply_text(f"Non trovo meteo per {city}")
        return

    try:
        t = text.replace('=', '').strip()
        if re.search(r'\d+\s*[\+\-\*\/x]\s*\d+', t) and len(t) < 30:
            expr=t.replace('x','*').replace('X','*')
            clean=re.sub(r'[^0-9\+\-\*\/\(\)\.\s]', '', expr)
            result=eval(clean, {"__builtins__": {}}, {})
            await update.message.reply_text(f"{text} = {result}")
            return
    except: pass

    if client:
        try:
            resp=client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role":"system","content":"Sei Nunzio, amico simpatico, italiano naturale, breve. Non dire che sei bot. Rispondi naturale."},
                    {"role":"user","content": text}
                ],
                max_tokens=250, temperature=0.7
            )
            content=resp.choices[0].message.content
            if content and content.strip():
                await update.message.reply_text(content.strip()[:1500])
                return
        except Exception as e:
            print(f"Groq error {e}")

    await update.message.reply_text("Ciao! Sono qui!")

def run_bot():
    if not BOT_TOKEN:
        print("ERRORE: BOT_TOKEN mancante!")
        return
    while True:
        try:
            print("Avvio bot Telegram...")
            b=ApplicationBuilder().token(BOT_TOKEN).build()
            b.add_handler(CommandHandler("start",start))
            b.add_handler(CommandHandler("snake",snake_cmd))
            b.add_handler(CommandHandler("pacman",pacman_cmd))
            b.add_handler(CommandHandler("tetris",tetris_cmd))
            b.add_handler(CallbackQueryHandler(move_callback))
            b.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat))
            b.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"Bot crashato: {e} - riavvio in 5 sec")
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"Flask parte su porta {port}")
    app.run(host="0.0.0.0", port=port)
