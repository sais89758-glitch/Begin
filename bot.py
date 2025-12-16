import os
import sqlite3
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [123456789]  # 🔴 မင်း Telegram ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================= DATABASE =================
db = sqlite3.connect("movies.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    name TEXT,
    poster TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER,
    ep_no INTEGER,
    link TEXT,
    views INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS history (
    user_id INTEGER,
    movie TEXT,
    episode INTEGER,
    time TEXT
)
""")

db.commit()

# ================= DATA ====================
CATEGORIES = [
    "❤️ အချစ်ဇတ်လမ်း",
    "💍 အိမ်ထောင်ရေးဇတ်လမ်း",
    "⚔️ စစ်ဇတ်လမ်း",
    "🏯 နန်းတွင်းဇတ်လမ်း",
    "🔪 အက်ရှင်ဇတ်လမ်း",
    "🔥 အကြမ်းဖက်ဇတ်လမ်း",
    "👻 သရဲဇတ်လမ်း",
    "🕵️ စုံထောက်ဇတ်လမ်း",
    "👨‍👩‍👧 မိသားစုဇတ်လမ်း",
    "😂 ဟာသဇတ်လမ်း",
]

# ================= FSM =====================
class AdminAdd(StatesGroup):
    category = State()
    poster = State()
    name = State()
    episodes = State()

# ================= KEYBOARDS ===============
def category_kb(prefix):
    kb = InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(CATEGORIES):
        kb.insert(InlineKeyboardButton(f"{i+1}. {c}", callback_data=f"{prefix}_{i}"))
    return kb

# ================= MEMBER ==================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("🎬 ရုပ်ရှင်အမျိုးအစားရွေးပါ", reply_markup=category_kb("user_cat"))

@dp.callback_query_handler(lambda c: c.data.startswith("user_cat_"))
async def user_category(call: types.CallbackQuery):
    idx = int(call.data.split("_")[-1])
    cat = CATEGORIES[idx]

    cur.execute("SELECT id,name FROM movies WHERE category=?", (cat,))
    movies = cur.fetchall()

    if not movies:
        await call.answer("ဇတ်လမ်းမရှိသေးပါ")
        return

    kb = InlineKeyboardMarkup(row_width=2)
    for m in movies:
        kb.insert(InlineKeyboardButton(m[1], callback_data=f"user_movie_{m[0]}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_start"))

    await call.message.answer("🎬 ဇတ်လမ်းရွေးပါ", reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "back_start")
async def back_start(call: types.CallbackQuery):
    await start(call.message)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("user_movie_"))
async def user_movie(call: types.CallbackQuery):
    movie_id = int(call.data.split("_")[-1])

    cur.execute("SELECT name,poster FROM movies WHERE id=?", (movie_id,))
    name, poster = cur.fetchone()

    cur.execute("SELECT ep_no,views,link FROM episodes WHERE movie_id=?", (movie_id,))
    eps = cur.fetchall()

    kb = InlineKeyboardMarkup(row_width=3)
    for ep in eps:
        kb.insert(
            InlineKeyboardButton(
                f"EP {ep[0]} 👁{ep[1]}",
                callback_data=f"watch_{movie_id}_{ep[0]}"
            )
        )
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_start"))

    await call.message.answer_photo(poster, caption=name, reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("watch_"))
async def watch_episode(call: types.CallbackQuery):
    _, movie_id, ep_no = call.data.split("_")
    movie_id = int(movie_id)
    ep_no = int(ep_no)

    cur.execute("SELECT link FROM episodes WHERE movie_id=? AND ep_no=?", (movie_id, ep_no))
    link = cur.fetchone()[0]

    cur.execute("UPDATE episodes SET views = views + 1 WHERE movie_id=? AND ep_no=?", (movie_id, ep_no))
    db.commit()

    cur.execute("SELECT name FROM movies WHERE id=?", (movie_id,))
    movie_name = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO history VALUES (?,?,?,?)",
        (call.from_user.id, movie_name, ep_no, datetime.now().isoformat())
    )
    db.commit()

    await call.answer("🎬 Playing...")
    await call.message.answer(link)

# ================= ADMIN ===================
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer("⚙️ Category ရွေးပါ", reply_markup=category_kb("admin_cat"))

@dp.callback_query_handler(lambda c: c.data.startswith("admin_cat_"))
async def admin_cat(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        return
    idx = int(call.data.split("_")[-1])
    await state.update_data(category=CATEGORIES[idx])
    await call.message.answer("📸 Poster ပုံပို့ပါ")
    await AdminAdd.poster.set()
    await call.answer()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AdminAdd.poster)
async def admin_poster(msg: types.Message, state: FSMContext):
    await state.update_data(poster=msg.photo[-1].file_id)
    await msg.answer("🎬 ဇတ်လမ်းနာမည်ပို့ပါ")
    await AdminAdd.name.set()

@dp.message_handler(state=AdminAdd.name)
async def admin_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text, episodes=[])
    await msg.answer("🔗 Episode link တစ်ခုချင်းပို့ပါ\nပြီးရင် /done")
    await AdminAdd.episodes.set()

@dp.message_handler(state=AdminAdd.episodes)
async def admin_episode(msg: types.Message, state: FSMContext):
    data = await state.get_data()

    if msg.text == "/done":
        cur.execute(
            "INSERT INTO movies (category,name,poster) VALUES (?,?,?)",
            (data["category"], data["name"], data["poster"])
        )
        movie_id = cur.lastrowid

        for i, link in enumerate(data["episodes"], start=1):
            cur.execute(
                "INSERT INTO episodes (movie_id,ep_no,link) VALUES (?,?,?)",
                (movie_id, i, link)
            )
        db.commit()

        await msg.answer("✅ ဇတ်လမ်းသိမ်းပြီးပါပြီ")
        await state.finish()
        return

    if len(data["episodes"]) >= 10:
        await msg.answer("❌ Episode ၁၀ ခုအထိပဲရပါတယ်\n/done")
        return

    data["episodes"].append(msg.text)
    await state.update_data(episodes=data["episodes"])
    await msg.answer(f"✔ Episode {len(data['episodes'])} ထည့်ပြီး")

# ================= RUN =====================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

# ================= ADMIN REPORT =================

@dp.message_handler(commands=["history"])
async def admin_history(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return

    cur.execute("""
        SELECT user_id, movie, episode, time
        FROM history
        ORDER BY time DESC
        LIMIT 20
    """)
    rows = cur.fetchall()

    if not rows:
        await msg.answer("📭 History မရှိသေးပါ")
        return

    text = "📊 နောက်ဆုံးကြည့်ထားသော History\n\n"
    for r in rows:
        text += (
            f"👤 User: {r[0]}\n"
            f"🎬 Movie: {r[1]}\n"
            f"▶ Episode: {r[2]}\n"
            f"⏰ {r[3]}\n\n"
        )

    await msg.answer(text)


@dp.message_handler(commands=["top"])
async def admin_top(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return

    cur.execute("""
        SELECT movies.name, episodes.ep_no, episodes.views
        FROM episodes
        JOIN movies ON episodes.movie_id = movies.id
        ORDER BY episodes.views DESC
        LIMIT 5
    """)
    rows = cur.fetchall()

    if not rows:
        await msg.answer("📉 Data မရှိသေးပါ")
        return

    text = "🔥 View အများဆုံး Episodes\n\n"
    for i, r in enumerate(rows, start=1):
        text += f"{i}. 🎬 {r[0]} | EP {r[1]} | 👁 {r[2]}\n"

    await msg.answer(text)


@dp.message_handler(commands=["export"])
async def admin_export(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return

    import csv

    filename = "history.csv"
    cur.execute("SELECT * FROM history")
    rows = cur.fetchall()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "movie", "episode", "time"])
        writer.writerows(rows)

    await msg.answer_document(open(filename, "rb"))
