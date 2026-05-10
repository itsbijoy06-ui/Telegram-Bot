import os
import datetime
import random
import string
import telebot
from telebot import types

import database as db
import keyboards as kb

BOT_TOKEN = os.environ.get("8670625404:AAF6K3rNfcVewn_fMhrgtUevFQQlGLmUgww")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

ADMIN_ID = 7268416193
CHANNELS = ["@tronex_bd", "@EL_SMM_PANEL"]

_awaiting_amount: set[int] = set()
_pending_deposit: dict[int, int] = {}
_order_state: dict[int, dict] = {}

SERVICES: dict[str, list] = {
    "Telegram": [
        {"name": "👁️ 1K Views",       "price": 3,   "key": "tg_views"},
        {"name": "❤️ 1K Reacts+Views", "price": 15,  "key": "tg_reacts"},
        {"name": "👥 1K Members",       "price": 50,  "key": "tg_members"},
    ],
    "Facebook": [
        {"name": "🎥 1K Video Views",   "price": 15,  "key": "fb_views"},
        {"name": "👤 1K Followers",     "price": 80,  "key": "fb_followers"},
        {"name": "😍 1K Reactions",     "price": 40,  "key": "fb_reactions"},
    ],
    "Instagram": [
        {"name": "👁️ 1K Views",        "price": 5,   "key": "ig_views"},
        {"name": "❤️ 1K Likes",        "price": 40,  "key": "ig_likes"},
        {"name": "⭐ 1K Followers",     "price": 90,  "key": "ig_followers"},
    ],
    "TikTok": [
        {"name": "👁️ 1K Views",        "price": 5,   "key": "tt_views"},
        {"name": "👍 1K Likes",         "price": 15,  "key": "tt_likes"},
        {"name": "⭐ 1K Followers",     "price": 200, "key": "tt_followers"},
    ],
    "YouTube": [
        {"name": "👍 1K Likes",         "price": 80,  "key": "yt_likes"},
        {"name": "🔔 1K Subscribers",   "price": 220, "key": "yt_subs"},
        {"name": "▶️ 1K Views",        "price": 60,  "key": "yt_views"},
    ],
}

_KEY_TO_SERVICE: dict[str, tuple[str, dict]] = {
    svc["key"]: (platform, svc)
    for platform, svcs in SERVICES.items()
    for svc in svcs
}

def _gen_order_id() -> str:
    return "ORD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

def _check_channels(user_id: int) -> list[str]:
    missing = []
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ("member", "creator", "administrator"):
                missing.append(ch)
        except Exception:
            pass
    return missing

def _send_main_menu(chat_id: int, text: str) -> None:
    bot.send_message(chat_id, text, reply_markup=kb.main_menu())

# ── /start ──────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(message):
    user = message.from_user
    missing = _check_channels(user.id)
    if missing:
        bot.send_message(message.chat.id,
            f"❌ আগে এই চ্যানেলগুলো join করুন:\n\n" + "\n".join(missing) +
            "\n\nJoin করার পরে /start দিন।")
        return
    db.update_user_info(user.id, user.username or "", user.first_name or "User")
    db.get_user(user.id)
    bal = db.get_balance(user.id)
    _send_main_menu(message.chat.id,
        f"🏡 <b>WELCOME TO SMM PANEL</b>\n\n"
        f"👋 স্বাগতম, <b>{user.first_name}</b>!\n"
        f"💼 আপনার ব্যালেন্স: <b>{bal:.0f}৳</b>")

# ── /menu & /help ────────────────────────────────────────────────────────────
@bot.message_handler(commands=["menu"])
def cmd_menu(message):
    bal = db.get_balance(message.from_user.id)
    _send_main_menu(message.chat.id,
        f"💼 আপনার ব্যালেন্স: <b>{bal:.0f}৳</b>\n\nকী করতে চান?")

@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(message.chat.id,
        "🤖 <b>Bot Commands</b>\n\n"
        "/start — বট শুরু করুন\n/menu — মেনু খুলুন\n/help — সাহায্য\n\n"
        "<b>Features:</b>\n• 🛒 Order\n• 💳 Deposit\n• 📦 Order Status\n"
        "• 👤 My Account\n• 📊 Price & Info\n• 🆘 Support\n• 📋 History",
        reply_markup=kb.main_menu())
  # ── Admin: /add ──────────────────────────────────────────────────────────────
@bot.message_handler(commands=["add"])
def cmd_add_balance(message):
    if message.chat.id != ADMIN_ID: return
    try:
        _, user_id, amt = message.text.split()[0], int(message.text.split()[1]), int(message.text.split()[2])
        new_bal = db.add_balance(user_id, amt, note="Admin deposit approval")
        bot.send_message(user_id, f"✅ <b>{amt}৳</b> আপনার অ্যাকাউন্টে যোগ হয়েছে!\n💼 নতুন ব্যালেন্স: <b>{new_bal:.0f}৳</b>")
        bot.send_message(message.chat.id, f"✔ {user_id} কে {amt}৳ দেওয়া হয়েছে।")
        _pending_deposit.pop(user_id, None)
    except: bot.send_message(message.chat.id, "❌ ভুল format\nUse: /add user_id amount")

