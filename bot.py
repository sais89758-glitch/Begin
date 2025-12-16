import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [8466996343]   # 🔴 သင့် admin id

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================== DATA ==================
categories = [
    "❤️ အချစ်ကား", "💍 အိမ်ထောင်ရေးကား", "⚔️ စစ်ကား", "🔥 အက်ရှင်ကား", "🧙 နန်တွင်းကား",
    "👻 သရဲကား", "🕵️ စုံထောက်ကား", "🎭 ဒရာမာကား", "😂 ဟာသကား", "👨‍👩‍👧 မိသားစုကား"
]

movies = {}  
# {cat_id: [{name, poster, episodes{1:link}}]}

# ================== STATES ==================
class AddMovie(StatesGroup):
    category = State()
    poster = State()
    title = State()
    episodes = State()

# ================== START ==================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(categories, 1):
        kb.insert(types.InlineKeyboardButton(f"{i}. {c}", callback_data=f"cat:{i}"))
    await msg.answer("🎬 ရုပ်ရှင်အမျိုးအစားရွေးပါ", reply_markup=kb)

# ================== CATEGORY ==================
@dp.callback_query_handler(lambda c: c.data.startswith("cat:"))
async def open_category(call: types.CallbackQuery):
    cid = int(call.data.split(":")[1])
    if cid not in movies:
        await call.message.answer("❌ ဇတ်လမ်းမရှိသေးပါ")
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    for i, m in enumerate(movies[cid]):
        kb.insert(types.InlineKeyboardButton(m["name"], callback_data=f"movie:{cid}:{i}"))

    await call.message.answer("📽 ဇတ်လမ်းရွေးပါ", reply_markup=kb)

# ================== MOVIE ==================
@dp.callback_query_handler(lambda c: c.data.startswith("movie:"))
async def open_movie(call: types.CallbackQuery):
    _, cid, mid = call.data.split(":")
    movie = movies[int(cid)][int(mid)]

    kb = types.InlineKeyboardMarkup(row_width=3)
    for ep in movie["episodes"]:
        kb.insert(types.InlineKeyboardButton(f"အပိုင်း {ep}", callback_data=f"ep:{cid}:{mid}:{ep}"))

    await bot.send_photo(
        call.message.chat.id,
        movie["poster"],
        caption=movie["name"],
        reply_markup=kb
    )

# ================== EPISODE ==================
@dp.callback_query_handler(lambda c: c.data.startswith("ep:"))
async def open_ep(call: types.CallbackQuery):
    _, cid, mid, ep = call.data.split(":")
    link = movies[int(cid)][int(mid)]["episodes"][int(ep)]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("▶️ ကြည့်ရန်", url=link))

    await call.message.answer(f"🎞 အပိုင်း {ep}", reply_markup=kb)

# ================== ADMIN ==================
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ ဇတ်လမ်းအသစ်ထည့်")
    await msg.answer("🛠 Admin Panel", reply_markup=kb)

# ================== ADD MOVIE FLOW ==================
@dp.message_handler(text="➕ ဇတ်လမ်းအသစ်ထည့်")
async def add_movie(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i, c in enumerate(categories, 1):
        kb.add(f"{i}")
    await msg.answer("အမျိုးအစား နံပါတ်ရွေးပါ", reply_markup=kb)
    await AddMovie.category.set()

@dp.message_handler(state=AddMovie.category)
async def get_cat(msg: types.Message, state: FSMContext):
    cid = int(msg.text)
    await state.update_data(cat=cid)
    await msg.answer("🖼 Poster ပို့ပါ", reply_markup=types.ReplyKeyboardRemove())
    await AddMovie.poster.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddMovie.poster)
async def get_poster(msg: types.Message, state: FSMContext):
    await state.update_data(poster=msg.photo[-1].file_id)
    await msg.answer("🎬 ဇတ်လမ်းနာမည် ပို့ပါ")
    await AddMovie.title.set()

@dp.message_handler(state=AddMovie.title)
async def get_title(msg: types.Message, state: FSMContext):
    await state.update_data(title=msg.text, episodes={})
    await msg.answer("🔗 Episode link တစ်ကြောင်းစီပို့ပါ\nပြီးရင် /done")
    await AddMovie.episodes.set()

@dp.message_handler(state=AddMovie.episodes)
async def get_links(msg: types.Message, state: FSMContext):
    if msg.text == "/done":
        data = await state.get_data()
        cid = data["cat"]

        movies.setdefault(cid, []).append({
            "name": data["title"],
            "poster": data["poster"],
            "episodes": data["episodes"]
        })

        await msg.answer("✅ သိမ်းပြီးပါပြီ")
        await state.finish()
        return

    data = await state.get_data()
    ep_no = len(data["episodes"]) + 1
    data["episodes"][ep_no] = msg.text
    await state.update_data(episodes=data["episodes"])
    await msg.answer(f"✔ Episode {ep_no} သိမ်းပြီး")

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
