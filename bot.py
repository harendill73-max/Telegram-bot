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
def home(): return "Nunzio V15 CLEAN"

games = {}

def anti_sleep():
    url = os.getenv("RENDER_EXTERNAL_URL") or "https://telegram-bot-hcj7.onrender.com"
    while True:
        time.sleep(600)
        try:
            urllib.request.urlopen(url, timeout=10).read()
        except: pass

PAC_MAZE = ["111111111","100000001","101010101","100000001","100000001","100000001","101010101","100000001","111111111"]
TETROS = {"I": ([(0,0),(1,0),(2,0),(3,0)], "BLU"), "O": ([(0,0),(1,0),(0,1),(1,1)], "GIALLO"), "T": ([(0,0),(1,0),(2,0),(1,1)], "VIOLA"), "L": ([(0,0),(0,1),(0,2),(1,2)], "ARANC"), "S": ([(1,0),(2,0),(0,1),(1,1)], "VERDE")}

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
            if PAC_MAZE[y][x]=="1": s+="#"
            elif (x,y)==g["pac"]: s+="C"
            elif (x,y)==g["ghost"]: s+="G"
            elif (x,y) in g["dots"]: s+="."
            else: s+=" "
        s+="\n"
    return s

def render_tetris(g):
    tmp = [row[:] for row in g["board"]]
    for dx,dy in g["piece"]:
        x=g["x"]+dx; y=g["y"]+dy
        if 0<=y<10 and 0<=x<10: tmp[y][x]=g["color"]
