import logging
import json
import os
import uuid
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

# --- CONFIG ---
# မိတ်ဆွေပေးထားသော Token အသစ်နှင့် ID
TOKEN = '8210400472:AAFapdRKx4uCa_vQFQnJvnRg8RZuOJX1wpY' 
ADMIN_ID = 8466996343 

DATA_FILE = 'movies_data.json'
(CHOOSING_CATEGORY, SENDING_POSTER, SENDING_NAME, SENDING_EPISODES) = range(4)

CATEGORIES = [
    "1️⃣ အက်ရှင် (Action) 💥", "2️⃣ အချစ်ဇာတ်လမ်း (Romance) 💖", 
    "3️⃣ ဟာသ (Comedy) 😂", "4️⃣ သရဲ/ထိတ်လန့် (Horror) 👻",
    "5️⃣ သိပ္ပံနှင့်အာကာသ (Sci-Fi) 👽", "6️⃣ ဒရာမာ (Drama) 🎭", 
    "7️⃣ သည်းထိတ်ရင်ဖို (Thriller) 🔪", "8️⃣ ကာတွန်း (Animation) 🎬",
    "9️⃣ နန်းတွင်းဇာတ်လမ်း 🏯", "🔟 အိမ်ထောင်ရေးဇာတ်လမ်း 🏠"
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {cat: [] for cat in CATEGORIES}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for cat in CATEGORIES:
                if cat not in data: data[cat] = []
            return data
    except:
        return {cat: [] for cat in CATEGORIES}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for cat in CATEGORIES:
        row.append(InlineKeyboardButton(cat, callback_data=f"view_cat|{cat}"))
        if len(row) == 2:
            keyboard.append(row); row = []
    if row: keyboard.append(row)
    await update.message.reply_text("👋 မင်္ဂလာပါ! အမျိုးအစားရွေးချယ်ပါ။", reply_markup=InlineKeyboardMarkup(keyboard))

# --- ADMIN COMMAND ---
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(f"⛔ သင် Admin မဟုတ်ပါ။ (ID: {update.effective_user.id})")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"admin_cat|{cat}")] for cat in CATEGORIES]
    await update.message.reply_text("🛠 **Admin Mode**\nဇာတ်ကားထည့်ရန် Category ကို ရွေးပါ:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_CATEGORY

async def admin_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.split("|")[1]
    context.user_data['new_movie'] = {'category': cat, 'episodes': []}
    await query.edit_message_text(f"📂 {cat}\n\n🖼️ **Poster ပုံ (Photo)** ကို ပို့ပေးပါ။")
    return SENDING_POSTER

async def receive_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ ပုံ (Photo) တစ်ပုံ ပို့ပေးပါ။")
        return SENDING_POSTER
    context.user_data['new_movie']['poster'] = update.message.photo[-1].file_id
    await update.message.reply_text("✅ ရပါပြီ။\n📝 **ဇာတ်လမ်းနာမည်** ကို ရေးပို့ပါ။")
    return SENDING_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_movie']['name'] = update.message.text
    context.user_data['new_movie']['id'] = str(uuid.uuid4())[:8]
    await update.message.reply_text("🔗 **Episode 1 Link** ကို ပို့ပေးပါ။\n(နောက်ထပ်အပိုင်းရှိလျှင် ထပ်ပို့ပါ၊ ပြီးလျှင် /done နှိပ်ပါ)")
    return SENDING_EPISODES

async def receive_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_movie']['episodes'].append(update.message.text)
    await update.message.reply_text(f"✅ Ep {len(context.user_data['new_movie']['episodes'])} ရပြီ။\nထပ်ပို့ပါ (သို့မဟုတ်) /done နှိပ်ပါ။")
    return SENDING_EPISODES

async def finish_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie = context.user_data.get('new_movie')
    all_data = load_data()
    all_data[movie['category']].append({
        'id': movie['id'], 'name': movie['name'], 'poster': movie['poster'], 'episodes': movie['episodes']
    })
    save_data(all_data)
    await update.message.reply_text(f"🎉 **{movie['name']}** ကို သိမ်းဆည်းပြီးပါပြီ။")
    context.user_data.clear()
    return ConversationHandler.END

# --- NAVIGATION ---
async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    all_data = load_data()

    if data[0] == "view_cat":
        movies = all_data.get(data[1], [])
        if not movies:
            await query.edit_message_text(f"📂 {data[1]}\n\nဇာတ်ကားမရှိသေးပါ။", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_home")]]))
            return
        btn = [[InlineKeyboardButton(f"🎬 {m['name']}", callback_data=f"view_story|{data[1]}|{m['id']}")] for m in movies]
        btn.append([InlineKeyboardButton("⬅️ Back", callback_data="back_home")])
        await query.edit_message_text(f"📂 {data[1]}", reply_markup=InlineKeyboardMarkup(btn))

    elif data[0] == "view_story":
        movie = next((m for m in all_data[data[1]] if m['id'] == data[2]), None)
        if movie:
            btn = []
            row = []
            for i in range(len(movie['episodes'])):
                row.append(InlineKeyboardButton(f"Ep {i+1}", callback_data=f"get_ep|{data[1]}|{data[2]}|{i}"))
                if len(row) == 4: btn.append(row); row = []
            if row: btn.append(row)
            btn.append([InlineKeyboardButton("⬅️ Back", callback_data=f"view_cat|{data[1]}")])
            await query.delete_message()
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=movie['poster'], caption=f"🎬 **{movie['name']}**", reply_markup=InlineKeyboardMarkup(btn))

    elif data[0] == "get_ep":
        movie = next((m for m in all_data[data[1]] if m['id'] == data[2]), None)
        link = movie['episodes'][int(data[3])]
        btn = [[InlineKeyboardButton("▶️ Watch Now", url=link)], [InlineKeyboardButton("⬅️ Back", callback_data=f"view_cat|{data[1]}")]]
        await query.edit_message_caption(caption=f"🎬 {movie['name']} - Episode {int(data[3])+1}", reply_markup=InlineKeyboardMarkup(btn))

    elif data[0] == "back_home":
        await query.delete_message(); await start(update, context)

# --- MAIN ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('admin', admin_start)],
        states={
            CHOOSING_CATEGORY: [CallbackQueryHandler(admin_choice, pattern='^admin_cat\|')],
            SENDING_POSTER: [MessageHandler(filters.PHOTO, receive_poster)],
            SENDING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            SENDING_EPISODES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_episodes), CommandHandler('done', finish_add)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    ))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_navigation))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
