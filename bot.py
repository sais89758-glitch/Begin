import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIG ---
TOKEN = '8210400472:AAGsYRGnoyVCJH1gBw32mF2QpFZ84it-Ick'
ADMIN_ID = 8466996343

CATEGORIES = [
    "1️⃣ အက်ရှင် (Action) 💥", "2️⃣ အချစ်ဇာတ်လမ်း (Romance) 💖", 
    "3️⃣ ဟာသ (Comedy) 😂", "4️⃣ သရဲ/ထိတ်လန့် (Horror) 👻",
    "5️⃣ သိပ္ပံနှင့်အာကာသ (Sci-Fi) 👽", "6️⃣ ဒရာမာ (Drama) 🎭", 
    "7️⃣ သည်းထိတ်ရင်ဖို (Thriller) 🔪", "8️⃣ ကာတွန်း (Animation) 🎬",
    "9️⃣ မှတ်တမ်းတင် (Documentary) 🌍", "🔟 ဇာတ်လမ်းတွဲများ (Series) 📺"
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for cat in CATEGORIES:
        row.append(InlineKeyboardButton(cat, callback_data=f"view_cat|{cat}"))
        if len(row) == 2:
            keyboard.append(row); row = []
    if row: keyboard.append(row)
    await update.message.reply_text("👋 မင်္ဂလာပါ! အမျိုးအစားရွေးချယ်ပါ။", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🛠 Admin Mode အသုံးပြုနိုင်ပါပြီ။ (ဇာတ်ကားထည့်ရန် /admin ရိုက်ပါ)")
    else:
        await update.message.reply_text("⛔ သင် Admin မဟုတ်ပါ။")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("setting", admin_cmd))
    
    print("Bot is starting correctly...")
    app.run_polling()

if __name__ == '__main__':
    main()
