import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# --- FIX PER RENDER (server finto) ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Nunzio bot is online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()
# --- FINE FIX ---

TOKEN = os.getenv("BOT_TOKEN")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ADMIN_USERNAME = "hadner"
ai_bloccata = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio_bot 🤖\nSei su @Nunzio bot pugliese!")

async def stop_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_bloccata
    user = update.effective_user.username
    if user != ADMIN_USERNAME:
        await update.message.reply_text("⛔ Solo @hadner può bloccare l'AI!")
        return
    ai_bloccata = True
    await update.message.reply_text("🔴 AI BLOCCATA da @hadner!\nOra Nunzio non risponde. Tu leggi i messaggi e rispondi tu a mano.\nScrivi /startai per sbloccare.")

async def start_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_bloccata
    user = update.effective_user.username
    if user != ADMIN_USERNAME:
        await update.message.reply_text("⛔ Solo @hadner può sbloccare l'AI!")
        return
    ai_bloccata = False
    await update.message.reply_text("🟢 AI SBLOCCATA! Nunzio è tornato!")

async def snake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐍 Snake - usa le frecce!")

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ai_bloccata:
        return
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Sei Nunzio, AI pugliese simpatico, parli italiano con accento pugliese leggero, divertente."},
                {"role": "user", "content": update.message.text}
            ]
        )
        await update.message.reply_text(r.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")

# --- AVVIO BOT ---
telegram_app = Application.builder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("stopai", stop_ai))
telegram_app.add_handler(CommandHandler("startai", start_ai))
telegram_app.add_handler(CommandHandler("snake", snake))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))

print("Bot avviato...")
telegram_app.run_polling()
