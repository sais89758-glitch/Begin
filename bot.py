# ======================= bot.py (ALL-IN-ONE) =======================
import os, sqlite3, logging, csv
from datetime import datetime, date
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [8466996343]  # 🔴 မင်း Telegram ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ======================= DB =======================
db = sqlite3.connect("movies.db")
cur = db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS movies(
 id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, name TEXT, poster TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS episodes(
 id INTEGER PRIMARY KEY AUTOINCREMENT, movie_id INTEGER, ep_no INTEGER, link TEXT, views INTEGER DEFAULT 0)""")
cur.execute("""CREATE TABLE IF NOT EXISTS history(
 user_id INTEGER, movie TEXT, episode INTEGER, time TEXT)""")
db.commit()

# ======================= DATA =======================
CATEGORIES = [
 "❤️ အချစ်ဇတ်လမ်း","💍 အိမ်ထောင်ရေးဇတ်လမ်း","⚔️ စစ်ဇတ်လမ်း","🏯 နန်းတွင်းဇတ်လမ်း",
 "🔪 အက်ရှင်ဇတ်လမ်း","🔥 အကြမ်းဖက်ဇတ်လမ်း","👻 သရဲဇတ်လမ်း","🕵️ စုံထောက်ဇတ်လမ်း",
 "👨‍👩‍👧 မိသားစုဇတ်လမ်း","😂 ဟာသဇတ်လမ်း",
]

# Category -> Channel mapping (မိန်းချယ်နယ်မရှိ, အသီးသီး)
CATEGORY_CHANNELS = {
 "❤️ အချစ်ဇတ်လမ်း": "@love_channel",
 "💍 အိမ်ထောင်ရေးဇတ်လမ်း": "@marriage_channel",
 "⚔️ စစ်ဇတ်လမ်း": "@war_channel",
 "🏯 နန်းတွင်းဇတ်လမ်း": "@palace_channel",
 "🔪 အက်ရှင်ဇတ်လမ်း": "@action_channel",
 "🔥 အကြမ်းဖက်ဇတ်လမ်း": "@crime_channel",
 "👻 သရဲဇတ်လမ်း": "@horror_channel",
 "🕵️ စုံထောက်ဇတ်လမ်း": "@detective_channel",
 "👨‍👩‍👧 မိသားစုဇတ်လမ်း": "@family_channel",
 "😂 ဟာသဇတ်လမ်း": "@comedy_channel",
}

@dp.callback_query_handler(lambda c: c.data.startswith("admin_cat_"))
async def admin_choose_category(c: types.CallbackQuery, state: FSMContext):
    if c.from_user.id not in ADMIN_IDS:
        await c.answer("Admin မဟုတ်ပါ", show_alert=True)
        return

    idx = int(c.data.split("_")[-1])
    category = CATEGORIES[idx]

    await state.update_data(category=category)

    await c.message.answer(
        f"📸 {category}\n\nPoster ပုံကို ပို့ပါ"
    )
    await AdminAdd.poster.set()
    await c.answer()

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

# ======================= HELPERS =======================
def cat_kb(prefix):
 kb=InlineKeyboardMarkup(row_width=2)
 for i,c in enumerate(CATEGORIES):
  kb.insert(InlineKeyboardButton(f"{i+1}. {c}", callback_data=f"{prefix}_{i}"))
 return kb

async def check_join(user_id:int, channel:str)->bool:
 try:
  m=await bot.get_chat_member(channel, user_id)
  return m.status in ["member","administrator","creator"]
 except:
  return False

# ======================= FSM =======================
class AdminAdd(StatesGroup):
 category=State(); poster=State(); name=State(); episodes=State()

# ======================= MEMBER =======================
@dp.message_handler(commands=["start"])
async def start(m:types.Message):
 await m.answer("🎬 ရုပ်ရှင်အမျိုးအစားရွေးပါ", reply_markup=cat_kb("user_cat"))

@dp.callback_query_handler(lambda c:c.data.startswith("user_cat_"))
async def user_cat(c:types.CallbackQuery):
 idx=int(c.data.split("_")[-1]); cat=CATEGORIES[idx]
 cur.execute("SELECT id,name FROM movies WHERE category=?", (cat,))
 rows=cur.fetchall()
 if not rows: await c.answer("ဇတ်လမ်းမရှိသေးပါ"); return
 kb=InlineKeyboardMarkup(row_width=2)
 for r in rows: kb.insert(InlineKeyboardButton(r[1], callback_data=f"user_movie_{r[0]}"))
 kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_start"))
 await c.message.answer("🎬 ဇတ်လမ်းရွေးပါ", reply_markup=kb); await c.answer()

@dp.callback_query_handler(lambda c:c.data=="back_start")
async def back_start(c:types.CallbackQuery):
 await start(c.message); await c.answer()

@dp.callback_query_handler(lambda c:c.data.startswith("user_movie_"))
async def user_movie(c:types.CallbackQuery):
 movie_id=int(c.data.split("_")[-1])
 cur.execute("SELECT category,name,poster FROM movies WHERE id=?", (movie_id,))
 cat,name,poster=cur.fetchone()
 ch=CATEGORY_CHANNELS.get(cat)
 if ch and not await check_join(c.from_user.id, ch):
  kb=InlineKeyboardMarkup().add(InlineKeyboardButton("🔔 Channel Join", url=f"https://t.me/{ch.replace('@','')}"))
  await c.message.answer(f"❌ ကြည့်ရန် {ch} ကို Join လုပ်ပါ", reply_markup=kb); return
 cur.execute("SELECT ep_no,views FROM episodes WHERE movie_id=?", (movie_id,))
 eps=cur.fetchall()
 kb=InlineKeyboardMarkup(row_width=3)
 for e in eps: kb.insert(InlineKeyboardButton(f"EP {e[0]} 👁{e[1]}", callback_data=f"watch_{movie_id}_{e[0]}"))
 kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_start"))
 await c.message.answer_photo(poster, caption=name, reply_markup=kb); await c.answer()

@dp.callback_query_handler(lambda c:c.data.startswith("watch_"))
async def watch(c:types.CallbackQuery):
 _,mid,ep=c.data.split("_"); mid=int(mid); ep=int(ep)
 cur.execute("SELECT link FROM episodes WHERE movie_id=? AND ep_no=?", (mid,ep))
 link=cur.fetchone()[0]
 cur.execute("UPDATE episodes SET views=views+1 WHERE movie_id=? AND ep_no=?", (mid,ep))
 cur.execute("SELECT name FROM movies WHERE id=?", (mid,))
 mname=cur.fetchone()[0]
 cur.execute("INSERT INTO history VALUES (?,?,?,?)",(c.from_user.id,mname,ep,datetime.now().isoformat()))
 db.commit()
 await c.message.answer(link, protect_content=True); await c.answer()

# ======================= ADMIN =======================
@dp.message_handler(commands=["admin"])
async def admin(m:types.Message):
 if m.from_user.id not in ADMIN_IDS: return
 await m.answer("⚙️ Category ရွေးပါ", reply_markup=cat_kb("admin_cat"))

@dp.callback_query_handler(lambda c:c.data.startswith("admin_cat_"))
async def admin_cat(c:types.CallbackQuery, s:FSMContext):
 if c.from_user.id not in ADMIN_IDS: return
 idx=int(c.data.split("_")[-1]); await s.update_data(category=CATEGORIES[idx])
 await c.message.answer("📸 Poster ပုံပို့ပါ"); await AdminAdd.poster.set(); await c.answer()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AdminAdd.poster)
async def admin_poster(m:types.Message, s:FSMContext):
 await s.update_data(poster=m.photo[-1].file_id); await m.answer("🎬 ဇတ်လမ်းနာမည်ပို့ပါ"); await AdminAdd.name.set()

@dp.message_handler(state=AdminAdd.name)
async def admin_name(m:types.Message, s:FSMContext):
 await s.update_data(name=m.text, episodes=[]); await m.answer("🔗 Episode link တစ်ခုချင်းပို့ပါ (max 10)\n/done"); await AdminAdd.episodes.set()

@dp.message_handler(state=AdminAdd.episodes)
async def admin_eps(m:types.Message, s:FSMContext):
 d=await s.get_data()
 if m.text=="/done":
  cur.execute("INSERT INTO movies(category,name,poster) VALUES(?,?,?)",(d["category"],d["name"],d["poster"]))
  mid=cur.lastrowid
  for i,l in enumerate(d["episodes"],1):
   cur.execute("INSERT INTO episodes(movie_id,ep_no,link) VALUES(?,?,?)",(mid,i,l))
  db.commit(); await m.answer("✅ သိမ်းပြီး"); await s.finish(); return
 if len(d["episodes"])>=10: await m.answer("❌ ၁၀ ခုအထိပဲ /done"); return
 d["episodes"].append(m.text); await s.update_data(episodes=d["episodes"])
 await m.answer(f"✔ Episode {len(d['episodes'])}")

# ======================= REPORTS =======================
@dp.message_handler(commands=["daily"])
async def daily(m:types.Message):
 if m.from_user.id not in ADMIN_IDS: return
 today=date.today().isoformat()
 cur.execute("SELECT movie,episode,COUNT(*) FROM history WHERE date(time)=? GROUP BY movie,episode",(today,))
 rows=cur.fetchall()
 with open("daily.csv","w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); w.writerow(["Movie","Episode","Views"]); w.writerows(rows)
 await m.answer_document(open("daily.csv","rb"))

@dp.message_handler(commands=["weekly"])
async def weekly(m:types.Message):
 if m.from_user.id not in ADMIN_IDS: return
 cur.execute("SELECT movie,episode,COUNT(*) FROM history WHERE time>=datetime('now','-7 days') GROUP BY movie,episode")
 rows=cur.fetchall()
 with open("weekly.csv","w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); w.writerow(["Movie","Episode","Views"]); w.writerows(rows)
 await m.answer_document(open("weekly.csv","rb"))

# ======================= RUN =======================
if __name__=="__main__":
 executor.start_polling(dp, skip_updates=True)
# ====================================================
