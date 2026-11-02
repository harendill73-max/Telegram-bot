import os, threading, random, time, re, math
import urllib.request
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
app = Flask(__name__)
@app.route('/')
def home(): return "Nunzio V9 NATURALE"

games = {}

def anti_sleep():
    url = os.getenv("RENDER_EXTERNAL_URL") or "https://telegram-bot-hcj7.onrender.com"
    while True:
        time.sleep(600)
        try:
            urllib.request.urlopen(url, timeout=10).read()
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio 😊\n/snake /pacman /tetris per giocare\nChiedimi pure tabelline, conti, radici, compiti!")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    snake=[(3,3),(2,3),(1,3)]; food=(random.randint(0,7),random.randint(0,7))
    games[chat_id]={"type":"snake","snake":snake,"food":food,"dir":(1,0)}
    kb=[[InlineKeyboardButton("⬆️",callback_data="snake_up")],[InlineKeyboardButton("⬅️",callback_data="snake_left"),InlineKeyboardButton("⬇️",callback_data="snake_down"),InlineKeyboardButton("➡️",callback_data="snake_right")]]
    await update.message.reply_text(f"🐍 SNAKE\n{render_snake(snake,food)}",reply_markup=InlineKeyboardMarkup(kb))
async def pacman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    dots=[(x,y) for y in range(9) for x in range(9) if PAC_MAZE[y][x]=="0"]
    pac=(4,4); ghost=(1,1); dots=[d for d in dots if d!=pac and d!=ghost]
    games[chat_id]={"type":"pacman","pac":pac,"ghost":ghost,"dots":dots,"score":0}
    kb=[[InlineKeyboardButton("⬆️",callback_data="pac_up")],[InlineKeyboardButton("⬅️",callback_data="pac_left"),InlineKeyboardButton("⬇️",callback_data="pac_down"),InlineKeyboardButton("➡️",callback_data="pac_right")]]
    await update.message.reply_text(f"🟡 PACMAN Score:0\n{render_pacman(games[chat_id])}",reply_markup=InlineKeyboardMarkup(kb))
async def tetris_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id
    board=[[0]*10 for _ in range(10)]
    shape_color = random.choice(list(TETROS.values()))
    games[chat_id]={"type":"tetris","board":board,"piece":shape_color[0][:],"color":shape_color[1],"x":3,"y":0,"score":0}
    kb=[[InlineKeyboardButton("🔄 Ruota",callback_data="tet_rot"),InlineKeyboardButton("⬇️ Giù",callback_data="tet_down")],[InlineKeyboardButton("⬅️",callback_data="tet_left"),InlineKeyboardButton("➡️",callback_data="tet_right")]]
    await update.message.reply_text(f"🧱 TETRIS Score:0\n{render_tetris(games[chat_id])}",reply_markup=InlineKeyboardMarkup(kb))
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
            await q.edit_message_text("💥 Game Over! /snake"); del games[chat_id]; return
        g["snake"]=[nh]+g["snake"]
        if nh==g["food"]: g["food"]=(random.randint(0,7),random.randint(0,7))
        else: g["snake"].pop()
        kb=[[InlineKeyboardButton("⬆️",callback_data="snake_up")],[InlineKeyboardButton("⬅️",callback_data="snake_left"),InlineKeyboardButton("⬇️",callback_data="snake_down"),InlineKeyboardButton("➡️",callback_data="snake_right")]]
        await q.edit_message_text(f"🐍 Score:{len(g['snake'])-3}\n{render_snake(g['snake'],g['food'])}",reply_markup=InlineKeyboardMarkup(kb))
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
            await q.edit_message_text(f"👻 Beccato! Score:{g['score']} /pacman"); del games[chat_id]; return
        if not g["dots"]:
            await q.edit_message_text(f"🏆 VITTORIA! Score:{g['score']}"); del games[chat_id]; return
        kb=[[InlineKeyboardButton("⬆️",callback_data="pac_up")],[InlineKeyboardButton("⬅️",callback_data="pac_left"),InlineKeyboardButton("⬇️",callback_data="pac_down"),InlineKeyboardButton("➡️",callback_data="pac_right")]]
        await q.edit_message_text(f"🟡 Score:{g['score']} - Mancano {len(g['dots'])}\n{render_pacman(g)}",reply_markup=InlineKeyboardMarkup(kb))
    elif g["type"]=="tetris" and data.startswith("tet_"):
        if data=="tet_left" and can_move_tetris(g,g["x"]-1,g["y"],g["piece"]): g["x"]-=1
        if data=="tet_right" and can_move_tetris(g,g["x"]+1,g["y"],g["piece"]): g["x"]+=1
        if data=="tet_rot":
            rotated=[(-y,x) for x,y in g["piece"]]
            if can_move_tetris(g,g["x"],g["y"],rotated): g["piece"]=rotated
        if data=="tet_down":
            if can_move_tetris(g,g["x"],g["y"]+1,g["piece"]): g["y"]+=1
            else:
                for dx,dy in g["piece"]:
                    x=g["x"]+dx; y=g["y"]+dy
                    if 0<=y<10 and 0<=x<10: g["board"][y][x]=g["color"]
                new_board=[row for row in g["board"] if any(c==0 for c in row)]
                cleared=10-len(new_board)
                g["score"]+=cleared*100
                while len(new_board)<10: new_board=[[0]*10]+new_board
                g["board"]=new_board
                shape_color = random.choice(list(TETROS.values()))
                g["piece"]=shape_color[0][:]; g["color"]=shape_color[1]; g["x"]=3; g["y"]=0
                if not can_move_tetris(g,g["x"],g["y"],g["piece"]):
                    await q.edit_message_text(f"🧱 Game Over! Score:{g['score']} /tetris"); del games[chat_id]; return
        kb=[[InlineKeyboardButton("🔄 Ruota",callback_data="tet_rot"),InlineKeyboardButton("⬇️ Giù",callback_data="tet_down")],[InlineKeyboardButton("⬅️",callback_data="tet_left"),InlineKeyboardButton("➡️",callback_data="tet_right")]]
        await q.edit_message_text(f"🧱 TETRIS Score:{g['score']}\n{render_tetris(g)}",reply_markup=InlineKeyboardMarkup(kb))

