import os
import threading
from flask import Flask
from telegram.ext import Application
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import filters

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    p = os.environ.get("PORT", "10000")
    port = int(p)
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get('TELEGRAM_API_KEY')

async def start(update, context):
    await update.message.reply_text("Ciao! Bot online!")

async def echo(update, context):
    txt = update.message.text
    await update.message.reply_text(f"Hai scritto: {txt}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, echo))
    application.run_polling()

if __name__ == '__main__':
    main()
