import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

# Logging များဖွင့်ပါ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Categories ကို မြန်မာဘာသာဖြင့် သတ်မှတ်ပါ
CATEGORIES = [
    "1️⃣ အက်ရှင် (Action) 💥", "2️⃣ အချစ်ဇာတ်လမ်း (Romance) 💖", 
    "3️⃣ ဟာသ (Comedy) 😂", "4️⃣ သရဲ/ထိတ်လန့် (Horror) 👻",
    "5️⃣ သိပ္ပံနှင့်အာကာသ (Sci-Fi) 👽", "6️⃣ ဒရာမာ (Drama) 🎭", 
    "7️⃣ သည်းထိတ်ရင်ဖို (Thriller) 🔪", "8️⃣ ကာတွန်း (Animation) 🎬",
    "9️⃣ နန်းတွင်းဇာတ်လမ်း 🏯", "🔟 အိမ်ထောင်ရေးဇာတ်လမ်း 🏠"
]

# /start command အတွက်
def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton(category, callback_data=category) for category in CATEGORIES.values()]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('ဇာတ်လမ်းအမျိုးအစားကို ရွေးချယ်ပါ:', reply_markup=reply_markup)

# Admin command
def admin(update: Update, context: CallbackContext):
    update.message.reply_text("Admin Panel:\nဇာတ်ကားများထည့်ရန် /add သုံးပါ။\nအချက်အလက်များအတွက် /stats_day, /stats_week သုံးပါ။")

# Stats commands
def stats_day(update: Update, context: CallbackContext):
    update.message.reply_text("နေ့စဉ်အချက်အလက်များ: [အချက်အလက်များ]")

def stats_week(update: Update, context: CallbackContext):
    update.message.reply_text("အပတ်စဉ်အချက်အလက်များ: [အချက်အလက်များ]")

# Top command
def top(update: Update, context: CallbackContext):
    update.message.reply_text("အထက်ဆုံးဇာတ်ကားများ: [အထက်ဆုံးဇာတ်ကားများ]")

# History command
def history_all(update: Update, context: CallbackContext):
    update.message.reply_text("ဇာတ်ကားမှတ်တမ်းများ: [မှတ်တမ်းများ]")

# Setting command
def settings(update: Update, context: CallbackContext):
    update.message.reply_text("Settings feature: သင့်ဇာတ်လမ်းများကို ပြုပြင်သွားနိုင်ပါတယ်။")

# Bot သည် command များကို ထည့်ပါ
def main():
    updater = Updater("8210400472:AAFapdRKx4uCa_vQFQnJvnRg8RZuOJX1wpY", use_context=True)
    
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CommandHandler("stats_day", stats_day))
    dp.add_handler(CommandHandler("stats_week", stats_week))
    dp.add_handler(CommandHandler("top", top))
    dp.add_handler(CommandHandler("history_all", history_all))
    dp.add_handler(CommandHandler("setting", settings))

    # Bot ကို စတင်ပါ
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
