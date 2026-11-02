import os
import threading
import random
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
    return "Nunzio_bot V3 - Snake Pacman Tetris Live!"

games = {}

# ========== UTILS ==========
def render_snake(snake, food, size=8):
    board = ""
    for y in range(size):
        for x in range(size):
            if (x,y) == food: board += "🍎"
            elif (x,y) in snake: board += "🟩" if (x,y) == snake[0] else "🟢"
            else: board += "⬛"
        board += "\n"
    return board

# ========== SNAKE (INTATTO) ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio_bot 🤖\nComandi:\n/start\n/snake 🐍\n/pacman 🟡\n/tetris 🧱\nScrivimi!")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    snake = [(3,3), (2,3), (1,3)]
    food = (random.randint(0,7), random.randint(0,7))
    games[chat_id] = {"type":"snake", "snake": snake, "food": food, "dir": (1,0), "size": 8}
    kb = [[InlineKeyboardButton("⬆️", callback_data="snake_up")],
          [InlineKeyboardButton("⬅️", callback_data="snake_left"), InlineKeyboardButton("⬇️", callback_data="snake_down"), InlineKeyboardButton("➡️", callback_data="snake_right")]]
    await update.message.reply_text(f"🐍 Snake\n\n{render_snake(snake, food)}", reply_markup=InlineKeyboardMarkup(kb))

# ========== PACMAN NUOVO ==========
async def pacman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # mappa 7x7, 0=vuoto con punto, 1=muro
    maze = [[0]*7 for _ in range(7)]
    pacman = (3,3)
    ghost = (0,0)
    dots = [(x,y) for x in range(7) for y in range(7) if (x,y) not in [pacman, ghost]]
    games[chat_id] = {"type":"pacman", "pac": pacman, "ghost": ghost, "dots": dots, "score":0, "size":7}
    kb = [[InlineKeyboardButton("⬆️", callback_data="pac_up")],
          [InlineKeyboardButton("⬅️", callback_data="pac_left"), InlineKeyboardButton("⬇️", callback_data="pac_down"), InlineKeyboardButton("➡️", callback_data="pac_right")]]
    await update.message.reply_text(f"🟡 PACMAN Score:0\n\n{render_pacman(games[chat_id])}", reply_markup=InlineKeyboardMarkup(kb))

def render_pacman(g):
    board=""
    for y in range(g["size"]):
        for x in range(g["size"]):
            if (x,y)==g["pac"]: board+="🟡"
            elif (x,y)==g["ghost"]: board+="👻"
            elif (x,y) in g["dots"]: board+="· "
            else: board+="⬛"
        board+="\n"
    return board

# ========== TETRIS NUOVO SEMPLICE ==========
TETROMINOS = {
    "I": [(0,0),(1,0),(2,0),(3,0)],
    "O": [(0,0),(1,0),(0,1),(1,1)],
    "T": [(0,0),(1,0),(2,0),(1,1)],
}
async def tetris_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    board = [[0]*8 for _ in range(12)]
    piece = random.choice(list(TETROMINOS.values()))
    px, py = 2, 0
    games[chat_id] = {"type":"tetris", "board":board, "piece":piece, "x":px, "y":py, "score":0}
    kb = [[InlineKeyboardButton("🔄", callback_data="tet_rot"), InlineKeyboardButton("⬇️", callback_data="tet_down")],
          [InlineKeyboardButton("⬅️", callback_data="tet_left"), InlineKeyboardButton("➡️", callback_data="tet_right")]]
    await update.message.reply_text(f"🧱 TETRIS Score:0\n\n{render_tetris(games[chat_id])}", reply_markup=InlineKeyboardMarkup(kb))

def render_tetris(g):
    tmp = [row[:] for row in g["board"]]
    for dx,dy in g["piece"]:
        x = g["x"]+dx
        y = g["y"]+dy
        if 0 <= y < 12 and 0 <= x < 8:
            tmp[y][x]=1
    s=""
    for y in range(12):
        for x in range(8):
            s += "🟦" if tmp[y][x] else "⬛"
        s+="\n"
    return s

