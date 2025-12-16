import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ============ CONFIG ============
BOT_TOKEN = os.getenv("BOT_TOKEN")   # Railway Variable ကနေယူမယ်
ADMINS = [8466996343]
# ================================

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set. Please add it in Railway Variables.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# In-memory storage (later JSON/DB ပြောင်းနိုင်)
movies = {}

# ============ STATES ============
class AddMovie(StatesGroup):
    key = State()
    name = State()
    poster = State()

class AddEpisode(StatesGroup):
    movie_key = State()
    ep_name = State()
    ep_link = State()

# ============ START ============
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    if not movies:
        await msg.answer("🎬 Movie မရှိသေးပါ")
        return

    kb = types.InlineKeyboardMarkup()
    for k, v in movies.items():
        kb.add(types.InlineKeyboardButton(v["name"], callback_data=f"movie:{k}"))

    await msg.answer("🎬 Movie List", reply_markup=kb)

# ============ ADMIN ============
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Movie", "➕ Add Episode")
    await msg.answer("🛠 Admin Panel", reply_markup=kb)

# ============ ADD MOVIE ============
@dp.message_handler(text="➕ Add Movie")
async def add_movie(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return
    await msg.answer("🎬 Movie key ထည့်ပါ (ဥပမာ: movie_a)")
    await AddMovie.key.set()

@dp.message_handler(state=AddMovie.key)
async def get_movie_key(msg: types.Message, state: FSMContext):
    await state.update_data(movie_key=msg.text)
    await msg.answer("🎬 Movie name ထည့်ပါ")
    await AddMovie.name.set()

@dp.message_handler(state=AddMovie.name)
async def get_movie_name(msg: types.Message, state: FSMContext):
    await state.update_data(movie_name=msg.text)
    await msg.answer("🖼 Poster JPG / PNG ပုံကို ပို့ပါ")
    await AddMovie.poster.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddMovie.poster)
async def get_movie_poster(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    movies[data["movie_key"]] = {
        "name": data["movie_name"],
        "poster": msg.photo[-1].file_id,
        "episodes": {}
    }
    await msg.answer("✅ Movie + Poster သိမ်းပြီးပါပြီ")
    await state.finish()

# ============ ADD EPISODE ============
@dp.message_handler(text="➕ Add Episode")
async def add_episode(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return
    await msg.answer("🎬 Movie key ထည့်ပါ (ဥပမာ: movie_a)")
    await AddEpisode.movie_key.set()

@dp.message_handler(state=AddEpisode.movie_key)
async def get_ep_movie(msg: types.Message, state: FSMContext):
    if msg.text not in movies:
        await msg.answer("❌ Movie key မမှန်ပါ")
        return
    await state.update_data(movie_key=msg.text)
    await msg.answer("🎞 Episode name ထည့်ပါ (ဥပမာ: Episode 1)")
    await AddEpisode.ep_name.set()

@dp.message_handler(state=AddEpisode.ep_name)
async def get_ep_name(msg: types.Message, state: FSMContext):
    await state.update_data(ep_name=msg.text)
    await msg.answer("🔗 Episode Channel link ထည့်ပါ\n(ဥပမာ: https://t.me/yourchannel/123)")
    await AddEpisode.ep_link.set()

@dp.message_handler(state=AddEpisode.ep_link)
async def get_ep_link(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    movies[data["movie_key"]]["episodes"][data["ep_name"]] = data["ep_link"]
    await msg.answer("✅ Episode + Channel link ထည့်ပြီးပါပြီ")
    await state.finish()

# ============ OPEN MOVIE ============
@dp.callback_query_handler(lambda c: c.data.startswith("movie:"))
async def open_movie(call: types.CallbackQuery):
    key = call.data.split(":")[1]
    movie = movies[key]

    kb = types.InlineKeyboardMarkup(row_width=2)
    for ep in movie["episodes"]:
        kb.insert(types.InlineKeyboardButton(ep, callback_data=f"ep:{key}:{ep}"))

    await bot.send_photo(
        call.message.chat.id,
        photo=movie["poster"],
        caption=f"🎬 {movie['name']}\nအပိုင်းရွေးပါ 👇",
        reply_markup=kb
    )

# ============ OPEN EPISODE ============
@dp.callback_query_handler(lambda c: c.data.startswith("ep:"))
async def open_episode(call: types.CallbackQuery):
    _, movie_key, ep_name = call.data.split(":", 2)
    link = movies[movie_key]["episodes"][ep_name]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("▶️ Watch Episode", url=link))

    await call.message.answer(
        f"🎞 {ep_name}\nChannel ထဲမှာ ကြည့်ရန် 👇",
        reply_markup=kb
    )

# ============ RUN ============
if __name__ == "__main__":
    print("BOT STARTED")
    executor.start_polling(dp, skip_updates=True)
