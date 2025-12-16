import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "8210400472:AAGsYRGnoyVCJH1gBw32mF2QpFZ84it-Ick"
ADMIN_IDS = [8466996343]   # 🔴 မင်း Telegram ID ထည့်

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================= DATA =================

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
    "😂 ဟာသဇတ်လမ်း"
]

MOVIES = {}   # {category: [{poster, title, links[]}]}

# ================= STATES =================

class AdminAdd(StatesGroup):
    poster = State()
    title = State()
    episodes = State()

# ================= USER =================

@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(CATEGORIES):
        kb.insert(
            InlineKeyboardButton(
                f"{i+1}. {c}",
                callback_data=f"user_cat_{i}"
            )
        )
    await m.answer("🎬 ဇတ်လမ်းအမျိုးအစားရွေးပါ", reply_markup=kb)

# ================= ADMIN =================

@dp.message_handler(commands=["admin"])
async def admin(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return

    kb = InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(CATEGORIES):
        kb.insert(
            InlineKeyboardButton(
                f"{i+1}. {c}",
                callback_data=f"admin_cat_{i}"
            )
        )
    await m.answer("⚙️ Category ရွေးပါ", reply_markup=kb)

# ---------- Admin choose category ----------

@dp.callback_query_handler(lambda c: c.data.startswith("admin_cat_"))
async def admin_choose_category(c: types.CallbackQuery, state: FSMContext):
    if c.from_user.id not in ADMIN_IDS:
        return

    idx = int(c.data.split("_")[-1])
    category = CATEGORIES[idx]

    await state.update_data(category=category)
    await c.message.answer(f"📸 {category}\n\nPoster ပုံကို ပို့ပါ")
    await AdminAdd.poster.set()
    await c.answer()

# ---------- Receive poster ----------

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AdminAdd.poster)
async def get_poster(m: types.Message, state: FSMContext):
    await state.update_data(poster=m.photo[-1].file_id)
    await m.answer("📝 ဇတ်လမ်းနာမည် ပို့ပါ")
    await AdminAdd.title.set()

# ---------- Receive title ----------

@dp.message_handler(state=AdminAdd.title)
async def get_title(m: types.Message, state: FSMContext):
    await state.update_data(title=m.text, links=[])
    await m.answer(
        "🔗 Episode link တွေ ပို့ပါ\n"
        "တစ်ကြောင်း = တစ်အပိုင်း\n"
        "/done နဲ့ပြီးပါ"
    )
    await AdminAdd.episodes.set()

# ---------- Receive episode links ----------

@dp.message_handler(state=AdminAdd.episodes)
async def get_links(m: types.Message, state: FSMContext):
    if m.text == "/done":
        data = await state.get_data()
        cat = data["category"]

        MOVIES.setdefault(cat, []).append({
            "poster": data["poster"],
            "title": data["title"],
            "links": data["links"]
        })

        await m.answer("✅ ဇတ်လမ်း သိမ်းပြီးပါပြီ")
        await state.finish()
        return

    data = await state.get_data()
    data["links"].append(m.text)
    await state.update_data(links=data["links"])
    await m.answer(f"➕ Episode {len(data['links'])} ထည့်ပြီး")

# ================= USER FLOW =================

@dp.callback_query_handler(lambda c: c.data.startswith("user_cat_"))
async def user_category(c: types.CallbackQuery):
    idx = int(c.data.split("_")[-1])
    category = CATEGORIES[idx]

    if category not in MOVIES:
        await c.answer("ဇတ်လမ်း မရှိသေးပါ", show_alert=True)
        return

    kb = InlineKeyboardMarkup(row_width=2)
    for i, m in enumerate(MOVIES[category]):
        kb.insert(
            InlineKeyboardButton(
                m["title"],
                callback_data=f"movie_{idx}_{i}"
            )
        )

    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="back_home"))
    await c.message.answer(category, reply_markup=kb)
    await c.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("movie_"))
async def show_episodes(c: types.CallbackQuery):
    _, cat_i, mov_i = c.data.split("_")
    movie = MOVIES[CATEGORIES[int(cat_i)]][int(mov_i)]

    kb = InlineKeyboardMarkup(row_width=5)
    for i, link in enumerate(movie["links"]):
        kb.insert(
            InlineKeyboardButton(
                f"အပိုင်း ({i+1})",
                url=link
            )
        )

    kb.add(InlineKeyboardButton("⬅️ Back", callback_data=f"user_cat_{cat_i}"))

    await bot.send_photo(
        c.message.chat.id,
        movie["poster"],
        caption=movie["title"],
        reply_markup=kb
    )
    await c.answer()

@dp.callback_query_handler(lambda c: c.data == "back_home")
async def back_home(c: types.CallbackQuery):
    await start(c.message)
    await c.answer()

# ================= RUN =================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

today = datetime.now().date().isoformat()
week = datetime.now().strftime("%Y-W%U")

movie_views[movie_name] = movie_views.get(movie_name, 0) + 1
daily_views[today] = daily_views.get(today, 0) + 1
weekly_views[week] = weekly_views.get(week, 0) + 1

@dp.message_handler(commands=["view"])
async def view_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    text = "📊 VIEW STATS\n\n"

    # 🔥 Top Movies
    text += "🏆 Top Movies:\n"
    for name, count in sorted(movie_views.items(), key=lambda x: x[1], reverse=True)[:5]:
        text += f"• {name} — {count} views\n"

    # 📅 Today
    today = datetime.now().date().isoformat()
    text += f"\n📆 Today ({today}): {daily_views.get(today, 0)} views\n"

    # 📅 This week
    week = datetime.now().strftime("%Y-W%U")
    text += f"🗓 This Week ({week}): {weekly_views.get(week, 0)} views\n"

    await message.reply(text)

