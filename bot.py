import os
import sqlite3
import csv
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters, ConversationHandler
)

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8493660753:AAGW63blwBFI6xQVTh_73gHiuOrpvpB9ajA")
ADMIN_IDS = [8466996343]  # သင်ပေးထားတဲ့ Admin ID

# Conversation States
ADD_CAT, ADD_POSTER, ADD_NAME, ADD_EPISODES = range(4)
EDIT_SELECT, EDIT_ACTION = range(4, 6)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('movie_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movies 
                 (id INTEGER PRIMARY KEY, category TEXT, poster TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS episodes 
                 (id INTEGER PRIMARY KEY, movie_id INTEGER, ep_num INTEGER, link TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats 
                 (user_id INTEGER, movie_id INTEGER, timestamp DATETIME)''')
    conn.commit()
    conn.close()

CATEGORIES = {
    "1": "1️⃣ အက်ရှင် (Action) 💥", "2": "2️⃣ အချစ်ဇာတ်လမ်း (Romance) 💖",
    "3": "3️⃣ ဟာသ (Comedy) 😂", "4": "4️⃣ သရဲ/ထိတ်လန့် (Horror) 👻",
    "5": "5️⃣ သိပ္ပံနှင့်အာကာသ (Sci-Fi) 👽", "6": "6️⃣ ဒရာမာ (Drama) 🎭",
    "7": "7️⃣ သည်းထိတ်ရင်ဖို (Thriller) 🔪", "8": "8️⃣ ကာတွန်း (Animation) 🎬",
    "9": "9️⃣ နန်းတွင်းဇာတ်လမ်း 🏯", "10": "🔟 အိမ်ထောင်ရေးဇာတ်လမ်း 🏠"
}

# --- MEMBER FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=f"cat_{kid}")] for kid, name in CATEGORIES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🎬 Movie Bot မှ ကြိုဆိုပါတယ်!\n\nCategory ကိုရွေးပါ 👇"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def show_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    cat_id = query.data.split("_")[1]
    cat_name = CATEGORIES[cat_id]
    
    conn = sqlite3.connect('movie_bot.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM movies WHERE category=?", (cat_name,))
    movies = c.fetchall()
    conn.close()

    keyboard = [[InlineKeyboardButton(f"🎬 {m[1]}", callback_data=f"mov_{m[0]}")] for m in movies]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_home")])
    
    await query.edit_message_text(f"📂 {cat_name}\n\nဇာတ်လမ်းများ 👇", reply_markup=InlineKeyboardMarkup(keyboard))

async def movie_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    movie_id = query.data.split("_")[1]
    
    conn = sqlite3.connect('movie_bot.db')
    c = conn.cursor()
    c.execute("SELECT category, poster, name FROM movies WHERE id=?", (movie_id,))
    movie = c.fetchone()
    c.execute("SELECT ep_num FROM episodes WHERE movie_id=? ORDER BY ep_num", (movie_id,))
    eps = c.fetchall()
    
    # Stats Logging
    c.execute("INSERT INTO stats VALUES (?, ?, ?)", (query.from_user.id, movie_id, datetime.now()))
    conn.commit()
    conn.close()

    keyboard = []
    row = []
    for ep in eps:
        row.append(InlineKeyboardButton(f"Ep-{ep[0]}", callback_data=f"viewep_{movie_id}_{ep[0]}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_home")])

    await query.message.delete()
    await query.message.reply_photo(
        photo=movie[1],
        caption=f"🎬 **Name:** {movie[2]}\n📂 **Category:** {movie[0]}\n\nအပိုင်းများကို ရွေးပါ 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def view_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, mid, ep_num = query.data.split("_")
    conn = sqlite3.connect('movie_bot.db')
    c = conn.cursor()
    c.execute("SELECT link FROM episodes WHERE movie_id=? AND ep_num=?", (mid, ep_num))
    link = c.fetchone()[0]
    conn.close()
    await query.message.reply_text(f"📺 Episode {ep_num} Link:\n{link}")
    await query.answer()

# --- ADMIN: ADD MOVIE ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    keyboard = [[InlineKeyboardButton(v, callback_data=f"ac_{v}")] for v in CATEGORIES.values()]
    await update.message.reply_text("➕ Category ကိုရွေးပါ:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CAT

async def add_cat_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['cat'] = query.data.split("_")[1]
    await query.edit_message_text("🖼️ Poster Link (URL) ကိုပို့ပါ:")
    return ADD_POSTER

async def add_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['poster'] = update.message.text
    await update.message.reply_text("📝 ဇာတ်လမ်းအမည် ပို့ပါ:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    context.user_data['eps'] = []
    await update.message.reply_text("🔗 Episode links ကို တစ်ခုချင်းပို့ပါ (ပြီးရင် /done နှိပ်ပါ):")
    return ADD_EPISODES

async def add_ep_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['eps'].append(update.message.text)
    await update.message.reply_text(f"✅ Episode {len(context.user_data['eps'])} ရပါပြီ။ /done နှိပ်နိုင်ပါပြီ။")
    return ADD_EPISODES

async def done_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    conn = sqlite3.connect('movie_bot.db')
    c = conn.cursor()
    c.execute("INSERT INTO movies (category, poster, name) VALUES (?,?,?)", (d['cat'], d['poster'], d['name']))
    mid = c.lastrowid
    for i, link in enumerate(d['eps'], 1):
        c.execute("INSERT INTO episodes (movie_id, ep_num, link) VALUES (?,?,?)", (mid, i, link))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🎉 '{d['name']}' ထည့်သွင်းပြီးပါပြီ!")
    return ConversationHandler.END

# --- ADMIN: STATS & COMMANDS ---

async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    cmd = update.message.text
    conn = sqlite3.connect('movie_bot.db')
    c = conn.cursor()
    
    if "day" in cmd:
        day = datetime.now().strftime('%Y-%m-%d')
        c.execute("SELECT COUNT(*) FROM stats WHERE timestamp LIKE ?", (f"{day}%",))
        await update.message.reply_text(f"📊 ယနေ့ကြည့်ရှုမှု: {c.fetchone()[0]} ကြိမ်")
    elif "top" in cmd:
        c.execute("SELECT m.name, COUNT(s.movie_id) as count FROM stats s JOIN movies m ON s.movie_id = m.id GROUP BY s.movie_id ORDER BY count DESC LIMIT 1")
        res = c.fetchone()
        await update.message.reply_text(f"🔝 အကြည့်အများဆုံး: {res[0]} ({res[1]} ကြိမ်)" if res else "ဒေတာမရှိသေးပါ။")
    
    conn.close()

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect('movie_bot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM stats")
    with open('history.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['User ID', 'Movie ID', 'Time'])
        writer.writerows(c.fetchall())
    conn.close()
    await update.message.reply_document(document=open('history.csv', 'rb'))

# --- MAIN ---
if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_panel)],
        states={
            ADD_CAT: [CallbackQueryHandler(add_cat_cb, pattern="^ac_")],
            ADD_POSTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_poster)],
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_EPISODES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ep_link)],
        },
        fallbacks=[CommandHandler('done', done_save)]
    )

    app.add_handler(add_conv)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler(['stats_day', 'top'], get_stats))
    app.add_handler(CommandHandler('export', export_data))
    app.add_handler(CallbackQueryHandler(start, pattern="back_home"))
    app.add_handler(CallbackQueryHandler(show_movies, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(movie_detail, pattern="^mov_"))
    app.add_handler(CallbackQueryHandler(view_episode, pattern="^viewep_"))

    print("Bot is running...")
    app.run_polling()
