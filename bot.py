import logging
import json
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ================= CONFIG =================
API_TOKEN = "8210400472:AAGsYRGnoyVCJH1gBw32mF2QpFZ84it-Ick"
ADMIN_IDS = [8466996343]  # ← သင့် Telegram ID
MOVIE_JSON = "movies.json"
STATS_DB = "stats.db"
# =========================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================= CATEGORY =================
CATEGORIES = {
    "1": "❤️ အချစ်ဇတ်လမ်း",
    "2": "💍 အိမ်ထောင်ရေးဇတ်လမ်း",
    "3": "⚔️ စစ်ဇတ်လမ်း",
    "4": "🏯 နန်းတွင်းဇတ်လမ်း",
    "5": "🔪 အက်ရှင်ဇတ်လမ်း",
    "6": "🔥 အကြမ်းဖက်ဇတ်လမ်း",
    "7": "👻 သရဲဇတ်လမ်း",
    "8": "🕵️ စုံထောက်ဇတ်လမ်း",
    "9": "👨‍👩‍👧 မိသားစုဇတ်လမ်း",
    "10": "😂 ဟာသဇတ်လမ်း"
}

# ================= FILE INIT =================
try:
    with open(MOVIE_JSON, "r", encoding="utf-8") as f:
        movies = json.load(f)
except:
    movies = {}

conn = sqlite3.connect(STATS_DB)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS views (
    user_id INTEGER,
    category TEXT,
    story TEXT,
    episode TEXT,
    date TEXT
)
""")
conn.commit()
conn.close()

# ================= STATES =================
class AddStory(StatesGroup):
    category = State()
    poster = State()
    name = State()
    episode = State()

# ================= UTIL =================
def save_movies():
    with open(MOVIE_JSON, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

def back_kb(target):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=target))
    return kb

# ================= MEMBER =================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for k, v in CATEGORIES.items():
        kb.insert(types.InlineKeyboardButton(f"{k}. {v}", callback_data=f"cat:{k}"))
    await msg.answer("🎬 ဇတ်လမ်းအမျိုးအစားရွေးပါ", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("cat:"))
async def open_category(call: types.CallbackQuery):
    cat = call.data.split(":")[1]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for story in movies.get(cat, {}):
        kb.insert(types.InlineKeyboardButton(story, callback_data=f"story:{cat}:{story}"))
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="home"))
    await call.message.answer("📽 ဇတ်လမ်းရွေးပါ", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "home")
async def back_home(call: types.CallbackQuery):
    await start(call.message)

@dp.callback_query_handler(lambda c: c.data.startswith("story:"))
async def open_story(call: types.CallbackQuery):
    _, cat, story = call.data.split(":", 2)
    data = movies[cat][story]
    kb = types.InlineKeyboardMarkup(row_width=5)
    for ep in data["episodes"]:
        kb.insert(types.InlineKeyboardButton(ep, callback_data=f"ep:{cat}:{story}:{ep}"))
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"cat:{cat}"))
    await bot.send_photo(call.message.chat.id, data["poster"], caption=story, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("ep:"))
async def open_episode(call: types.CallbackQuery):
    _, cat, story, ep = call.data.split(":", 3)
    link = movies[cat][story]["episodes"][ep]

    conn = sqlite3.connect(STATS_DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO views VALUES (?,?,?,?,?)",
                (call.from_user.id, cat, story, ep, datetime.now().date().isoformat()))
    conn.commit()
    conn.close()

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("▶️ Watch", url=link))
    kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"story:{cat}:{story}"))
    await call.message.answer(f"{story} - {ep}", reply_markup=kb)

# ================= ADMIN =================
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for k, v in CATEGORIES.items():
        kb.insert(types.InlineKeyboardButton(v, callback_data=f"addcat:{k}"))
    await msg.answer("🛠 Category ရွေးပါ", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("addcat:"))
async def add_cat(call: types.CallbackQuery, state: FSMContext):
    cat = call.data.split(":")[1]
    await state.update_data(category=cat, eps={})
    await call.message.answer("🖼 Poster ပို့ပါ")
    await AddStory.poster.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddStory.poster)
async def add_poster(msg: types.Message, state: FSMContext):
    await state.update_data(poster=msg.photo[-1].file_id)
    await msg.answer("📖 ဇတ်လမ်းနာမည် ပို့ပါ")
    await AddStory.name.set()

@dp.message_handler(state=AddStory.name)
async def add_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text, ep_i=1)
    await msg.answer("🔗 Episode 1 link ပို့ပါ")
    await AddStory.episode.set()

@dp.message_handler(state=AddStory.episode)
async def add_eps(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    i = data["ep_i"]
    data["eps"][f"အပိုင်း({i})"] = msg.text
    i += 1
    if i > 10:
        cat = data["category"]
        movies.setdefault(cat, {})
        movies[cat][data["name"]] = {
            "poster": data["poster"],
            "episodes": data["eps"]
        }
        save_movies()
        await msg.answer("✅ ဇတ်လမ်းသိမ်းပြီးပါပြီ")
        await state.finish()
    else:
        await state.update_data(ep_i=i)
        await msg.answer(f"🔗 Episode {i} link ပို့ပါ")

# ================= STATS =================
@dp.message_handler(commands=["stats_day"])
async def stats_day(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    conn = sqlite3.connect(STATS_DB)
    cur = conn.cursor()
    today = datetime.now().date().isoformat()
    cur.execute("SELECT COUNT(*) FROM views WHERE date=?", (today,))
    c = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"📊 Today Views: {c}")

@dp.message_handler(commands=["stats_week"])
async def stats_week(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    conn = sqlite3.connect(STATS_DB)
    cur = conn.cursor()
    d = (datetime.now() - timedelta(days=7)).date().isoformat()
    cur.execute("SELECT COUNT(*) FROM views WHERE date>=?", (d,))
    c = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"📊 Weekly Views: {c}")

@dp.message_handler(commands=["top"])
async def top(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    conn = sqlite3.connect(STATS_DB)
    cur = conn.cursor()
    cur.execute("SELECT story, COUNT(*) c FROM views GROUP BY story ORDER BY c DESC LIMIT 5")
    rows = cur.fetchall()
    conn.close()
    text = "\n".join([f"{r[0]} - {r[1]}" for r in rows]) or "No data"
    await msg.answer(text)

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
