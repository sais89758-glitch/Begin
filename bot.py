import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Railway Environment Variable မှ Token ကို ယူခြင်း
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎥 Movies", callback_data="movies")],
        [InlineKeyboardButton("📺 Series", callback_data="series")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "🎬 Movie Bot မှ ကြိုဆိုပါတယ်!\n\nCategory ကိုရွေးပါ 👇",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            "🎬 Movie Bot မှ ကြိုဆိုပါတယ်!\n\nCategory ကိုရွေးပါ 👇",
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "movies":
        await query.edit_message_text("🎥 Movies (မကြာမီ ထည့်မယ်)")
    elif query.data == "series":
        await query.edit_message_text("📺 Series (မကြာမီ ထည့်မယ်)")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing in Railway Variables!")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
