# bot.py
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# အခြေခံ Setting များ
# ==============================

# Telegram Bot Token (Environment Variable မှ ယူမည်)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Admin Telegram User ID များ
ADMIN_IDS = [8466996343]

# Data သိမ်းဆည်းမည့် ဖိုင်များ
DATA_FILE = "data.json"
DB_FILE = "stats.db"

# ==============================
# Data Storage Function များ
# ==============================

def load_data() -> Dict[str, Any]:
    """Movie / Series Data ကို JSON ဖိုင်မှ ဖတ်ယူ"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"categories": []}, f, ensure_ascii=False, indent=2)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: Dict[str, Any]):
    """Movie / Series Data ကို JSON ဖိုင်ထဲသို့ သိမ်းဆည်း"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_db():
    """အသုံးပြုမှု စာရင်းသွင်းရန် SQLite Database ဖန်တီး"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id TEXT,
            ts TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def log_click(user_id: int, item_id: str):
    """User Click ကို Database ထဲသို့ မှတ်တမ်းတင်"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO clicks(user_id, item_id, ts) VALUES (?, ?, ?)",
        (user_id, item_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

# ==============================
# Helper Function များ
# ==============================

def is_admin(user_id: int) -> bool:
    """User သည် Admin ဖြစ်မဖြစ် စစ်ဆေး"""
    return user_id in ADMIN_IDS


def build_keyboard(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    """Inline Keyboard တည်ဆောက်"""
    return InlineKeyboardMarkup(rows)


def back_button(target: str):
    """နောက်ပြန်သွားရန် Button"""
    return InlineKeyboardButton("⬅️ နောက်ပြန်", callback_data=f"BACK:{target}")

# ==============================
# Keyboard UI တည်ဆောက်ခြင်း
# ==============================

def categories_keyboard(data):
    """Category Button များ"""
    rows = []
    for cat in data["categories"][:10]:
        rows.append(
            [InlineKeyboardButton(cat["name"], callback_data=f"CAT:{cat['id']}")]
        )
    return build_keyboard(rows)


def items_keyboard(category):
    """Movie / Series Button များ"""
    rows = []
    for item in category.get("items", []):
        rows.append(
            [InlineKeyboardButton(item["title"], callback_data=f"ITEM:{item['id']}")]
        )
    rows.append([back_button("START")])
    return build_keyboard(rows)


def episodes_keyboard(item):
    """Episode Button များ"""
    rows = []
    for ep in item.get("episodes", [])[:10]:
        rows.append(
            [InlineKeyboardButton(f"အပိုင်း {ep['ep']}", url=ep["link"])]
        )
    rows.append([back_button("CAT")])
    return build_keyboard(rows)

# ==============================
# User Command များ
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot စတင်အသုံးပြု"""
    data = load_data()
    await update.effective_chat.send_message(
        "🎬 ရုပ်ရှင် / ဇာတ်လမ်း Bot မှ ကြိုဆိုပါတယ်\n\nအမျိုးအစား ရွေးပါ 👇",
        reply_markup=categories_keyboard(data),
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin Panel"""
    if not is_admin(update.effective_user.id):
        return

    rows = [
        [InlineKeyboardButton("➕ အသစ်ထည့်ရန်", callback_data="ADM:ADD")],
        [InlineKeyboardButton("✏️ ပြင်ရန်", callback_data="ADM:EDIT")],
        [InlineKeyboardButton("❌ ဖျက်ရန်", callback_data="ADM:DEL")],
    ]
    await update.effective_chat.send_message(
        "🛠 Admin Panel",
        reply_markup=build_keyboard(rows),
    )

# ==============================
# Callback Button Handler
# ==============================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_data()
    cd = query.data

    if cd == "BACK:START":
        await query.edit_message_text(
            "အမျိုးအစား ရွေးပါ 👇",
            reply_markup=categories_keyboard(data),
        )
        return

    if cd.startswith("CAT:"):
        cat_id = int(cd.split(":")[1])
        category = next((c for c in data["categories"] if c["id"] == cat_id), None)
        if not category:
            return
        await query.edit_message_text(
            category["name"],
            reply_markup=items_keyboard(category),
        )
        return

    if cd.startswith("ITEM:"):
        item_id = cd.split(":")[1]
        for category in data["categories"]:
            for item in category.get("items", []):
                if item["id"] == item_id:
                    log_click(query.from_user.id, item_id)
                    if item.get("poster"):
                        await query.message.edit_media(
                            media=InputMediaPhoto(
                                media=item["poster"],
                                caption=item["title"],
                            ),
                            reply_markup=episodes_keyboard(item),
                        )
                    else:
                        await query.edit_message_text(
                            item["title"],
                            reply_markup=episodes_keyboard(item),
                        )
                    return

    if cd == "BACK:CAT":
        await query.edit_message_text(
            "အမျိုးအစား ရွေးပါ 👇",
            reply_markup=categories_keyboard(data),
        )
        return

    # ==========================
    # Admin Function များ
    # ==========================
    if not is_admin(query.from_user.id):
        return

    if cd == "ADM:ADD":
        context.user_data.clear()
        context.user_data["stage"] = "ADD_CATEGORY"
        await query.edit_message_text("အမျိုးအစား အမည် ထည့်ပါ (ဥပမာ - အက်ရှင် 🎬)")
        return

# ==============================
# Admin Message Flow
# ==============================

async def admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user_data = context.user_data
    data = load_data()

    if user_data.get("stage") == "ADD_CATEGORY":
        name = update.message.text.strip()
        new_id = max([c["id"] for c in data["categories"]] + [0]) + 1
        user_data["category"] = {"id": new_id, "name": name, "items": []}
        user_data["stage"] = "ADD_TITLE"
        await update.message.reply_text("ရုပ်ရှင် / ဇာတ်လမ်း အမည် ထည့်ပါ")
        return

    if user_data.get("stage") == "ADD_TITLE":
        user_data["item"] = {
            "id": f"item_{int(datetime.utcnow().timestamp())}",
            "title": update.message.text.strip(),
            "poster": "",
            "episodes": [],
        }
        user_data["stage"] = "ADD_POSTER"
        await update.message.reply_text("Poster ပုံ ပို့ပါ (မရှိရင် skip လို့ရေး)")
        return

    if user_data.get("stage") == "ADD_POSTER":
        if update.message.photo:
            user_data["item"]["poster"] = update.message.photo[-1].file_id
        user_data["stage"] = "ADD_EP_COUNT"
        await update.message.reply_text("အပိုင်း အရေအတွက် ထည့်ပါ (၁ မှ ၁၀ အထိ)")
        return

    if user_data.get("stage") == "ADD_EP_COUNT":
        user_data["ep_total"] = int(update.message.text.strip())
        user_data["ep_index"] = 1
        user_data["stage"] = "ADD_EP_LINK"
        await update.message.reply_text(
            f"အပိုင်း {user_data['ep_index']} link ထည့်ပါ"
        )
        return

    if user_data.get("stage") == "ADD_EP_LINK":
        user_data["item"]["episodes"].append(
            {
                "ep": user_data["ep_index"],
                "link": update.message.text.strip(),
            }
        )
        user_data["ep_index"] += 1

        if user_data["ep_index"] <= user_data["ep_total"]:
            await update.message.reply_text(
                f"အပိုင်း {user_data['ep_index']} link ထည့်ပါ"
            )
            return

        user_data["category"]["items"].append(user_data["item"])
        data["categories"].append(user_data["category"])
        save_data(data)
        user_data.clear()

        await update.message.reply_text("✅ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ")
        return

# ==============================
# Statistics Command များ
# ==============================

async def stats_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM clicks WHERE ts >= datetime('now','-1 day')"
    )
    count = cur.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"ဒီနေ့ အသုံးပြုမှု: {count}")


async def stats_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM clicks WHERE ts >= datetime('now','-7 day')"
    )
    count = cur.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"ဒီအပတ် အသုံးပြုမှု: {count}")

# ==============================
# Main
# ==============================

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("stats_day", stats_day))
    app.add_handler(CommandHandler("stats_week", stats_week))

    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, admin_messages))

    app.run_polling()

if __name__ == "__main__":
    main()
