import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [8466996343]  # မင်း Telegram ID

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# ================= DATA =================
CATEGORIES = [
    "အချစ်ကား",
    "အိမ်ထောင်ရေးကား",
    "စစ်ကား",
    "နန်းတွင်းကား",
    "Action",
    "Crime",
    "Fantasy",
    "Family",
    "History",
    "Comedy"
]

MOVIES = {i: [] for i in range(1, 11)}

# ================= STATES =================
class AddMovie(StatesGroup):
    category = State()
    poster = State()

# ================= START =================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    for i, name in enumerate(CATEGORIES, start=1):
        kb.add(InlineKeyboardButton(f"({i}) {name}", callback_data=f"cat_{i}"))
    await msg.answer("🎬 ရုပ်ရှင်အမျိုးအစားရွေးပါ", reply_markup=kb)

# ================= CATEGORY =================
@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def show_posters(call: types.CallbackQuery):
    cat = int(call.data.split("_")[1])
    kb = InlineKeyboardMarkup()
    for i, m in enumerate(MOVIES[cat]):
        kb.add(InlineKeyboardButton(m["title"], callback_data=f"movie_{cat}_{i}"))
    await call.message.edit_text(f"📂 {CATEGORIES[cat-1]}", reply_markup=kb)

# ================= MOVIE =================
@dp.callback_query_handler(lambda c: c.data.startswith("movie_"))
async def show_episodes(call: types.CallbackQuery):
    _, cat, idx = call.data.split("_")
    movie = MOVIES[int(cat)][int(idx)]

    kb = InlineKeyboardMarkup(row_width=2)
    for i, link in enumerate(movie["episodes"], start=1):
        kb.add(InlineKeyboardButton(f"အပိုင်း({i})", url=link))

    await call.message.answer_photo(
        movie["poster"],
        caption=movie["title"],
        reply_markup=kb
    )

# ================= ADMIN =================
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return

    kb = InlineKeyboardMarkup(row_width=2)
    for i, name in enumerate(CATEGORIES, start=1):
        kb.add(InlineKeyboardButton(f"({i}) {name}", callback_data=f"add_{i}"))
    await msg.answer("Admin: Category ရွေးပါ", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("add_"))
async def admin_category(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(category=int(call.data.split("_")[1]))
    await call.message.answer(
        "Poster ပုံပို့ပါ\n\n"
        "Caption format:\n"
        "ဇတ်လမ်းနာမည်\n"
        "link1\nlink2\nlink3\n..."
    )
    await AddMovie.poster.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddMovie.poster)
async def save_movie(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    lines = msg.caption.splitlines()

    title = lines[0]
    episodes = lines[1:]

    MOVIES[data["category"]].append({
        "title": title,
        "poster": msg.photo[-1].file_id,
        "episodes": episodes
    })

    await msg.answer("✅ ဇတ်လမ်းတင်ပြီးပါပြီ")
    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp)
