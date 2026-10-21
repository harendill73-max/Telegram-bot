import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono online! ✅\n\n"
        "/start - Avvia il bot\n"
        "/help - Aiuto"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sono attivo su Render! Funziono 24/7 🚀")

def main():
    if not TOKEN:
        print("ERRORE: BOT_TOKEN mancante su Render!")
        return
    
    print("Avvio bot...")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    print("Bot avviato, in polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
