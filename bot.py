import os
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# --- FIX PER RENDER: apre una porta finta ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()
# --- FINE FIX ---

# --- IL TUO BOT ---
TOKEN = os.environ.get('TELEGRAM_API_KEY')

async def start(update, context):
    await update.message.reply_text("Ciao! Bot online su Render! 🚀")

async def echo(update, context):
    await update.message.reply_text(f"Hai scritto: {update.message.text}")

def main():
    print("Avvio bot...")
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    print("Bot avviato! In ascolto...")
    application.run_polling()

if __name__ == '__main__':
    main()