# ── Admin: /deduct ───────────────────────────────────────────────────────────
@bot.message_handler(commands=["deduct"])
def cmd_deduct_balance(message):
    if message.chat.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        user_id, amt = int(parts[1]), int(parts[2])
        success, new_bal = db.deduct_balance(user_id, amt, note="Admin deduction")
        if success:
            bot.send_message(user_id, f"🔴 আপনার অ্যাকাউন্ট থেকে <b>{amt}৳</b> কাটা হয়েছে।\n💼 নতুন ব্যালেন্স: <b>{new_bal:.0f}৳</b>")
            bot.send_message(message.chat.id, f"✔ {user_id} থেকে {amt}৳ কাটা হয়েছে।")
        else: bot.send_message(message.chat.id, f"❌ ব্যালেন্স কম। বর্তমান: {new_bal:.0f}৳")
    except: bot.send_message(message.chat.id, "❌ Use: /deduct user_id amount")

# ── Admin: /setstatus ────────────────────────────────────────────────────────
@bot.message_handler(commands=["setstatus"])
def cmd_set_status(message):
    if message.chat.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        user_id, order_id, status = int(parts[1]), parts[2], " ".join(parts[3:])
        if db.update_order_status(user_id, order_id, status):
            bot.send_message(user_id, f"📦 অর্ডার <code>{order_id}</code> আপডেট:\n➡️ <b>{status}</b>")
            bot.send_message(message.chat.id, f"✔ Order {order_id} → {status}")
        else: bot.send_message(message.chat.id, "❌ Order ID পাওয়া যায়নি।")
    except: bot.send_message(message.chat.id, "❌ Use: /setstatus user_id ORDER-ID status")

# ── Admin: /users ────────────────────────────────────────────────────────────
@bot.message_handler(commands=["users"])
def cmd_users(message):
    if message.chat.id != ADMIN_ID: return
    all_users = db.get_all_users()
    deposited = spent = orders = 0
    for u in all_users.values():
        for t in u.get("transactions", []):
            if t["type"] == "credit": deposited += t["amount"]
            else: spent += t["amount"]
        orders += len(u.get("orders", []))
    bot.send_message(message.chat.id,
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users: <b>{len(all_users)}</b>\n"
        f"🛒 Total Orders: <b>{orders}</b>\n"
        f"💰 Total Deposited: <b>{deposited:.0f}৳</b>\n"
        f"💸 Total Spent: <b>{spent:.0f}৳</b>")

# ── Admin: /listorders ───────────────────────────────────────────────────────
@bot.message_handler(commands=["listorders"])
def cmd_list_orders(message):
    if message.chat.id != ADMIN_ID: return
    pending = [
        (uid, u.get("first_name","?"), o)
        for uid, u in db.get_all_users().items()
        for o in u.get("orders", []) if o.get("status") == "Processing"
    ]
    if not pending:
        bot.send_message(message.chat.id, "✅ কোনো pending অর্ডার নেই।"); return
    lines = [f"📋 <b>Pending Orders ({len(pending)})</b>\n"]
    for uid, name, o in pending[-20:]:
        lines.append(
            f"⏳ <code>{o['order_id']}</code>\n"
            f"   👤 {name} (<code>{uid}</code>)\n"
            f"   📲 {o['platform']} — {o['service']}\n"
            f"   🔢 {o['quantity']:,} | 💵 {o['cost']:.0f}৳\n"
            f"   🔗 <code>{o['link']}</code>\n"
            f"   ✅ /setstatus {uid} {o['order_id']} Completed")
    bot.send_message(message.chat.id, "\n\n".join(lines))
  # ── Admin: /broadcast ────────────────────────────────────────────────────────
@bot.message_handler(commands=["broadcast"])
def cmd_broadcast(message):
    if message.chat.id != ADMIN_ID: return
    text = message.text.partition(" ")[2].strip()
    if not text:
        bot.send_message(message.chat.id, "❌ Use: /broadcast আপনার মেসেজ"); return
    sent = failed = 0
    for uid in db.get_all_users():
        try: bot.send_message(int(uid), f"📢 <b>Announcement</b>\n\n{text}"); sent += 1
        except: failed += 1
    bot.send_message(message.chat.id, f"✅ Broadcast সম্পন্ন!\n\n✔ Sent: {sent}\n❌ Failed: {failed}")

# ── Admin: /reject ───────────────────────────────────────────────────────────
@bot.message_handler(commands=["reject"])
def cmd_reject(message):
    if message.chat.id != ADMIN_ID: return
    try:
        user_id = int(message.text.split()[1])
        _pending_deposit.pop(user)
      
