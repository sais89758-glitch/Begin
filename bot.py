import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# ========= CONFIG =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [8466996343]
# ==========================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ========= DATA =========
CATEGORIES = [
    "၁. ❤️ အချစ်ဇတ်လမ်း",
    "၂. 💍 အိမ်ထောင်ရေးဇတ်လမ်း",
    "၃. ⚔️ စစ်ဇတ်လမ်း",
    "၄. 🏯 နန်းတွင်းဇတ်လမ်း",
    "၅. 🔪 အက်ရှင်ဇတ်လမ်း",
    "၆. 🔥 အကြမ်းဖက်ဇတ်လမ်း",
    "၇. 👻 သရဲဇတ်လမ်း",
    "၈. 🕵️ စုံထောက်ဇတ်လမ်း",
    "၉. 👨‍👩‍👧 မိသားစုဇတ်လမ်း",
    "၁၀. 😂 ဟာသဇတ်လမ်း"
]

movies = {}  
# movies = {
#   category_index: [
#       {
#         "title": "ဇတ်လမ်းနာမည်",
#         "poster": file_id,
#         "episodes": ["link1","link2",...]
#       }
#   ]
# }

# ========= START =========
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(len(CATEGORIES)):
        kb.add(CATEGORIES[i])
    await msg.answer("🎬 ဇတ်လမ်းအမျိုးအစား ရွေးပါ", reply_markup=kb)

# ========= ADMIN =========
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ ဇတ်လမ်းအသစ်ထည့်")
    await msg.answer("🛠 Admin Panel", reply_markup=kb)

# ========= RUN =========
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
