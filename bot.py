import os, threading, random, time, re, json, logging
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
def home(): return "Nunzio V20 FULL - Giochi + Meteo - LIVE"

games = {}

def anti_sleep():
    url = os.getenv("RENDER_EXTERNAL_URL") or "https://telegram-bot-hcj7.onrender.com"
    while True:
        time.sleep(600)
        try: urllib.request.urlopen(url, timeout=10).read()
        except: pass

PAC_MAZE = ["111111111","100000001","101010101","100000001","100000001","100000001","101010101","100000001","111111111"]
TETROS = {
    "I": ([(0,0),(1,0),(2,0),(3,0)], "BLU"),
    "O": ([(0,0),(1,0),(0,1),(1,1)], "GIALLO"),
    "T": ([(0,0),(1,0),(2,0),(1,1)], "VIOLA"),
    "L": ([(0,0),(0,1),(0,2),(1,2)], "ARANC"),
    "S": ([(1,0),(2,0),(0,1),(1,1)], "VERDE")
}

def render_snake(snake, food, size=8):
    b=""
    for y in range(size):
        for x in range(size):
            if (x,y)==food: b+="A "
            elif (x,y)==snake[0]: b+="O "
            elif (x,y) in snake: b+="# "
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
    tmp = [row[:] for row in g["board"]]
    for dx,dy in g["piece"]:
        x=g["x"]+dx; y=g["y"]+dy
        if 0<=y<10 and 0<=x<10: tmp[y][x]=g["color"]
    out=""
    for y in range(10):
        for x in range(10): 
            out+= tmp[y][x][0] if tmp[y][x]!=0 else ". "
        out+="\n"
    return out

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
        elif code == 45: desc = "Nebbia"
        elif code == 61: desc = "Pioggia leggera"
        elif code == 63: desc = "Pioggia"
        elif code == 65: desc = "Pioggia forte"
        elif code == 95: desc = "Temporale"
        else: desc = "Meteo codice " + str(code)
        return name + " oggi: " + desc + "\nOra: " + str(temp) + "C (min " + str(tmin) + " / max " + str(tmax) + ")\nVento: " + str(wind) + " km/h"
    except Exception as e:
        print("Weather error")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_USERNAME
    try: BOT_USERNAME = (await context.bot.get_me()).username
    except: pass
    await update.message.reply_text("Ciao! Sono Nunzio!\n/snake /pacman /tetris per giocare\nScrivimi che tempo fa a Bari?")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    snake=[(3,3),(2,3),(1,3)]; food=(random.randint(0,7),random.randint(0,7))
    games[chat_id]={"type":"snake","snake":snake,"food":food,"dir":(1,0)}
    kb=[[InlineKeyboardButton("SU",callback_data="snake_up")],[InlineKeyboardButton("SX",callback_data="snake_left"),InlineKeyboardButton("GIU",callback_data="snake_down"),InlineKeyboardButton("DX",callback_data="snake_right")]]
    await update.message.reply_text("SNAKE Score:0\n" + render_snake(snake,food),reply_markup=InlineKeyboardMarkup(kb))

async def pacman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    dots=[(x,y) for y in range(9) for x in range(9) if PAC_MAZE[y][x]=="0"]
    pac=(4,4); ghost=(1,1); dots=[d for d in dots if d!=pac and d!=ghost]
    games[chat_id]={"type":"pacman","pac":pac,"ghost":ghost,"dots":dots,"score":0}
    kb=[[InlineKeyboardButton("SU",callback_data="pac_up")],[InlineKeyboardButton("SX",callback_data="pac_left"),InlineKeyboardButton("GIU",callback_data="pac_down"),InlineKeyboardButton("DX",callback_data="pac_right")]]
    await update.message.reply_text("PACMAN Score:0\n" + render_pacman(games[chat_id]),reply_markup=InlineKeyboardMarkup(kb))

async def tetris_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    board=[[0]*10 for _ in range(10)]
    shape_color = random.choice(list(TETROS.values()))
    games[chat_id]={"type":"tetris","board":board,"piece":shape_color[0][:],"color":shape_color[1],"x":3,"y":0,"score":0}
    kb=[[InlineKeyboardButton("Ruota",callback_data="tet_rot"),InlineKeyboardButton("Giu",callback_data="tet_down")],[InlineKeyboardButton("SX",callback_data="tet_left"),InlineKeyboardButton("DX",callback_data="tet_right")]]
    await update.message.reply_text("TETRIS Score:0\n" + render_tetris(games[chat_id]),reply_markup=InlineKeyboardMarkup(kb))

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
            await q.edit_message_text("Game Over! /snake per rigiocare"); del games[chat_id]; return
        g["snake"]=[nh]+g["snake"]
        if nh==g["food"]: g["food"]=(random.randint(0,7),random.randint(0,7))
        else: g["snake"].pop()
        kb=[[InlineKeyboardButton("SU",callback_data="snake_up")],[InlineKeyboardButton("SX",callback_data="snake_left"),InlineKeyboardButton("GIU",callback_data="snake_down"),InlineKeyboardButton("DX",callback_data="snake_right")]]
        await q.edit_message_text("Score:" + str(len(g['snake'])-3) + "\n" + render_snake(g['snake'],g['food']),reply_markup=InlineKeyboardMarkup(kb))
    elif g["type"]=="pacman" and data.startswith("pac_"):
        dirs={"pac_up":(0,-1),"pac_down":(0,1),"pac_left":(-1,0),"pac_right":(1,0)}
        nd=dirs[data]; nx=g["pac"][0]+nd[0]; ny=g["pac"][1]+nd[1]
        if 0<=nx<9 and 0<=ny<9 and PAC_MAZE[ny][nx]=="0":
            g["pac"]=(nx,ny)
            if g["pac"] in g["dots"]: g["dots"].remove(g["pac"]); g["score"]+=10
        gx,gy=g["ghost"]; px,py=g["pac"]
        best=None; bestdist=999
        for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nnx=gx+dx; nny=gy+dy
            if 0<=nnx<9 and 0<=nny<9 and PAC_MAZE[nny][nnx]=="0":
                dist=abs(nnx-px)+abs(nny-py)
                if dist<bestdist: bestdist=dist; best=(nnx,nny)
        if best: g["ghost"]=best
        if g["pac"]==g["ghost"]:
            await q.edit_message_text("Beccato! Score:" + str(g['score']) + " /pacman"); del games[chat_id]; return
        if not g["dots"]:
            await q.edit_message_text("VITTORIA! Score:" + str(g['score'])); del games[chat_id]; return
        kb=[[InlineKeyboardButton("SU",callback_data="pac_up")],[InlineKeyboardButton("SX",callback_data="pac_left"),InlineKeyboardButton("GIU",callback_data="pac_down"),InlineKeyboardButton("DX",callback_data="pac_right")]]
        await q.edit_message_text("Score:" + str(g['score']) + " Mancano " + str(len(g['dots'])) + "\n" + render_pacman(g),reply_markup=InlineKeyboardMarkup(kb))
    elif g["type"]=="tetris" and data.startswith("tet_"):
        if data=="tet_left" and can_move_tetris(g,g["x"]-1,g["y"],g["piece"]): g["x"]-=1
        if data=="tet_right" and can_move_tetris(g,g["x"]+1,g
