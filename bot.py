import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Railway Variables ထဲက BOT_TOKEN ကို ဖတ်ယူခြင်း
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎥 Movies", callback_data="movies")],
        [InlineKeyboardButton("📺 Series", callback_data="series")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Message ကနေလာတာလား Callback ကနေလာတာလား စစ်ဆေးခြင်း
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

# ခလုတ်များနှိပ်လိုက်လျှင် အလုပ်လုပ်မည့်အပိုင်း
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "movies":
        await query.edit_message_text("🎥 Movies (မကြာမီ ထည့်မယ်)")
    elif query.data == "series":
        await query.edit_message_text("📺 Series (မကြာမီ ထည့်မယ်)")

def main():
    # Token ရှိမရှိ အရင်စစ်ဆေးခြင်း
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing! Please check Railway Variables.")
        return

    # Application တည်ဆောက်ခြင်း
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command နှင့် Handler များ ထည့်သွင်းခြင်း
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Bot ကို စတင် Run ခြင်း
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
