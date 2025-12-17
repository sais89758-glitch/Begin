import logging
import json
import sqlite3
import os
import uuid
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from collections import Counter

# -----------------------------------------------------------------------------
# CONFIGURATION (ဒီနေရာမှာ ပြင်ပါ)
# -----------------------------------------------------------------------------
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'  # BotFather ဆီက Token ထည့်ပါ
ADMIN_ID = 123456789                    # admin ရဲ့ User ID (Integer) ကိုထည့်ပါ

# Data Files
DATA_FILE = 'movies_data.json'
DB_FILE = 'bot_stats.db'

# Conversation States
(
    CHOOSING_CATEGORY,
    SENDING_POSTER,
    SENDING_NAME,
    SENDING_EPISODES,
) = range(4)

# Categories (10 Types)
CATEGORIES = [
    "1️⃣ Action 💥", "2️⃣ Romance 💖", "3️⃣ Comedy 😂", "4️⃣ Horror 👻",
    "5️⃣ Sci-Fi 👽", "6️⃣ Drama 🎭", "7️⃣ Thriller 🔪", "8️⃣ Animation 🎬",
    "9️⃣ Documentary 🌍", "🔟 Series 📺"
]

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# DATA MANAGEMENT (JSON & SQLite)
# -----------------------------------------------------------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {cat: [] for cat in CATEGORIES}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Ensure all categories exist
        for cat in CATEGORIES:
            if cat not in data:
                data[cat] = []
        return data

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stats
                 (user_id INTEGER, action TEXT, details TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

def log_stat(user_id, action, details=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO stats VALUES (?, ?, ?, ?)", 
              (user_id, action, details, datetime.now()))
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# ADMIN HANDLERS (Add Content)
# -----------------------------------------------------------------------------

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ သင် Admin မဟုတ်ပါ။")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(cat, callback_data=f"admin_cat|{cat}")] for cat in CATEGORIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 **Admin Mode**\nဇာတ်လမ်းထည့်ရန် Category ရွေးပါ:", parse_mode='Markdown', reply_markup=reply_markup)
    return CHOOSING_CATEGORY

async def admin_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split("|")[1]
    context.user_data['new_movie'] = {'category': category, 'episodes': []}
    
    await query.edit_message_text(f"📂 Category: {category}\n\n🖼️ ကျေးဇူးပြု၍ **Poster** ပုံကို ပို့ပေးပါ။")
    return SENDING_POSTER

async def receive_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ ပုံ (Photo) သာ ပို့ပေးပါ။")
        return SENDING_POSTER
    
    photo_id = update.message.photo[-1].file_id
    context.user_data['new_movie']['poster'] = photo_id
    
    await update.message.reply_text("✅ Poster ရပါပြီ။\n\n📝 **ဇာတ်လမ်းနာမည် (Story Name)** ကို ရေးပို့ပါ။")
    return SENDING_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data['new_movie']['name'] = name
    context.user_data['new_movie']['id'] = str(uuid.uuid4())[:8] # Short ID
    
    await update.message.reply_text(
        f"✅ နာမည်: {name}\n\n🔗 **Episode 1 Link** ကို ပို့ပေးပါ။\n(နောက်အပိုင်းများကို တစ်ခုချင်းစီ ဆက်တိုက်ပို့နိုင်ပါသည်။ ပြီးရင် /done နှိပ်ပါ)"
    )
    return SENDING_EPISODES

async def receive_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    # Simple check if text looks like a link or file ID
    ep_count = len(context.user_data['new_movie']['episodes']) + 1
    context.user_data['new_movie']['episodes'].append(link)
    
    await update.message.reply_text(
        f"✅ Episode {ep_count} ထည့်ပြီး။\n\n🔗 နောက်ထပ် Link ပို့ပါ သို့မဟုတ် ပြီးဆုံးရန် /done ကိုနှိပ်ပါ။"
    )
    return SENDING_EPISODES

async def finish_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_data = context.user_data.get('new_movie')
    if not movie_data:
        await update.message.reply_text("❌ Error ဖြစ်သွားသည်။")
        return ConversationHandler.END
    
    # Save to JSON
    all_data = load_data()
    cat = movie_data['category']
    
    new_entry = {
        'id': movie_data['id'],
        'name': movie_data['name'],
        'poster': movie_data['poster'],
        'episodes': movie_data['episodes']
    }
    
    all_data[cat].append(new_entry)
    save_data(all_data)
    
    await update.message.reply_text(f"🎉 **{movie_data['name']}** ကို အောင်မြင်စွာ သိမ်းဆည်းလိုက်ပါပြီ။", parse_mode='Markdown')
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Process ကို ဖျက်လိုက်ပါပြီ။")
    context.user_data.clear()
    return ConversationHandler.END

