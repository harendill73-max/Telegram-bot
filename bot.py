import os, threading, random, time, re, math, json, asyncio
import urllib.request, urllib.parse
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

app = Flask(__name__)
@app.route('/')
def home(): return "Nunzio V23 POLLING FIX LIVE"

games = {}

def get_weather(city):
    try:
        q = urllib.parse.quote(city)
        url1 = "https://geocoding-api.open-meteo.com/v1/search?name=" + q + "&count=1&language=it&format=json"
        with urllib.request.urlopen(url1, timeout=5) as r:
            geo = json.loads(r.read().decode())
        if not geo.get("results"): return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        name = geo["results"][0]["name"]
        url2 = "https://api.open-meteo.com/v1/forecast?latitude=" + str(lat) + "&longitude=" + str(lon) + "&current=temperature_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        with urllib.request.urlopen(url2, timeout=5) as r:
            w = json.loads(r.read().decode())
        temp = w["current"]["temperature_2m"]
        wind = w["current"]["wind_speed_10m"]
        code = w["current"]["weather_code"]
        tmax = w["daily"]["temperature_2m_max"][0]
        tmin = w["daily"]["temperature_2m_min"][0]
        desc = "Sereno"
        if code == 0: desc = "Sereno sole"
        if code == 1: desc = "Quasi sereno"
        if code == 2: desc = "Parz nuvoloso"
        if code == 3: desc = "Coperto"
        if code == 95: desc = "Temporale"
        return name + " oggi: " + desc + "\nOra: " + str(temp) + "C (min " + str(tmin) + " max " + str(tmax) + ")\nVento: " + str(wind) + " km/h"
    except: return None

PAC_MAZE = ["111111111","100000001","101010101","100000001","100000001","100000001","101010101","100000001","111111111"]

def render_snake(snake, food):
    b=""
    for y in range(8):
        for x in range(8):
            p=(x,y)
            if p==food: b+="A "
            elif p==snake[0]: b+="O "
            elif p in snake: b+="# "
            else: b+=". "
        b+="\n"
    return b

def render_pacman(g):
    s=""
    for y in range(9):
        for x in range(9):
            if PAC_MAZE[y][x]=="1": s+="# "
            elif (x,y)==g["pac"]: s+="C "
            elif (x,y)==g["ghost"]: s+="G "
            elif (x,y) in g["dots"]: s+=". "
            else: s+="  "
        s+="\n"
    return s

def render_tetris(g):
    tmp=[row[:] for row in g["board"]]
    for dx,dy in g["piece"]:
        x=g["x"]+dx; y=g["y"]+dy
        if 0<=y<10 and 0<=x<10: tmp[y][x]="X"
    out=""
    for y in range(10):
        for x in range(10): out+= ". " if tmp[y][x]==0 else "X "
        out+="\n"
    return out

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio V23!\n/snake /pacman /tetris\nDimmi che tempo fa a Bari o √35")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    snake=[(3,3),(2,3),(1,3)]; food=(random.randint(0,7),random.randint(0,7))
    games[chat_id]={"type":"snake","snake":snake,"food":food,"dir":(1,0)}
    kb=[[InlineKeyboardButton("SU",callback_data="snake_up")],[InlineKeyboardButton("SX",callback_data="snake_left"),InlineKeyboardButton("GIU",callback_data="snake_down"),InlineKeyboardButton("DX",callback_data="snake_right")]]
    await update.message.reply_text("SNAKE\n"+render_snake(snake,food),reply_markup=InlineKeyboardMarkup(kb))

async def pacman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    dots=[(x,y) for y in range(9) for x in range(9) if PAC_MAZE[y][x]=="0"]
    pac=(4,4); ghost=(1,1)
    dots=[d for d in dots if d!=pac and d!=ghost]
    games[chat_id]={"type":"pacman","pac":pac,"ghost":ghost,"dots":dots,"score":0}
    kb=[[InlineKeyboardButton("SU",callback_data="pac_up")],[InlineKeyboardButton("SX",callback_data="pac_left"),InlineKeyboardButton("GIU",callback_data="pac_down"),InlineKeyboardButton("DX",callback_data="pac_right")]]
    await update.message.reply_text("PACMAN\n"+render_pacman(games[chat_id]),reply_markup=InlineKeyboardMarkup(kb))

