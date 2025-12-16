import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [8466996343]   # မင်း Telegram ID
# ===========================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================== DATA ==================
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

MOVIES = {}  
# MOVIES = {category: [{name, poster, episodes: [link1, link2]}]}

# ================== FSM ==================
class AddMovie(StatesGroup):
    category = State()
    poster = State()
    name = State()
    episodes = State()

# ================== START ==================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(CATEGORIES, start=1):
        kb.insert(InlineKeyboardButton(f"{i}. {c}", callback_data=f"cat_{i-1}"))
    await msg.answer("🎬 ရုပ်ရှင်အမျိုးအစားရွေးပါ", reply_markup=kb)

# ================== CATEGORY (MEMBER) ==================
@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def show_movies(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    category = CATEGORIES[idx]

    kb = InlineKeyboardMarkup(row_width=2)
    for i, m in enumerate(MOVIES.get(category, [])):
        kb.insert(InlineKeyboardButton(m["name"], callback_data=f"movie_{idx}_{i}"))

    await call.message.answer(f"📂 {category}", reply_markup=kb)
    await call.answer()

# ================== MOVIE → EPISODES ==================
@dp.callback_query_handler(lambda c: c.data.startswith("movie_"))
async def show_episodes(call: types.CallbackQuery):
    _, cidx, midx = call.data.split("_")
    category = CATEGORIES[int(cidx)]
    movie = MOVIES[category][int(midx)]

    kb = InlineKeyboardMarkup(row_width=3)
    for i in range(len(movie["episodes"])):
        kb.insert(InlineKeyboardButton(f"အပိုင်း {i+1}", url=movie["episodes"][i]))

    await call.message.answer_photo(
        movie["poster"],
        caption=f"🎬 {movie['name']}\nအပိုင်းရွေးပါ 👇",
        reply_markup=kb
    )
    await call.answer()

# ================== ADMIN ==================
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ ဇတ်လမ်းအသစ်ထည့်", callback_data="add_movie"))
    await msg.answer("🛠 Admin Panel", reply_markup=kb)

# ================== ADD MOVIE FLOW ==================
@dp.callback_query_handler(text="add_movie")
async def add_movie(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(CATEGORIES, start=1):
        kb.insert(InlineKeyboardButton(f"{i}. {c}", callback_data=f"addcat_{i-1}"))
    await call.message.answer("ဇတ်လမ်းအမျိုးအစားရွေးပါ", reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("addcat_"))
async def add_category(call: types.CallbackQuery, state: FSMContext):
    idx = int(call.data.split("_")[1])
    await state.update_data(category=CATEGORIES[idx])
    await call.message.answer("📸 Poster ပုံ ပို့ပါ")
    await AddMovie.poster.set()
    await call.answer()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddMovie.poster)
async def add_poster(msg: types.Message, state: FSMContext):
    await state.update_data(poster=msg.photo[-1].file_id)
    await msg.answer("🎬 ဇတ်လမ်းနာမည် ပို့ပါ")
    await AddMovie.name.set()

@dp.message_handler(state=AddMovie.name)
async def add_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text, episodes=[])
    await msg.answer("🔗 Episode link တွေကို တစ်ကြောင်းစီ ပို့ပါ\nပြီးရင် /done")
    await AddMovie.episodes.set()

@dp.message_handler(state=AddMovie.episodes)
async def add_episode_links(msg: types.Message, state: FSMContext):
    if msg.text == "/done":
        data = await state.get_data()
        MOVIES.setdefault(data["category"], []).append({
            "name": data["name"],
            "poster": data["poster"],
            "episodes": data["episodes"]
        })
        await state.finish()
        await msg.answer("✅ ဇတ်လမ်းသိမ်းပြီးပါပြီ")
    else:
        data = await state.get_data()
        data["episodes"].append(msg.text)
        await state.update_data(episodes=data["episodes"])
        await msg.answer(f"✔ Episode {len(data['episodes'])} ထည့်ပြီး")

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
