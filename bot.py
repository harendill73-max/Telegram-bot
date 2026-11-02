import os, threading, random, time, re, math, json
import urllib.request, urllib.parse
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
BOT_USERNAME = None

app = Flask(__name__)
@app.route('/')
def home(): return "Nunzio V14 METEO"

games = {}

def anti_sleep():
    url = os.getenv("RENDER_EXTERNAL_URL") or "https://telegram-bot-hcj7.onrender.com"
    while True:
        time.sleep(600)
        try: urllib.request.urlopen(url, timeout=10).read()
        except: pass

PAC_MAZE = ["111111111","100000001","101010101","100000001","100000001","100000001","101010101","100000001","111111111"]
TETROS = {"I": ([(0,0),(1,0),(2,0),(3,0)], "🟦"), "O": ([(0,0),(1,0),(0,1),(1,1)], "🟨"), "T": ([(0,0),(1,0),(2,0),(1,1)], "🟪"), "L": ([(0,0),(0,1),(0,2),(1,2)], "🟧"), "S": ([(1,0),(2,0),(0,1),(1,1)], "🟩")}

def render_snake(snake, food, size=8):
    b=""
    for y in range(size):
        for x in range(size):
            if (x,y)==food: b+="🍎"
            elif (x,y)==snake[0]: b+="😀"
            elif (x,y) in snake: b+="🟩"
            else: b+="⬛"
        b+="\n"
    return b
def render_pacman(g):
    s=""
    for y in range(9):
        for x in range(9):
            if PAC_MAZE[y][x]=="1": s+="🟦"
            elif (x,y)==g["pac"]: s+="😋"
            elif (x,y)==g["ghost"]: s+="👻"
            elif (x,y) in g["dots"]: s+="⚪"
            else: s+="⬜"
        s+="\n"
    return s
def render_tetris(g):
    tmp = [row[:] for row in g["board"]]
    for dx,dy in g["piece"]:
        x=g["x"]+dx; y=g["y"]+dy
        if 0<=y<10 and 0<=x<10: tmp[y][x]=g["color"]
    out=""
    for y in range(10):
        for x in range(10): out+= tmp[y][x] if tmp[y][x]!=0 else "⬛"
        out+="\n"
    return out

def get_weather(city):
    try:
        # 1. Trova coordinate città
        q = urllib.parse.quote(city)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=1&language=it&format=json"
        with urllib.request.urlopen(geo_url, timeout=5) as r:
            geo = json.loads(r.read().decode())
        if not geo.get("results"): return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        name = geo["results"][0]["name"]
        # 2. Prendi meteo
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        with urllib.request.urlopen(weather_url, timeout=5) as r:
            w = json.loads(r.read().decode())
        temp = w["current"]["temperature_2m"]
        wind = w["current"]["wind_speed_10m"]
        code = w["current"]["weather_code"]
        tmax = w["daily"]["temperature_2m_max"][0]
        tmin = w["daily"]["temperature_2m_min"][0]
        # Decodifica tempo
        codes = {0:"Sereno ☀️",1:"Quasi sereno 🌤️",2:"Parz. nuvoloso ⛅",3:"Coperto ☁️",45:"Nebbia 🌫️",51:"Pioviggine 🌦️",61:"Pioggia leggera 🌧️",63:"Pioggia 🌧️",65:"Pioggia forte 🌧️",71:"Neve leggera ❄️",80:"Rovesci 🌦️",95:"Temporale ⛈️"}
        desc = codes.get(code, f"Codice {code}")
        return f"📍 {name} oggi:\n{desc}\n🌡️ Ora: {temp}°C (min {tmin}° / max {tmax}°)\n💨 Vento: {wind} km/h"
    except Exception as e:
        print(f"Weather error: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_USERNAME
    try: BOT_USERNAME = (await context.bot.get_me()).username
    except: pass
    await update.message.reply_text("Ciao! Sono Nunzio 😊\n/snake /pacman /tetris per giocare\nTaggami per meteo, conti, tabelline!")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    snake=[(3,3),(2,3),(1,3)]; food=(random.randint(0,7),random.randint(0,7))
    games[chat_id]={"type":"snake","snake":snake,"food":food,"dir":(1,0)}
    kb=[[InlineKeyboardButton("⬆️",callback_data="
