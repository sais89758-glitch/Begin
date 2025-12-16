import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
# =========================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================= DATA ===================
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
# {category: [{name, poster, episodes: []}]}

# ================= FSM ====================
class AddMovie(StatesGroup):
    category = State()
    poster = State()
    name = State()
    episodes = State()

# ================= START ==================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    for i, c in enumerate(CATEGORIES, start=1):
        kb.insert(
            InlineKeyboardButton(
                f"{i}. {c}", callback_data=f"select_cat_{i-1}"
            )
        )
    await msg.answer("🎬 ရုပ်ရှင်အမျိုးအစားရွေးပါ", reply_markup=kb)

# ============ CATEGORY SELECT =============
@dp.callback_query_handler(lambda c: c.data.startswith("select_cat_"))
async def select_category(call: types.CallbackQuery, state: FSMContext):
    idx = int(call.data.split("_")[-1])
    category = CATEGORIES[idx]
    await state.update_data(category=category)

    await call.message.answer("📸 ပိုစတာပုံ ပို့ပါ")
    await AddMovie.poster.set()
    await call.answer()

# ============ POSTER ======================
@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddMovie.poster)
async def get_poster(msg: types.Message, state: FSMContext):
    await state.update_data(poster=msg.photo[-1].file_id)
    await msg.answer("🎬 ဇတ်လမ်းနာမည် ပို့ပါ")
    await AddMovie.name.set()

# ============ MOVIE NAME ==================
@dp.message_handler(state=AddMovie.name)
async def get_movie_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text, episodes=[])
    await msg.answer(
        "🔗 Episode link တွေကို တစ်ကြောင်းစီ ပို့ပါ\n"
        "အများဆုံး ၁၀ ခု\n"
        "ပြီးရင် /done"
    )
    await AddMovie.episodes.set()

# ============ EPISODES ====================
@dp.message_handler(state=AddMovie.episodes)
async def get_episodes(msg: types.Message, state: FSMContext):
    if msg.text == "/done":
        data = await state.get_data()
        category = data["category"]

        MOVIES.setdefault(category, []).append({
            "name": data["name"],
            "poster": data["poster"],
            "episodes": data["episodes"]
        })

        movie_index = len(MOVIES[category]) - 1

        kb = InlineKeyboardMarkup(row_width=3)
        for i, link in enumerate(data["episodes"], start=1):
            kb.insert(
                InlineKeyboardButton(
                    f"အပိုင်း {i}", url=link
                )
            )

        await msg.answer_photo(
            data["poster"],
            caption=f"🎬 {data['name']}\nအပိုင်းရွေးပါ 👇",
            reply_markup=kb
        )

        await state.finish()
        return

    data = await state.get_data()
    if len(data["episodes"]) >= 10:
        await msg.answer("❌ Episode ၁၀ ခုအထိပဲ ထည့်လို့ရပါတယ်\n/done")
        return

    data["episodes"].append(msg.text)
    await state.update_data(episodes=data["episodes"])
    await msg.answer(f"✔ အပိုင်း {len(data['episodes'])} ထည့်ပြီး")

# ================= RUN ====================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
