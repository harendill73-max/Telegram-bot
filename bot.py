import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

GAMES = {
    "pacman": "https://www.google.com/logos/2010/pacman10-hp.html",
    "tetris": "https://tetris.com/play-tetris",
    "tris": "https://playtictactoe.org/"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao Nunzio! Sono il tuo Nunsio_bot 🤖\n\nComandi:\n/giochi - lista giochi\n/admin - pannello padrone (solo tu)"
    )

async def giochi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for name, link in GAMES.items():
        keyboard.append([InlineKeyboardButton(f"🎮 {name.upper()}", url=link)])
    await update.message.reply_text("Scegli un gioco:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Non sei il padrone!")
        return
    await update.message.reply_text(
        "Pannello Padrone 👑\n\nUsa:\n/addgame NOME | LINK - aggiungi gioco\n/listgame - vedi giochi\nDel token non ti preoccupare, è su Render"
    )

async def addgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        text = " ".join(context.args)
        nome, link = text.split("|")
        GAMES[nome.strip().lower()] = link.strip()
        await update.message.reply_text(f"Gioco {nome} aggiunto!")
    except:
        await update.message.reply_text("Usa: /addgame Snake | https://link.com")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        return
    user = update.effective_user
    msg = f"📩 Da @{user.username} ({user.id}):\n{update.message.text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
    await update.message.reply_text("Messaggio inviato al padrone!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("giochi", giochi))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("addgame", addgame))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