# -----------------------------------------------------------------------------
# ADMIN STATS & SETTINGS HANDLERS
# -----------------------------------------------------------------------------

def check_admin(func):
    async def wrapper(update, context, *args, **kwargs):
        if update.effective_user.id != ADMIN_ID:
            return # Ignore non-admins
        return await func(update, context, *args, **kwargs)
    return wrapper

@check_admin
async def stats_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    yesterday = datetime.now() - timedelta(days=1)
    c.execute("SELECT COUNT(*) FROM stats WHERE timestamp > ?", (yesterday,))
    count = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📊 **24 နာရီအတွင်း အသုံးပြုသူ:** {count} ဦး", parse_mode='Markdown')

@check_admin
async def stats_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    week_ago = datetime.now() - timedelta(weeks=1)
    c.execute("SELECT COUNT(*) FROM stats WHERE timestamp > ?", (week_ago,))
    count = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📊 **၁ ပတ်အတွင်း အသုံးပြုသူ:** {count} ဦး", parse_mode='Markdown')

@check_admin
async def stats_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Count clicks on stories
    c.execute("SELECT details, COUNT(*) as cnt FROM stats WHERE action='view_story' GROUP BY details ORDER BY cnt DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    
    msg = "🏆 **လူကြည့်အများဆုံး ဇာတ်ကားများ**\n\n"
    for idx, (name, count) in enumerate(rows, 1):
        msg += f"{idx}. {name} - {count} views\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

@check_admin
async def history_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM stats ORDER BY timestamp DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    msg = "📜 **နောက်ဆုံး Activity ၂၀**\n\n"
    for row in rows:
        msg += f"👤 {row[0]} | {row[1]} | {row[2]}\n"
    await update.message.reply_text(msg)

@check_admin
async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_document(document=open(DATA_FILE, 'rb'), caption="📂 Movies Data JSON")
    await update.message.reply_document(document=open(DB_FILE, 'rb'), caption="📊 Stats Database")

@check_admin
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Show categories to edit
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"set_cat|{cat}")] for cat in CATEGORIES]
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_setting")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ **Settings / Edit Mode**\nပြုပြင်လိုသော Category ရွေးပါ:", parse_mode='Markdown', reply_markup=reply_markup)

