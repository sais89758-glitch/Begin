import logging
import os
from aiogram import Bot, Dispatcher, executor, types

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [8466996343]   # မင်း Telegram ID ထည့်ထား
# ==========================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================= START =================
@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        "၁. ❤️ အချစ်ဇတ်လမ်း",
        "၂. 💍 အိမ်ထောင်ရေးဇတ်လမ်း",
        "၃. ⚔️ စစ်ဇတ်လမ်း",
        "၄. 🏯 နန်းတွင်းဇတ်လမ်း",
        "၅. 🔪 အက်ရှင်ဇတ်လမ်း",
        "၆. 🔥 အကြမ်းဖက်ဇတ်လမ်း",
        "၇. 👻 သရဲဇတ်လမ်း",
        "၈. 🕵️ စုံထောက်ဇတ်လမ်း",
        "၉. 👨‍👩‍👧 မိသားစုဇတ်လမ်း",
        "၁၀. 😂 ဟာသဇတ်လမ်း",
    )
    await msg.answer("🎬 ရုပ်ရှင်အမျိုးအစားရွေးပါ", reply_markup=kb)

# ================= ADMIN PANEL =================
@dp.message_handler(commands=["admin"])
async def admin_panel(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ ဇတ်လမ်းအသစ်ထည့်")
    await msg.answer("🛠 Admin Panel", reply_markup=kb)

# ================= ADD MOVIE =================
@dp.message_handler(lambda msg: msg.text == "➕ ဇတ်လမ်းအသစ်ထည့်")
async def add_movie(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        "၁. ❤️ အချစ်ဇတ်လမ်း",
        "၂. 💍 အိမ်ထောင်ရေးဇတ်လမ်း",
        "၃. ⚔️ စစ်ဇတ်လမ်း",
        "၄. 🏯 နန်းတွင်းဇတ်လမ်း",
        "၅. 🔪 အက်ရှင်ဇတ်လမ်း",
        "၆. 🔥 အကြမ်းဖက်ဇတ်လမ်း",
        "၇. 👻 သရဲဇတ်လမ်း",
        "၈. 🕵️ စုံထောက်ဇတ်လမ်း",
        "၉. 👨‍👩‍👧 မိသားစုဇတ်လမ်း",
        "၁၀. 😂 ဟာသဇတ်လမ်း",
    )

    await msg.answer("📂 ဇတ်လမ်းအမျိုးအစား ရွေးပါ", reply_markup=kb)

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
