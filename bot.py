# ================== ADMIN ==================
@dp.message_handler(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ ဇတ်လမ်းအသစ်ထည့်")
    kb.add("/start")
    await msg.answer("🛠 Admin Panel", reply_markup=kb)

# ================== ADD MOVIE FLOW ==================
@dp.message_handler(text="➕ ဇတ်လမ်းအသစ်ထည့်")
async def add_movie(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i, c in enumerate(categories, 1):
        kb.add(f"{i}. {c}")   # ✅ နံပါတ် + နာမည်
    await msg.answer("အမျိုးအစားရွေးပါ", reply_markup=kb)
    await AddMovie.category.set()

@dp.message_handler(state=AddMovie.category)
async def get_cat(msg: types.Message, state: FSMContext):
    cid = int(msg.text.split(".")[0])   # ✅ "1. အချစ်ကား" → 1
    await state.update_data(cat=cid)
    await msg.answer("🖼 Poster ပို့ပါ", reply_markup=types.ReplyKeyboardRemove())
    await AddMovie.poster.set()

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

        await msg.answer(
            "✅ ဇတ်လမ်း သိမ်းပြီးပါပြီ\n/start နဲ့ပြန်ကြည့်နိုင်ပါတယ်",
            reply_markup=types.ReplyKeyboardRemove()
        )

        await state.finish()   # ✅ state အပြည့် reset
        return

    data = await state.get_data()
    ep_no = len(data["episodes"]) + 1
    data["episodes"][ep_no] = msg.text
    await state.update_data(episodes=data["episodes"])
    await msg.answer(f"✔ Episode {ep_no} သိမ်းပြီး")
