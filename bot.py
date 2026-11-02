import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono Nunsio_bot - cervellone pugliese! 🤖\nScrivi qualcosa o usa /snake /tetris")

async def snake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐍 SNAKE:\n⬆️⬅️➡️⬇️ usa le frecce!")

async def tetris(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟦 TETRIS in arrivo...")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_text = update.message.text
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Sei Nunsio, un AI pugliese simpatico, alla mano, parli in italiano."},
                {"role": "user", "content": user_text}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"AI offline: {e}")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("snake", snake))
app.add_handler(CommandHandler("tetris", tetris))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot avviato...")
app.run_polling()
