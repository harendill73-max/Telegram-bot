import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

TOKEN = os.getenv("BOT_TOKEN")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# False = AI accesa, True = AI bloccata (leggi tu)
ai_bloccata = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio_bot 🤖\n/startai per attivare AI\n/stopai per bloccare AI e leggere tu")

async def stop_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_bloccata
    ai_bloccata = True
    await update.message.reply_text("🔴 AI BLOCCATA!\nOra leggo solo io, non risponde più Nunzio.\nTu puoi leggere e rispondere a mano su Telegram.\nScrivi /startai per sbloccare.")

async def start_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_bloccata
    ai_bloccata = False
    await update.message.reply_text("🟢 AI SBLOCCATA!\nOra Nunzio risponde di nuovo da solo!")

async def snake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐍 Snake ok!")

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_bloccata
    # SE AI BLOCCATA, NON RISPONDE
    if ai_bloccata:
        return  # tu leggi il messaggio su Telegram e rispondi tu a mano

    try:
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "Sei Nunzio, AI pugliese simpatico, parli italiano."},
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
