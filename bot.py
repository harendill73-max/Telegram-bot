import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

TOKEN = os.getenv("BOT_TOKEN")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ADMIN_USERNAME = "hadner"  # solo tu puoi bloccare l'AI
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
        return # AI bloccata, tu leggi e rispondi a mano
    try:
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "Sei Nunzio, AI pugliese simpatico, parli italiano con accento pugliese leggero, divertente."},
                {"role": "user", "content": update.message.text}
            ]
        )
        await update.message.reply_text(r.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Errore: {e}")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stopai", stop_ai))
app.add_handler(CommandHandler("startai", start_ai))
app.add_handler(CommandHandler("snake", snake))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))
app.run_polling()
