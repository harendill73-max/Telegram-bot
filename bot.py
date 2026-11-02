import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot online! Inviami un messaggio.")

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    text = f"Da @{user.username or user.id} ({user.id}):\n{update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    await update.message.reply_text("Inviato all'admin!")

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN mancante")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin))
    app.run_polling()

if __name__ == "__main__":
    main()
