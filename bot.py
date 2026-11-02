import os, threading, random, time, json
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
def home():
    return "Nunzio V20.1 FULL OK"

games = {}

PAC_MAZE = [
 "111111111",
 "100000001",
 "101010101",
 "100000001",
 "100000001",
 "100000001",
 "101010101",
 "100000001",
 "111111111"
]

def render_snake(snake, food):
    b = ""
    size = 8
    for y in range(size):
        for x in range(size):
            p = (x,y)
            if p == food:
                b += "A "
            elif p == snake[0]:
                b += "O "
            elif p in snake:
                b += "# "
            else:
                b += ". "
        b += "\n"
    return b

def render_pacman(g):
    s = ""
    for y in range(9):
        for x in range(9):
            if PAC_MAZE[y][x] == "1":
                s += "# "
            elif (x,y) == g["pac"]:
                s += "C "
            elif (x,y) == g["ghost"]:
                s += "G "
            elif (x,y) in g["dots"]:
                s += ". "
            else:
                s += "  "
        s += "\n"
    return s

def render_tetris(g):
    tmp = []
    for row in g["board"]:
        tmp.append(row[:])
    for dx,dy in g["piece"]:
        x = g["x"] + dx
        y = g["y"] + dy
        if 0 <= y < 10:
            if 0 <= x < 10:
                tmp[y][x] = g["color"]
    out = ""
    for y in range(10):
        for x in range(10):
            if tmp[y][x] == 0:
                out += ". "
            else:
                out += "X "
        out += "\n"
    return out

def get_weather(city):
    try:
        q = urllib.parse.quote(city)
        url1 = "https://geocoding-api.open-meteo.com/v1/search?name="
        url1 += q + "&count=1&language=it&format=json"
        with urllib.request.urlopen(url1, timeout=5) as r:
            geo = json.loads(r.read().decode())
        if not geo.get("results"):
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        name = geo["results"][0]["name"]
        url2 = "https://api.open-meteo.com/v1/forecast?latitude="
        url2 += str(lat) + "&longitude=" + str(lon)
        url2 += "&current=temperature_2m,weather_code,wind_speed_10m"
        url2 += "&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        with urllib.request.urlopen(url2, timeout=5) as r:
            w = json.loads(r.read().decode())
        temp = w["current"]["temperature_2m"]
        wind = w["current"]["wind_speed_10m"]
        code = w["current"]["weather_code"]
        tmax = w["daily"]["temperature_2m_max"][0]
        tmin = w["daily"]["temperature_2m_min"][0]
        desc = "Meteo"
        if code == 0:
            desc = "Sereno"
        if code == 1:
            desc = "Quasi sereno"
        if code == 2:
            desc = "Parz nuvoloso"
        if code == 3:
            desc = "Coperto"
        if code == 95:
            desc = "Temporale"
        msg = name + " oggi: " + desc + "\n"
        msg += "Ora: " + str(temp) + "C "
        msg += "(min " + str(tmin) + " / max " + str(tmax) + ")\n"
        msg += "Vento: " + str(wind) + " km/h"
        return msg
    except:
        return None

