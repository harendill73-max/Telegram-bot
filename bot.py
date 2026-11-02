import os, json, sqlite3, random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = "Hadner" # tu sei l'admin
GROQ_KEY = os.getenv("GROQ_API_KEY", "") # la aggiungiamo dopo

# --- DATABASE UTENTI ---
conn = sqlite3.connect("users.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_seen TEXT, msgs INTEGER DEFAULT 0)")
conn.commit()

def track_user(user):
    try:
        cur = conn.cursor()
        cur.execute("SELECT msgs FROM users WHERE id=?", (user.id,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET username=?, first_name=?, last_seen=?, msgs=msgs+1 WHERE id=?", (user.username, user.first_name, datetime.now().isoformat(), user.id))
        else:
            cur.execute("INSERT INTO users VALUES (?,?,?,?,0)", (user.id, user.username, user.first_name, datetime.now().isoformat()))
        conn.commit()
    except: pass

# --- AI CERVELLO ---
async def ai_reply(prompt):
    if not GROQ_KEY:
        return "🧠 Sono Nunzio Cervellone! (AI non ancora configurata, aggiungi GROQ_API_KEY su Render). Dimmi pure: " + prompt
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        comp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":"Sei Nunzio, un bot italiano simpatico, esperto di giochi, aiuti tutti, parli in dialetto pugliese leggero."},{"role":"user","content":prompt}])
        return comp.choices[0].message.content
    except Exception as e:
        return f"AI momentaneamente offline: {e}. Ma sono qui! {prompt}"

# --- COMANDI BASE ---
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    await update.message.reply_text(f"Ciao {update.effective_user.first_name}! Sono Nunzio CERVELLONE 🧠🎮\n\nComandi:\n/ Snake - gioca a Snake\n/tetris - Tetris\n/pacman - Pacman\n/ai dimmi qualcosa - parla con l'AI\n/utenti (solo admin)\n/broadcast messaggio (solo admin)\n/stat")

async def stat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(msgs) FROM users")
    c, m = cur.fetchone()
    await update.message.reply_text(f"📊 Utenti totali: {c or 0}\nMessaggi totali: {m or 0}")

async def utenti(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME: return
    cur = conn.cursor()
    cur.execute("SELECT id, username, first_name, msgs, last_seen FROM users ORDER BY msgs DESC LIMIT 20")
    rows = cur.fetchall()
    txt = "👁️ Ultimi utenti:\n\n"
    for r in rows: txt += f"• {r[2]} @{r[1]} - {r[3]} msg - {r[0]}\n"
    await update.message.reply_text(txt)

async def broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME: return
    msg = " ".join(ctx.args)
    if not msg: await update.message.reply_text("Uso: /broadcast Ciao a tutti!"); return
    cur = conn.cursor()
    cur.execute("SELECT id FROM users")
    ok=0
    for (uid,) in cur.fetchall():
        try: await ctx.bot.send_message(uid, f"📢 Messaggio da Nunzio:\n\n{msg}"); ok+=1
        except: pass
    await update.message.reply_text(f"Inviato a {ok} utenti.")

# --- SNAKE SEMPLICE ---
games = {}
async def snake(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    board = [["⬜"]*5 for _ in range(5)]
    sx, sy = 2,2
    fx, fy = random.randint(0,4), random.randint(0,4)
    board[sy][sx]="🟩"
    board[fy][fx]="🍎"
    games[update.effective_user.id]={"x":sx,"y":sy,"fx":fx,"fy":fy,"score":0}
    txt = "\n".join("".join(r) for r in board) + f"\n\nScore: 0"
    kb = [[InlineKeyboardButton("⬆️", callback_data="sn_up"),],[InlineKeyboardButton("⬅️", callback_data="sn_left"),InlineKeyboardButton("➡️", callback_data="sn_right"),],[InlineKeyboardButton("⬇️", callback_data="sn_down"),]]
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def snake_move(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    uid=q.from_user.id
    if uid not in games: return
    g=games[uid]
    if "up" in q.data: g["y"]=max(0,g["y"]-1)
    if "down" in q.data: g["y"]=min(4,g["y"]+1)
    if "left" in q.data: g["x"]=max(0,g["x"]-1)
    if "right" in q.data: g["x"]=min(4,g["x"]+1)
    if g["x"]==g["fx"] and g["y"]==g["fy"]:
        g["score"]+=1
        g["fx"],g["fy"]=random.randint(0,4),random.randint(0,4)
    board=[["⬜"]*5 for _ in range(5)]
    board[g["fy"]][g["fx"]]="🍎"
    board[g["y"]][g["x"]]="🟩"
    txt="\n".join("".join(r) for r in board)+f"\n\nScore: {g['score']}"
    kb=[[InlineKeyboardButton("⬆️", callback_data="sn_up"),],[InlineKeyboardButton("⬅️", callback_data="sn_left"),InlineKeyboardButton("➡️", callback_data="sn_right"),],[InlineKeyboardButton("⬇️", callback_data="sn_down"),]]
    await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def tetris(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    await update.message.reply_text("🕹️ TETRIS - Versione base in arrivo! Per ora gioca a /snake. Vuoi la versione con grafica vera? Te la preparo come WebApp.")

async def pacman(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    await update.message.reply_text("👻 PACMAN - Versione base in arrivo! Per ora gioca a /snake. WebApp in preparazione.")

# --- MESSAGGI AI ---
async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    if update.message.text.startswith("/"): return
    # Se scrive in privato, risponde AI
    reply = await ai_reply(update.message.text)
    await update.message.reply_text(reply)

async def ai_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    prompt=" ".join(ctx.args)
    if not prompt: await update.message.reply_text("Scrivi: /ai Ciao come stai?"); return
    reply = await ai_reply(prompt)
    await update.message.reply_text(reply)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stat", stat))
    app.add_handler(CommandHandler("utenti", utenti))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("snake", snake))
    app.add_handler(CommandHandler("tetris", tetris))
    app.add_handler(CommandHandler("pacman", pacman))
    app.add_handler(CommandHandler("ai", ai_cmd))
    app.add_handler(CallbackQueryHandler(snake_move, pattern="^sn_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("Bot cervellone online!")
    app.run_polling()

if __name__=="__main__": main()