# ========== CALLBACK UNICO CHE NON ROMPE ==========
async def move_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    if chat_id not in games: return
    g = games[chat_id]
    data = query.data

    # SNAKE
    if g["type"]=="snake" and data.startswith("snake_"):
        dirs = {"snake_up": (0,-1), "snake_down": (0,1), "snake_left": (-1,0), "snake_right": (1,0)}
        nd = dirs[data]
        if (nd[0]*-1, nd[1]*-1) != g["dir"]: g["dir"]=nd
        new_head = (g["snake"][0][0]+g["dir"][0], g["snake"][0][1]+g["dir"][1])
        if not (0 <= new_head[0] < g["size"] and 0 <= new_head[1] < g["size"]) or new_head in g["snake"]:
            await query.edit_message_text("💥 Snake Game Over! /snake per rigiocare"); del games[chat_id]; return
        g["snake"]=[new_head]+g["snake"]
        if new_head==g["food"]: g["food"]=(random.randint(0,7), random.randint(0,7))
        else: g["snake"].pop()
        kb = [[InlineKeyboardButton("⬆️", callback_data="snake_up")],[InlineKeyboardButton("⬅️", callback_data="snake_left"), InlineKeyboardButton("⬇️", callback_data="snake_down"), InlineKeyboardButton("➡️", callback_data="snake_right")]]
        await query.edit_message_text(f"🐍 Score:{len(g['snake'])-3}\n\n{render_snake(g['snake'], g['food'])}", reply_markup=InlineKeyboardMarkup(kb))

    # PACMAN
    elif g["type"]=="pacman" and data.startswith("pac_"):
        dirs = {"pac_up": (0,-1), "pac_down": (0,1), "pac_left": (-1,0), "pac_right": (1,0)}
        nd = dirs[data]
        nx = max(0, min(g["size"]-1, g["pac"][0]+nd[0]))
        ny = max(0, min(g["size"]-1, g["pac"][1]+nd[1]))
        g["pac"]=(nx,ny)
        if g["pac"] in g["dots"]: g["dots"].remove(g["pac"]); g["score"]+=10
        # ghost random
        gx, gy = g["ghost"]
        g["ghost"]=(max(0,min(6,gx+random.choice([-1,0,1]))), max(0,min(6,gy+random.choice([-1,0,1]))))
        if g["pac"]==g["ghost"]:
            await query.edit_message_text(f"👻 Game Over Pacman! Score:{g['score']} /pacman per rigiocare"); del games[chat_id]; return
        if not g["dots"]:
            await query.edit_message_text(f"🏆 Hai vinto Pacman! Score:{g['score']}"); del games[chat_id]; return
        kb = [[InlineKeyboardButton("⬆️", callback_data="pac_up")],[InlineKeyboardButton("⬅️", callback_data="pac_left"), InlineKeyboardButton("⬇️", callback_data="pac_down"), InlineKeyboardButton("➡️", callback_data="pac_right")]]
        await query.edit_message_text(f"🟡 PACMAN Score:{g['score']}\n\n{render_pacman(g)}", reply_markup=InlineKeyboardMarkup(kb))

    # TETRIS
    elif g["type"]=="tetris" and data.startswith("tet_"):
        if data=="tet_left": g["x"]=max(0,g["x"]-1)
        if data=="tet_right": g["x"]=min(7,g["x"]+1)
        if data=="tet_down": g["y"]+=1
        if data=="tet_rot": g["piece"]=[(-y,x) for x,y in g["piece"]]
        # check collision bottom
        if g["y"]>=10 or any(g["y"]+dy>=11 for _,dy in g["piece"]):
            # fissa pezzo
            for dx,dy in g["piece"]:
                x=g["x"]+dx; y=g["y"]+dy
                if 0<=y<12 and 0<=x<8: g["board"][y][x]=1
            g["piece"]=random.choice(list(TETROMINOS.values())); g["x"]=2; g["y"]=0; g["score"]+=10
            if any(g["board"][0][x] for x in range(8)):
                await query.edit_message_text(f"🧱 Tetris Game Over! Score:{g['score']} /tetris per rigiocare"); del games[chat_id]; return
        kb = [[InlineKeyboardButton("🔄", callback_data="tet_rot"), InlineKeyboardButton("⬇️", callback_data="tet_down")],[InlineKeyboardButton("⬅️", callback_data="tet_left"), InlineKeyboardButton("➡️", callback_data="tet_right")]]
        await query.edit_message_text(f"🧱 TETRIS Score:{g['score']}\n\n{render_tetris(g)}", reply_markup=InlineKeyboardMarkup(kb))

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not client:
        await update.message.reply_text("Manca chiave Groq!"); return
    try:
        resp = client.chat.completions.create(model="openai/gpt-oss-20b",
            messages=[{"role":"system","content":"Sei Nunzio, bot pugliese simpatico, dialetto barese leggero, divertente."},{"role":"user","content":update.message.text}], max_tokens=300)
        await update.message.reply_text(resp.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    print(f"BOT_TOKEN: {BOT_TOKEN[:10] if BOT_TOKEN else 'MANCANTE'}...")
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot V3 partito - Snake Pacman Tetris!")
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("snake", snake_cmd))
    bot_app.add_handler(CommandHandler("pacman", pacman_cmd))
    bot_app.add_handler(CommandHandler("tetris", tetris_cmd))
    bot_app.add_handler(CallbackQueryHandler(move_callback))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    bot_app.run_polling(drop_pending_updates=True)