def can_move_tetris(g, nx, ny, piece):
    for dx,dy in piece:
        x = nx + dx
        y = ny + dy
        if x < 0 or x >= 10:
            return False
        if y < 0 or y >= 10:
            return False
        if g["board"][y][x] != 0:
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio!\n/snake /pacman /tetris")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    snake = [(3,3),(2,3),(1,3)]
    fx = random.randint(0,7)
    fy = random.randint(0,7)
    food = (fx,fy)
    games[chat_id] = {}
    games[chat_id]["type"] = "snake"
    games[chat_id]["snake"] = snake
    games[chat_id]["food"] = food
    games[chat_id]["dir"] = (1,0)
    kb = []
    kb.append([InlineKeyboardButton("SU", callback_data="snake_up")])
    kb.append([InlineKeyboardButton("SX", callback_data="snake_left"), InlineKeyboardButton("GIU", callback_data="snake_down"), InlineKeyboardButton("DX", callback_data="snake_right")])
    txt = "SNAKE\n" + render_snake(snake, food)
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def pacman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    dots = []
    for y in range(9):
        for x in range(9):
            if PAC_MAZE[y][x] == "0":
                dots.append((x,y))
    pac = (4,4)
    ghost = (1,1)
    if pac in dots:
        dots.remove(pac)
    if ghost in dots:
        dots.remove(ghost)
    games[chat_id] = {}
    games[chat_id]["type"] = "pacman"
    games[chat_id]["pac"] = pac
    games[chat_id]["ghost"] = ghost
    games[chat_id]["dots"] = dots
    games[chat_id]["score"] = 0
    kb = []
    kb.append([InlineKeyboardButton("SU", callback_data="pac_up")])
    kb.append([InlineKeyboardButton("SX", callback_data="pac_left"), InlineKeyboardButton("GIU", callback_data="pac_down"), InlineKeyboardButton("DX", callback_data="pac_right")])
    txt = "PACMAN\n" + render_pacman(games[chat_id])
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def tetris_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    board = []
    for _ in range(10):
        board.append([0]*10)
    piece = [(0,0),(1,0),(2,0),(3,0)]
    games[chat_id] = {}
    games[chat_id]["type"] = "tetris"
    games[chat_id]["board"] = board
    games[chat_id]["piece"] = piece
    games[chat_id]["color"] = "BLU"
    games[chat_id]["x"] = 3
    games[chat_id]["y"] = 0
    games[chat_id]["score"] = 0
    kb = []
    kb.append([InlineKeyboardButton("Ruota", callback_data="tet_rot"), InlineKeyboardButton("Giu", callback_data="tet_down")])
    kb.append([InlineKeyboardButton("SX", callback_data="tet_left"), InlineKeyboardButton("DX", callback_data="tet_right")])
    txt = "TETRIS\n" + render_tetris(games[chat_id])
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def move_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat_id = q.message.chat_id
    if chat_id not in games:
        return
    g = games[chat_id]
    data = q.data

    if g["type"] == "snake":
        if data == "snake_up":
            nd = (0,-1)
        if data == "snake_down":
            nd = (0,1)
        if data == "snake_left":
            nd = (-1,0)
        if data == "snake_right":
            nd = (1,0)
        # evita inversione
        if g["type"] == "snake":
            # check
            pass
        g["dir"] = nd
        hx = g["snake"][0][0] + g["dir"][0]
        hy = g["snake"][0][1] + g["dir"][1]
        nh = (hx, hy)
        if hx < 0 or hx >= 8 or hy < 0 or hy >= 8:
            await q.edit_message_text("Game Over! /snake")
            del games[chat_id]
            return
        if nh in g["snake"]:
            await q.edit_message_text("Game Over! /snake")
            del games[chat_id]
            return
        g["snake"] = [nh] + g["snake"]
        if nh == g["food"]:
            fx = random.randint(0,7)
            fy = random.randint(0,7)
            g["food"] = (fx,fy)
        else:
            g["snake"].pop()
        kb = []
        kb.append([InlineKeyboardButton("SU", callback_data="snake_up")])
        kb.append([InlineKeyboardButton("SX", callback_data="snake_left"), InlineKeyboardButton("GIU", callback_data="snake_down"), InlineKeyboardButton("DX", callback_data="snake_right")])
        sc = len(g["snake"]) - 3
        txt = "Score:" + str(sc) + "\n" + render_snake(g["snake"], g["food"])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    if g["type"] == "pacman":
        if data == "pac_up":
            nd = (0,-1)
        if data == "pac_down":
            nd = (0,1)
        if data == "pac_left":
            nd = (-1,0)
        if data == "pac_right":
            nd = (1,0)
        nx = g["pac"][0] + nd[0]
        ny = g["pac"][1] + nd[1]
        if 0 <= nx < 9 and 0 <= ny < 9:
            if PAC_MAZE[ny][nx] == "0":
                g["pac"] = (nx,ny)
                if g["pac"] in g["dots"]:
                    g["dots"].remove(g["pac"])
                    g["score"] += 10
        # ghost
        gx = g["ghost"][0]
        gy = g["ghost"][1]
        px = g["pac"][0]
        py = g["pac"][1]
        best = None
        bestdist = 999
        for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nnx = gx + dx
            nny = gy + dy
            if 0 <= nnx < 9 and 0 <= nny < 9:
                if PAC_MAZE[nny][nnx] == "0":
                    dist = abs(nnx-px) + abs(nny-py)
                    if dist < bestdist:
                        bestdist = dist
                        best = (nnx,nny)
        if best:
            g["ghost"] = best
        if g["pac"] == g["ghost"]:
            await q.edit_message_text("Beccato! Score:" + str(g["score"]) + " /pacman")
            del games[chat_id]
            return
        if len(g["dots"]) == 0:
            await q.edit_message_text("VITTORIA! Score:" + str(g["score"]))
            del games[chat_id]
            return
        kb = []
        kb.append([InlineKeyboardButton("SU", callback_data="pac_up")])
        kb.append([InlineKeyboardButton("SX", callback_data="pac_left"), InlineKeyboardButton("GIU", callback_data="pac_down"), InlineKeyboardButton("DX", callback_data="pac_right")])
        txt = "Score:" + str(g["score"]) + "\n" + render_pacman(g)
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    if g["type"] == "tetris":
        if data == "tet_left":
            nx = g["x"] - 1
            ok = can_move_tetris(g, nx, g["y"], g["piece"])
            if ok:
                g["x"] = nx
        if data == "tet_right":
            nx = g["x"] + 1
            ok = can_move_tetris(g, nx, g["y"], g["piece"])
            if ok:
                g["x"] = nx
        if data == "tet_rot":
            rot = []
            for x,y in g["piece"]:
                rot.append((-y,x))
            ok = can_move_tetris(g, g["x"], g["y"], rot)
            if ok:
                g["piece"] = rot
        if data == "tet_down":
            ny = g["y"] + 1
            ok = can_move_tetris(g, g["x"], ny, g["piece"])
            if ok:
                g["y"] = ny
            else:
                # blocca pezzo
                for dx,dy in g["piece"]:
                    x = g["x"] + dx
                    y = g["y"] + dy
                    if 0 <= y < 10 and 0 <= x < 10:
                        g["board"][y][x] = g["color"]
                new_board = []
                for row in g["board"]:
                    has_zero = False
                    for c in row:
                        if c == 0:
                            has_zero = True
                    if has_zero:
                        new_board.append(row)
                cleared = 10 - len(new_board)
                g["score"] += cleared * 100
                while len(new_board) < 10:
                    new_board = [[0]*10] + new_board
                g["board"] = new_board
                g["piece"] = [(0,0),(1,0),(2,0),(3,0)]
                g["x"] = 3
                g["y"] = 0
                ok2 = can_move_tetris(g, g["x"], g["y"], g["piece"])
                if not ok2:
                    await q.edit_message_text("Game Over! Score:" + str(g["score"]) + " /tetris")
                    del games[chat_id]
                    return
        kb = []
        kb.append([InlineKeyboardButton("Ruota", callback_data="tet_rot"), InlineKeyboardButton("Giu", callback_data="tet_down")])
        kb.append([InlineKeyboardButton("SX", callback_data="tet_left"), InlineKeyboardButton("DX", callback_data="tet_right")])
        txt = "TETRIS Score:" + str(g["score"]) + "\n" + render_tetris(g)
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    low = text.lower()
    print("MSG: " + text)

    if "tempo" in low or "meteo" in low or "bari" in low:
        city = "Bari"
        if "roma" in low:
            city = "Roma"
        if "milano" in low:
            city = "Milano"
        if "napoli" in low:
            city = "Napoli"
        if "bari" in low:
            city = "Bari"
        meteo = get_weather(city)
        if meteo:
            await update.message.reply_text(meteo)
        else:
            await update.message.reply_text("Non trovo meteo")
        return

    chat_type = update.effective_chat.type
    if chat_type in ["group", "supergroup"]:
        is_tag = "@nunzio" in low
        if "nunzio" in low[:7]:
            is_tag = True
        is_reply = False
        if update.message.reply_to_message:
            try:
                if update.message.reply_to_message.from_user.id == context.bot.id:
                    is_reply = True
            except:
                pass
        if not is_tag and not is_reply:
            return
        text = text.replace("@nunzio", "")
        text = text.replace("@Nunzio", "")
        if text.lower().startswith("nunzio"):
            text = text[6:]

    if client:
        try:
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Sei Nunzio, amico simpatico, italiano breve, naturale. Non dire mai E quindi? o Ti ascolto!"},
                    {"role": "user", "content": text}
                ],
                max_tokens=200,
                temperature=0.7
            )
            content = resp.choices[0].message.content
            if content and content.strip():
                await update.message.reply_text(content.strip()[:1000])
                return
        except:
            pass

    await update.message.reply_text("Ciao! Sono qui!")

def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN mancante!")
        return
    while True:
        try:
            print("Avvio bot polling...")
            b = ApplicationBuilder().token(BOT_TOKEN).build()
            b.add_handler(CommandHandler("start", start))
            b.add_handler(CommandHandler("snake", snake_cmd))
            b.add_handler(CommandHandler("pacman", pacman_cmd))
            b.add_handler(CommandHandler("tetris", tetris_cmd))
            b.add_handler(CallbackQueryHandler(move_callback))
            b.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
            print("Bot ONLINE FULL!")
            b.run_polling(drop_pending_updates=True)
        except Exception as e:
            print("Crash bot")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print("Flask parte")
    app.run(host="0.0.0.0", port=port)