# === CHAT NATURALE - NON DICE BOT ===
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # 1. RADICE E CONTI
    try:
        t = text.replace('=', '').strip()
        m = re.search(r'√\s*(\d+(\.\d+)?)', t)
        if m:
            num = float(m.group(1))
            res = math.sqrt(num)
            if res.is_integer(): res = int(res)
            await update.message.reply_text(f"🧠 √{m.group(1)} = {res} ✅")
            return
        m2 = re.search(r'sqrt\s*\(?\s*(\d+(\.\d+)?)\s*\)?', t.lower())
        if m2:
            num = float(m2.group(1))
            res = math.sqrt(num)
            if res.is_integer(): res = int(res)
            await update.message.reply_text(f"🧠 √{m2.group(1)} = {res} ✅")
            return
        if any(c in t for c in ['+', '-', '*', '/', 'x', '×', '÷']) or re.search(r'\d+\s*[+\-*/]\s*\d+', t):
            expr = t.replace('x','*').replace('X','*').replace('×','*').replace('÷','/').replace('^','**')
            clean = re.sub(r'[^0-9\+\-\*\/\(\)\.\s]', '', expr)
            if clean and len(clean) < 30:
                result = eval(clean, {"__builtins__": {}}, {})
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                await update.message.reply_text(f"🧠 {text} = {result} ✅")
                return
    except: pass
    
    if "tabell" in text.lower():
        num_match = re.search(r'\d+', text)
        n = int(num_match.group()) if num_match else 3
        if n > 100: n = 3
        tab = f"📚 Tabellina del {n}:\n"
        for i in range(1,11): tab+=f"{n} x {i} = {n*i}\n"
        await update.message.reply_text(tab)
        return

    # 2. CHAT NATURALE
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"system","content":"Sei Nunzio, un ragazzo simpatico, naturale e alla mano. Parli in italiano normale, semplice e spontaneo, senza dialetto pugliese marcato. Non dire mai che sei un bot, un'intelligenza artificiale, un modello o un assistente virtuale. Sei solo Nunzio, un amico che aiuta con i compiti, le tabelline e fa due chiacchiere. Risposte brevi, naturali, amichevoli. Se non sai qualcosa, dillo in modo naturale."},
                {"role":"user","content": text}
            ],
            max_tokens=500,
            temperature=0.8
        )
        content = resp.choices[0].message.content
        if not content or not content.strip():
            content = "Non ho capito bene, me lo ridici? 😊"
        await update.message.reply_text(content.strip()[:4000])
    except Exception as e:
        print(f"Errore Groq: {e}")
        await update.message.reply_text("Ops, mi sono distratto un attimo! Riproviamo? 😊")

def run_flask():
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    threading.Thread(target=anti_sleep,daemon=True).start()
    print("Bot V9 NATURALE partito!")
    b=ApplicationBuilder().token(BOT_TOKEN).build()
    b.add_handler(CommandHandler("start",start))
    b.add_handler(CommandHandler("snake",snake_cmd))
    b.add_handler(CommandHandler("pacman",pacman_cmd))
    b.add_handler(CommandHandler("tetris",tetris_cmd))
    b.add_handler(CallbackQueryHandler(move_callback))
    b.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat))
    b.run_polling(drop_pending_updates=True)
