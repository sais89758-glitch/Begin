import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [8466996343]   # မင်း Telegram ID
# =========================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================= DATA ===================
# structure:
# categories = {
#   "marriage": {
#       "name": "အိမ်ထောင်ရေးကား",
#       "movies": {
#           "m1": {
#               "poster": file_id,
#               "episodes": {
#                   "အပိုင်း (1)": "https://t.me/xxx/1"
#               }
#           }
#       }
#   }
# }

categories = {
    "love": {"name": "❤️ အချစ်ကား", "movies": {}},
    "marriage": {"name": "💍 အိမ်ထောင်ရေးကား", "movies": {}},
    "war": {"name": "⚔️ စစ်ကား", "movies": {}},
    "palace": {"name": "🏯 နန်းတွင်းကား", "movies": {}},
    "crime": {"name": "🔪 ရာဇဝတ်ကား", "movies": {}},
    "action": {"name": "🔥 အက်ရှင်ကား", "movies": {}},
    "family": {"name": "👨‍👩‍👧 မိသားစုကား", "movies": {}},
    "school": {"name": "🎒 ကျောင်းကား", "movies": {}},
    "history": {"name": "📜 သမိုင်းကား", "movies": {}},
    "fantasy": {"name": "🧙 ဖန်တီးကား", "movies": {}},
}

# ================= STATES =================
class AddMovie(StatesGroup):
    category = State()
    poster = State()
    links = State()

# ================= MEMBER =================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for k, v in categories.items():
        kb.insert(types.InlineKeyboardButton(v["name"], callback_data=f"cat:{k}"))
    await msg.answer("🎬 ရုပ်ရှင်အမျိုးအစားရွေးပါ", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("cat:"))
async def open_category(call: types.CallbackQuery):
    key = call.data.split(":")[1]
    movies = categories[key]["movies"]

    if not movies:
        await call.message.answer("❌ ဒီအမျိုးအစားထဲမှာ မရှိသေးပါ")
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    for m_id in movies:
        kb.insert(types.InlineKeyboardButton(f"🎞 Movie {m_id}", callback_data=f"movie:{key}:{m_id}"))

    await call.message.answer("🎬 Poster ရွေးပါ", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("movie:"))
async def open_movie(call: types.CallbackQuery):
    _, cat, mid = call.data.split(":")
    movie = categories[cat]["movies"][mid]

    kb = types.InlineKeyboardMarkup(row_width=2)
    for ep in movie["episodes"]:
        kb.insert(types.InlineKeyboardButton(ep, callback_data=f"ep:{cat}:{mid}:{ep}"))

    await bot.send_photo(
        call.message.chat.id,
        photo=movie["poster"],
        caption="အပိုင်းရွေးပါ 👇",
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data.startswith("ep:"))
async def open_episode(call: types.CallbackQuery):
    _, cat, mid, ep = call.data.split(":", 3)
    link = categories[cat]["movies"][mid]["episodes"][ep]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("▶️ ကြည့်ရန်", url=link))

    await call.message.answer(ep, reply_markup=kb)

# ================= ADMIN =================
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for k, v in categories.items():
        kb.add(v["name"])
    await msg.answer("🛠 ဇတ်လမ်းအမျိုးအစားရွေးပါ", reply_markup=kb)


@dp.message_handler(lambda m: m.text in [v["name"] for v in categories.values()])
async def admin_choose_category(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in ADMINS:
        return

    for k, v in categories.items():
        if v["name"] == msg.text:
            await state.update_data(category=k)

    await msg.answer("🖼 Poster ပုံပို့ပါ")
    await AddMovie.poster.set()


@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddMovie.poster)
async def admin_get_poster(msg: types.Message, state: FSMContext):
    await state.update_data(poster=msg.photo[-1].file_id)
    await msg.answer(
        "📌 Caption ထဲမှာ Episode link တွေကို ဒီလိုတစ်ကြောင်းစီရေးပါ\n\n"
        "အပိုင်း (1)|https://t.me/xxx/1\n"
        "အပိုင်း (2)|https://t.me/xxx/2"
    )
    await AddMovie.links.set()


@dp.message_handler(state=AddMovie.links)
async def admin_get_links(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    cat = data["category"]
    poster = data["poster"]

    episodes = {}
    for line in msg.text.splitlines():
        if "|" in line:
            name, link = line.split("|", 1)
            episodes[name.strip()] = link.strip()

    mid = f"m{len(categories[cat]['movies']) + 1}"

    categories[cat]["movies"][mid] = {
        "poster": poster,
        "episodes": episodes
    }

    await msg.answer("✅ ဇတ်လမ်းတစ်ခုလုံး သိမ်းပြီးပါပြီ")
    await state.finish()

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
