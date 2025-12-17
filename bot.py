import logging
import json
import sqlite3
import os
import uuid
import asyncio
from datetime import datetime, timedelta

# Import telegram library correctly
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        ConversationHandler,
        filters,
    )
except ImportError:
    print("Error: 'python-telegram-bot' library not found. Please check requirements.txt")

# --- CONFIGURATION ---
TOKEN = '8210400472:AAGsYRGnoyVCJH1gBw32mF2QpFZ84it-Ick' 
ADMIN_ID = 8466996343 

DATA_FILE = 'movies_data.json'
DB_FILE = 'bot_stats.db'

(CHOOSING_CATEGORY, SENDING_POSTER, SENDING_NAME, SENDING_EPISODES) = range(4)

CATEGORIES = [
    "1️⃣ အက်ရှင် (Action) 💥", "2️⃣ အချစ်ဇာတ်လမ်း (Romance) 💖", 
    "3️⃣ ဟာသ (Comedy) 😂", "4️⃣ သရဲ/ထိတ်လန့် (Horror) 👻",
    "5️⃣ သိပ္ပံနှင့်အာကာသ (Sci-Fi) 👽", "6️⃣ ဒရာမာ (Drama) 🎭", 
    "7️⃣ သည်းထိတ်ရင်ဖို (Thriller) 🔪", "8️⃣ ကာတွန်း (Animation) 🎬",
    "9️⃣ မှတ်တမ်းတင် (Documentary) 🌍", "🔟 ဇာတ်လမ်းတွဲများ (Series) 📺"
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {cat: [] for cat in CATEGORIES}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {cat: [] for cat in CATEGORIES}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stats (user_id INTEGER, action TEXT, details TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for cat in CATEGORIES:
        row.append(InlineKeyboardButton(cat, callback_data=f"view_cat|{cat}"))
        if len(row) == 2:
            keyboard.append(row); row = []
    if row: keyboard.append(row)
    await update.message.reply_text("👋 မင်္ဂလာပါ! အမျိုးအစားရွေးချယ်ပါ။", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ သင် Admin မဟုတ်ပါ။")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"admin_cat|{cat}")] for cat in CATEGORIES]
    await update.message.reply_text("🛠 Admin Mode: Category ရွေးပါ။", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_CATEGORY

async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    all_data = load_data()

    if data[0] == "view_cat":
        movies = all_data.get(data[1], [])
        btn = [[InlineKeyboardButton(m['name'], callback_data=f"view_story|{data[1]}|{m['id']}")] for m in movies]
        btn.append([InlineKeyboardButton("⬅️ Back", callback_data="back_home")])
        await query.edit_message_text(f"📂 {data[1]}", reply_markup=InlineKeyboardMarkup(btn))
    
    elif data[0] == "back_home":
        await query.delete_message()
        await start(update, context)

# --- MAIN ---
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    # Simple navigation
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_start))
    app.add_handler(CallbackQueryHandler(handle_navigation))
    
    print("Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