async def tetris_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    board=[[0]*10 for _ in range(10)]
    piece=[(0,0),(1,0),(2,0),(3,0)]
    games[chat_id]={"type":"tetris","board":board,"piece":piece,"x":3,"y":0,"score":0}
    kb=[[InlineKeyboardButton("Ruota",callback_data="tet_rot"),InlineKeyboardButton("Giu",callback_data="tet_down")],[InlineKeyboardButton("SX",callback_data="tet_left"),InlineKeyboardButton("DX",callback_data="tet_right")]]
    await update.message.reply_text("TETRIS\n"+render_tetris(games[chat_id]),reply_markup=InlineKeyboardMarkup(kb))

def can_move_tetris(g, nx, ny, piece):
    for dx,dy in piece:
        x=nx+dx; y=ny+dy
        if not (0<=x<10 and 0<=y<10): return False
        if g["board"][y][x]!=0: return False
    return True

async def move_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    chat_id=q.message.chat_id
    if chat_id not in games: return
    g=games[chat_id]; data=q.data
    if g["type"]=="snake" and data.startswith("snake_"):
        dirs={"snake_up":(0,-1),"snake_down":(0,1),"snake_left":(-1,0),"snake_right":(1,0)}
        nd=dirs[data]
        if (nd[0]*-1, nd[1]*-1)!=g["dir"]: g["dir"]=nd
        nh=(g["snake"][0][0]+g["dir"][0], g["snake"][0][1]+g["dir"][1])
        if not (0<=nh[0]<8 and 0<=nh[1]<8) or nh in g["snake"]:
            await q.edit_message_text("Game Over! /snake"); del games[chat_id]; return
        g["snake"]=[nh]+g["snake"]
        if nh==g["food"]: g["food"]=(random.randint(0,7),random.randint(0,7))
        else: g["snake"].pop()
        kb=[[InlineKeyboardButton("SU",callback_data="snake_up")],[InlineKeyboardButton("SX",callback_data="snake_left"),InlineKeyboardButton("GIU",callback_data="snake_down"),InlineKeyboardButton("DX",callback_data="snake_right")]]
        await q.edit_message_text("Score:"+str(len(g['snake'])-3)+"\n"+render_snake(g['snake'],g['food']),reply_markup=InlineKeyboardMarkup(kb))

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=update.message.text.strip()
    low=text.lower()
    print("MSG: "+text)

    if "tempo" in low or "meteo" in low:
        city="Bari"
        if "roma" in low: city="Roma"
        if "milano" in low: city="Milano"
        if "bari" in low: city="Bari"
        meteo=get_weather(city)
        if meteo:
            await update.message.reply_text(meteo)
            return

    try:
        has_digit=any(c.isdigit() for c in text)
        if has_digit and ("√" in text or "sqrt" in low):
            m=re.search(r'√\s*(\d+)', text)
            if not m: m=re.search(r'sqrt\s*\(?\s*(\d+)', low)
            if m:
                num=float(m.group(1))
                res=math.sqrt(num)
                if res.is_integer(): res=int(res)
                await update.message.reply_text("√"+m.group(1)+" = "+str(res)+" ✅")
                return
    except: pass

    if client:
        try:
            resp=client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role":"system","content":"Sei Nunzio, bagnino pugliese simpatico, italiano breve, naturale."},{"role":"user","content":text}],
                max_tokens=250, temperature=0.7
            )
            content=resp.choices[0].message.content
            if content and content.strip():
                await update.message.reply_text(content.strip()[:1000])
                return
        except Exception as e:
            print("Groq error: "+str(e))

    await update.message.reply_text("Ciao! Sono qui! Dimmi pure 😊")

async def run_bot_async():
    print("Avvio bot polling V23...")
    b=ApplicationBuilder().token(BOT_TOKEN).build()
    b.add_handler(CommandHandler("start",start))
    b.add_handler(CommandHandler("snake",snake_cmd))
    b.add_handler(CommandHandler("pacman",pacman_cmd))
    b.add_handler(CommandHandler("tetris",tetris_cmd))
    b.add_handler(CallbackQueryHandler(move_callback))
    b.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat))
    await b.initialize()
    await b.start()
    await b.updater.start_polling(drop_pending_updates=True)
    print("Bot ONLINE V23!")
    await b.updater.idle()

def run_bot():
    while True:
        try:
            asyncio.run(run_bot_async())
        except Exception as e:
            print("Crash bot: "+str(e))
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port=int(os.environ.get("PORT", 10000))
    print("Flask parte porta "+str(port))
    app.run(host="0.0.0.0", port=port)
