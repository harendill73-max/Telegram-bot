import os, threading, random
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
app = Flask(__name__)
@app.route('/')
def home(): return "Nunzio_bot V4 - POLISHED"

games = {}

# ===== SNAKE BELLO =====
def render_snake(snake, food, size=8):
    b=""
    b+="⬜"* (size+2) + "\n"
    for y in range(size):
        b+="⬜"
        for x in range(size):
            if (x,y)==food: b+="🍎"
            elif (x,y)==snake[0]: b+="😀"
            elif (x,y) in snake: b+="🟩"
            else: b+="⬛"
        b+="⬜\n"
    b+="⬜"* (size+2) + "\n"
    return b

# ===== PACMAN CON LABIRINTO VERO =====
PAC_MAZE = [
    "111111111",
    "100000001",
    "101110101",
    "100000001",
    "101010101",
    "100000001",
    "101110101",
    "100000001",
    "111111111",
]
def render_pacman(g):
    s=""
    for y in range(9):
        for x in range(9):
            if PAC_MAZE[y][x]=="1": s+="🟦"
            elif (x,y)==g["pac"]: s+="😋"
            elif (x,y)==g["ghost"]: s+="👻"
            elif (x,y) in g["dots"]: s+="·"
            else: s+="⬛"
        s+="\n"
    return s

# ===== TETRIS 10x10 CHE SI VEDE TUTTO =====
TETROS = {
    "I": [(0,0),(1,0),(2,0),(3,0)],
    "O": [(0,0),(1,0),(0,1),(1,1)],
    "T": [(0,0),(1,0),(2,0),(1,1)],
    "L": [(0,0),(0,1),(0,2),(1,2)],
    "S": [(1,0),(2,0),(0,1),(1,1)],
}
COLORS = {"I":"🟦","O":"🟨","T":"🟪","L":"🟧","S":"🟩"}

def render_tetris(g):
    tmp = [row[:] for row in g["board"]]
    for dx,dy in g["piece"]:
        x=g["x"]+dx; y=g["y"]+dy
        if 0<=y<10 and 0<=x<10:
            tmp[y][x]=g["color"]
    out="┏"+"━"*10+"┓\n"
    for y in range(10):
        out+="┃"
        for x in range(10):
            c=tmp[y][x]
            out+= c if c!=0 else "⬛"
        out+="┃\n"
    out+="┗"+"━"*10+"┛"
    return out

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Nunzio_bot V4 🤖\n/snake 🐍 classico\n/pacman 🟡 labirinto\n/tetris 🧱 10x10 perfetto\nTutto si vede sullo schermo!")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    snake=[(3,3),(2,3),(1,3)]
    food=(random.randint(0,7),random.randint(0,7))
    games[chat_id]={"type":"snake","snake":snake,"food":food,"dir":(1,0),"size":8}
    kb=[[InlineKeyboardButton("⬆️",callback_data="snake_up")],[InlineKeyboardButton("⬅️",callback_data="snake_left"),InlineKeyboardButton("⬇️",callback_data="snake_down"),InlineKeyboardButton("➡️",callback_data="snake_right")]]
    await update.message.reply_text(f"🐍 SNAKE Score:0\n{render_snake(snake,food)}",reply_markup=InlineKeyboardMarkup(kb))

async def pacman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    dots=[(x,y) for y in range(9) for x in range(9) if PAC_MAZE[y][x]=="0"]
    pacman=(4,4); ghost=(1,1)
    if pacman in dots: dots.remove(pacman)
    games[chat_id]={"type":"pacman","pac":pacman,"ghost":ghost,"dots":dots,"score":0}
    kb=[[InlineKeyboardButton("⬆️",callback_data="pac_up")],[InlineKeyboardButton("⬅️",callback_data="pac_left"),InlineKeyboardButton("⬇️",callback_data="pac_down"),InlineKeyboardButton("➡️",callback_data="pac_right")]]
    await update.message.reply_text(f"🟡 PACMAN Score:0\n{render_pacman(games[chat_id])}",reply_markup=InlineKeyboardMarkup(kb))

async def tetris_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    board=[[0]*10 for _ in range(10)]
    name=random.choice(list(TETROS.keys()))
    games[chat_id]={"type":"tetris","board":board,"piece":TETROS[name][:],"color":COLORS[name],"x":3,"y":0,"score":0,"name":name}
    kb=[[InlineKeyboardButton("🔄 Ruota",callback_data="tet_rot"),InlineKeyboardButton("⬇️ Giù",callback_data="tet_down")],[InlineKeyboardButton("⬅️",callback_data="tet_left"),InlineKeyboardButton("➡️",callback_data="tet_right")]]
    await update.message.reply_text(f"🧱 TETRIS Score:0 - 10x10\n{render_tetris(games[chat_id])}",reply_markup=InlineKeyboardMarkup(kb))

