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
    return "Nunzio_bot is Live!"

games = {}

def render_board(snake, food, size=8):
    board = ""
    for y in range(size):
        for x in range(size):
            if (x,y) == food:
                board += "🍎"
            elif (x,y) in snake:
                board += "🟩" if (x,y) == snake[0] else "🟢"
            else:
                board += "⬛"
        board += "\n"
    return board

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio_bot 🤖\nSei su @Nunzio bot pugliese!\n\nComandi:\n/start - saluto\n/snake - gioca a Snake 🐍\nScrivimi qualsiasi cosa!")

async def snake_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    snake = [(3,3), (2,3), (1,3)]
    food = (random.randint(0,7), random.randint(0,7))
    games[chat_id] = {"snake": snake, "food": food, "dir": (1,0), "size": 8}
    keyboard = [
        [InlineKeyboardButton("⬆️", callback_data="up")],
        [InlineKeyboardButton("⬅️", callback_data="left"), InlineKeyboardButton("⬇️", callback_data="down"), InlineKeyboardButton("➡️", callback_data="right")]
    ]
    board = render_board(snake, food)
    await update.message.reply_text(f"🐍 Snake - usa le frecce!\n\n{board}", reply_markup=InlineKeyboardMarkup(keyboard))

async def move_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    if chat_id not in games:
        return
    game = games[chat_id]
    dirs = {"up": (0,-1), "down": (0,1), "left": (-1,0), "right": (1,0)}
    if query.data in dirs:
        nd = dirs[query.data]
        if (nd[0] * -1, nd[1] * -1) != game["dir"]:
            game["dir"] = nd
        head = game["snake"][0]
        new_head = (head[0] + game["dir"][0], head[1] + game["dir"][1])
        if not (0 <= new_head[0] < game["size"] and 0 <= new_head[1] < game["size"]):
            await query.edit_message_text("💥 Game Over! Hai sbattuto! Fai /snake per rigiocare")
            del games[chat_id]
            return
        if new_head in game["snake"]:
            await query.edit_message_text("💥 Game Over! Ti sei morso! Fai /snake per rigiocare")
            del games[chat_id]
            return
        game["snake"] = [new_head] + game["snake"]
        if new_head == game["food"]:
            game["food"] = (random.randint(0,7), random.randint(0,7))
        else:
            game["snake"].pop()
        keyboard = [
            [InlineKeyboardButton("⬆️", callback_data="up")],
            [InlineKeyboardButton("⬅️", callback_data="left"), InlineKeyboardButton("⬇️", callback_data="down"), InlineKeyboardButton("➡️", callback_data="right")]
        ]
        board = render_board(game["snake"], game["food"])
        score = len(game["snake"]) - 3
        await query.edit_message_text(f"🐍 Score: {score}\n\n{board}", reply_markup=InlineKeyboardMarkup(keyboard))

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not client:
        await update.message.reply_text("Manca chiave Groq!")
        return
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Sei Nunzio, un bot pugliese simpatico, verace, parli in dialetto barese/pugliese leggero, divertente."},
                {"role": "user", "content": update.message.text}
            ],
            max_tokens=300
        )
        await update.message.reply_text(resp.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERRORE FATALE: BOT_TOKEN non trovato su Render Environment!")
    else:
        print(f"BOT_TOKEN trovato: {BOT_TOKEN[:10]}...")
    # Flask in background, NON blocca più il bot!
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot Telegram partito... - Ora rispondo su Telegram!")
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("snake", snake_cmd))
    bot_app.add_handler(CallbackQueryHandler(move_callback))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    bot_app.run_polling()
