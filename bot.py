import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

TOKEN = os.getenv("BOT_TOKEN")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunzio_bot 🤖\nScrivi qualcosa o /snake")

async def snake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐍 Snake ok!")

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
app.add_handler(CommandHandler("snake", snake))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))
print("Bot avviato...")
app.run_polling()