async def move_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    chat_id=q.message.chat_id
    if chat_id not in games: return
    g=games[chat_id]; data=q.data

    if g["type"]=="snake" and data.startswith("snake_"):
        dirs={"snake_up":(0,-1),"snake_down":(0,1),"snake_left":(-1,0),"snake_right":(1,0)}
        nd=dirs[data]
        if (nd[0]*-1,nd[1]*-1)!=g["dir"]: g["dir"]=nd
        nh=(g["snake"][0][0]+g["dir"][0], g["snake"][0][1]+g["dir"][1])
        if not (0<=nh[0]<8 and 0<=nh[1]<8) or nh in g["snake"]:
            await q.edit_message_text("💥 Snake Game Over! /snake"); del games[chat_id]; return
        g["snake"]=[nh]+g["snake"]
        if nh==g["food"]: g["food"]=(random.randint(0,7),random.randint(0,7))
        else: g["snake"].pop()
        kb=[[InlineKeyboardButton("⬆️",callback_data="snake_up")],[InlineKeyboardButton("⬅️",callback_data="snake_left"),InlineKeyboardButton("⬇️",callback_data="snake_down"),InlineKeyboardButton("➡️",callback_data="snake_right")]]
        await q.edit_message_text(f"🐍 Score:{len(g['snake'])-3}\n{render_snake(g['snake'],g['food'])}",reply_markup=InlineKeyboardMarkup(kb))

    elif g["type"]=="pacman" and data.startswith("pac_"):
        dirs={"pac_up":(0,-1),"pac_down":(0,1),"pac_left":(-1,0),"pac_right":(1,0)}
        nd=dirs[data]; nx=g["pac"][0]+nd[0]; ny=g["pac"][1]+nd[1]
        if 0<=nx<9 and 0<=ny<9 and PAC_MAZE[ny][nx]!="1":
            g["pac"]=(nx,ny)
            if g["pac"] in g["dots"]: g["dots"].remove(g["pac"]); g["score"]+=10
        # ghost muove
        gx,gy=g["ghost"]
        opts=[(gx+dx,gy+dy) for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)] if 0<=gx+dx<9 and 0<=gy+dy<9 and PAC_MAZE[gy+dy][gx+dx]!="1"]
        if opts: g["ghost"]=random.choice(opts)
        if g["pac"]==g["ghost"]:
            await q.edit_message_text(f"👻 Beccato! Score:{g['score']} /pacman"); del games[chat_id]; return
        if not g["dots"]:
            await q.edit_message_text(f"🏆 VITTORIA PACMAN! Score:{g['score']}"); del games[chat_id]; return
        kb=[[InlineKeyboardButton("⬆️",callback_data="pac_up")],[InlineKeyboardButton("⬅️",callback_data="pac_left"),InlineKeyboardButton("⬇️",callback_data="pac_down"),InlineKeyboardButton("➡️",callback_data="pac_right")]]
        await q.edit_message_text(f"🟡 PACMAN Score:{g['score']}\n{render_pacman(g)}",reply_markup=InlineKeyboardMarkup(kb))

    elif g["type"]=="tetris" and data.startswith("tet_"):
        if data=="tet_left" and g["x"]>0: g["x"]-=1
        if data=="tet_right" and g["x"]<6: g["x"]+=1
        if data=="tet_down": g["y"]+=1
        if data=="tet_rot": g["piece"]=[(-y,x) for x,y in g["piece"]]
        # fissa se tocca fondo
        if g["y"]>=8 or any(g["y"]+dy>=9 for _,dy in g["piece"]):
            for dx,dy in g["piece"]:
                x=g["x"]+dx; y=g["y"]+dy
                if 0<=y<10 and 0<=x<10: g["board"][y][x]=g["color"]
            # cancella linee piene
            new_board=[row for row in g["board"] if any(c==0 for c in row)]
            cleared=10-len(new_board)
            g["score"]+=cleared*100
            while len(new_board)<10: new_board=[[0]*10]+new_board
            g["board"]=new_board
            name=random.choice(list(TETROS.keys()))
            g["piece"]=TETROS[name][:]; g["color"]=COLORS[name]; g["x"]=3; g["y"]=0
            if any(g["board"][0][x]!=0 for x in range(10)):
                await q.edit_message_text(f"🧱 TETRIS Game Over! Score:{g['score']} /tetris"); del games[chat_id]; return
        kb=[[InlineKeyboardButton("🔄 Ruota",callback_data="tet_rot"),InlineKeyboardButton("⬇️ Giù",callback_data="tet_down")],[InlineKeyboardButton("⬅️",callback_data="tet_left"),InlineKeyboardButton("➡️",callback_data="tet_right")]]
        await q.edit_message_text(f"🧱 TETRIS Score:{g['score']}\n{render_tetris(g)}",reply_markup=InlineKeyboardMarkup(kb))

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp=client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":"Sei Nunzio, bot pugliese simpatico, dialetto barese leggero."},{"role":"user","content":update.message.text}],max_tokens=300)
        await update.message.reply_text(resp.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")

def run_flask():
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    print("Bot V4 POLISHED partito!")
    b=ApplicationBuilder().token(BOT_TOKEN).build()
    b.add_handler(CommandHandler("start",start))
    b.add_handler(CommandHandler("snake",snake_cmd))
    b.add_handler(CommandHandler("pacman",pacman_cmd))
    b.add_handler(CommandHandler("tetris",tetris_cmd))
    b.add_handler(CallbackQueryHandler(move_callback))
    b.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat))
    b.run_polling(drop_pending_updates=True)