# -----------------------------------------------------------------------------
# MEMBER HANDLERS (Browsing)
# -----------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_stat(user.id, "start")
    
    keyboard = []
    # Create 2 columns for categories
    row = []
    for cat in CATEGORIES:
        row.append(InlineKeyboardButton(cat, callback_data=f"view_cat|{cat}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 မင်္ဂလာပါ! **Movie Channel Bot** မှ ကြိုဆိုပါတယ်။\nကြည့်ရှုလိုသော အမျိုးအစားကို ရွေးချယ်ပါ။ 👇",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    action = data[0]
    
    user_id = update.effective_user.id
    all_data = load_data()

    # --- VIEW CATEGORY ---
    if action == "view_cat":
        cat_name = data[1]
        movies = all_data.get(cat_name, [])
        
        keyboard = []
        for movie in movies:
            keyboard.append([InlineKeyboardButton(f"🎬 {movie['name']}", callback_data=f"view_story|{cat_name}|{movie['id']}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_home")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Text based list instead of poster for category view to save bandwidth
        await query.edit_message_text(
            f"📂 **{cat_name}**\nဇာတ်ကားရွေးချယ်ပါ:", 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )

    # --- VIEW STORY (Shows Poster + Episodes) ---
    elif action == "view_story":
        cat_name = data[1]
        movie_id = data[2]
        movie = next((m for m in all_data[cat_name] if m['id'] == movie_id), None)
        
        if movie:
            log_stat(user_id, "view_story", movie['name'])
            
            # Episode Grid (5 per row)
            ep_keyboard = []
            row = []
            for i, link in enumerate(movie['episodes']):
                row.append(InlineKeyboardButton(f"Ep {i+1}", callback_data=f"get_ep|{cat_name}|{movie_id}|{i}"))
                if len(row) == 5:
                    ep_keyboard.append(row)
                    row = []
            if row: ep_keyboard.append(row)
            
            ep_keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"view_cat|{cat_name}")])
            
            # Delete previous text message to send new photo message
            await query.delete_message()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=movie['poster'],
                caption=f"🎬 **{movie['name']}**\n\nကြည့်ရှုလိုသော အပိုင်းကို ရွေးပါ:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(ep_keyboard),
                protect_content=True # Prevent downloading poster
            )

    # --- GET EPISODE LINK ---
    elif action == "get_ep":
        cat_name = data[1]
        movie_id = data[2]
        ep_index = int(data[3])
        
        movie = next((m for m in all_data[cat_name] if m['id'] == movie_id), None)
        if movie:
            link = movie['episodes'][ep_index]
            log_stat(user_id, "click_ep", f"{movie['name']} - Ep {ep_index+1}")
            
            # Check if link is a URL or a Telegram Message Link
            keyboard = [[InlineKeyboardButton("▶️ Watch Now / Download", url=link)]]
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"view_story_text|{cat_name}|{movie['id']}")]) # Special back to avoid resending photo
            
            await query.edit_message_caption(
                caption=f"🎬 **{movie['name']}** - Episode {ep_index+1}\n\n👇 အောက်ပါခလုတ်ကို နှိပ်ပြီး ကြည့်ရှုပါ။",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    # --- BACK TO HOME ---
    elif action == "back_home":
        await start(update, context)

    # --- SPECIAL BACK HANDLER (From Episode to Story) ---
    elif action == "view_story_text":
        # Just restore the episode grid caption
        cat_name = data[1]
        movie_id = data[2]
        movie = next((m for m in all_data[cat_name] if m['id'] == movie_id), None)
        
        ep_keyboard = []
        row = []
        for i, link in enumerate(movie['episodes']):
            row.append(InlineKeyboardButton(f"Ep {i+1}", callback_data=f"get_ep|{cat_name}|{movie_id}|{i}"))
            if len(row) == 5:
                ep_keyboard.append(row)
                row = []
        if row: ep_keyboard.append(row)
        ep_keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"view_cat|{cat_name}")])
        
        await query.edit_message_caption(
            caption=f"🎬 **{movie['name']}**\n\nကြည့်ရှုလိုသော အပိုင်းကို ရွေးပါ:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(ep_keyboard)
        )

    # -------------------------------------------------------------------------
    # SETTINGS CALLBACKS (DELETE/EDIT)
    # -------------------------------------------------------------------------
    elif action == "set_cat":
        if user_id != ADMIN_ID: return
        cat_name = data[1]
        movies = all_data.get(cat_name, [])
        
        keyboard = []
        for movie in movies:
            keyboard.append([InlineKeyboardButton(f"🗑️ {movie['name']}", callback_data=f"del_confirm|{cat_name}|{movie['id']}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_setting")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(f"⚙️ **{cat_name}**\nဖျက်လိုသော ဇာတ်ကားကို နှိပ်ပါ:", parse_mode='Markdown', reply_markup=reply_markup)

    elif action == "del_confirm":
        cat_name = data[1]
        movie_id = data[2]
        
        # Delete Logic
        movies = all_data.get(cat_name, [])
        new_movies = [m for m in movies if m['id'] != movie_id]
        all_data[cat_name] = new_movies
        save_data(all_data)
        
        await query.answer("🗑️ ဖျက်ပြီးပါပြီ!", show_alert=True)
        # Refresh list
        keyboard = []
        for movie in new_movies:
            keyboard.append([InlineKeyboardButton(f"🗑️ {movie['name']}", callback_data=f"del_confirm|{cat_name}|{movie['id']}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_setting")])
        
        await query.edit_message_text(f"⚙️ **{cat_name}**\nUpdate ဖြစ်ပြီးပါပြီ။", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == "back_setting":
        await settings_command(update, context)
        
    elif action == "close_setting":
        await query.delete_message()

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

def main():
    # Initialize DB
    init_db()
    
    # Create App
    application = Application.builder().token(TOKEN).build()

    # --- ADMIN CONVERSATION (Add Movie) ---
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_start)],
        states={
            CHOOSING_CATEGORY: [CallbackQueryHandler(admin_choice, pattern='^admin_cat\|')],
            SENDING_POSTER: [MessageHandler(filters.PHOTO, receive_poster)],
            SENDING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            SENDING_EPISODES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_episodes),
                CommandHandler('done', finish_add)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)

    # --- ADMIN COMMANDS ---
    application.add_handler(CommandHandler("stats_day", stats_day))
    application.add_handler(CommandHandler("stats_week", stats_week))
    application.add_handler(CommandHandler("top", stats_top))
    application.add_handler(CommandHandler("history_all", history_all))
    application.add_handler(CommandHandler("export", export_data))
    application.add_handler(CommandHandler("setting", settings_command))

    # --- MEMBER COMMANDS ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_navigation))

    # Run Bot
    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
