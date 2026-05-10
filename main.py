import os
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ✅ Crash বন্ধ করার জন্য safe fallback
if not BOT_TOKEN:
    print("❌ BOT_TOKEN not found! Using fallback...")
    BOT_TOKEN = "8670625404:AAF6K3rNfcVewn_fMhrgtUevFQQlGLmUgww"   # ⚠️ এখানে নিজের token বসাতে পারো

bot = telebot.TeleBot(BOT_TOKEN)

print("Bot started...")

bot.infinity_polling()


ADMIN_ID = 7268416193
CHANNELS = ["@tronex_bd", "@EL_SMM_PANEL"]

_awaiting_amount: set[int] = set()
_pending_deposit: dict[int, int] = {}
_order_state: dict[int, dict] = {}

SERVICES = {
    "Telegram": [
        {"name": "👁️ 1K Views", "price": 3, "key": "tg_views"},
        {"name": "❤️ 1K Reacts+Views", "price": 15, "key": "tg_reacts"},
        {"name": "👥 1K Members", "price": 50, "key": "tg_members"},
    ],
    "Facebook": [
        {"name": "🎥 1K Video Views", "price": 15, "key": "fb_views"},
        {"name": "👤 1K Followers", "price": 80, "key": "fb_followers"},
        {"name": "😍 1K Reactions", "price": 40, "key": "fb_reactions"},
    ],
    "Instagram": [
        {"name": "👁️ 1K Views", "price": 5, "key": "ig_views"},
        {"name": "❤️ 1K Likes", "price": 40, "key": "ig_likes"},
        {"name": "⭐ 1K Followers", "price": 90, "key": "ig_followers"},
    ],
    "TikTok": [
        {"name": "👁️ 1K Views", "price": 5, "key": "tt_views"},
        {"name": "👍 1K Likes", "price": 15, "key": "tt_likes"},
        {"name": "⭐ 1K Followers", "price": 200, "key": "tt_followers"},
    ],
    "YouTube": [
        {"name": "👍 1K Likes", "price": 80, "key": "yt_likes"},
        {"name": "🔔 1K Subscribers", "price": 220, "key": "yt_subs"},
        {"name": "▶️ 1K Views", "price": 60, "key": "yt_views"},
    ],
}

_KEY_TO_SERVICE = {
    svc["key"]: (platform, svc)
    for platform, svcs in SERVICES.items()
    for svc in svcs
}

def _gen_order_id():
    return "ORD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

def _check_channels(user_id):
    missing = []
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ("member", "creator", "administrator"):
                missing.append(ch)
        except:
            pass
    return missing

def _send_main_menu(chat_id, text):
    bot.send_message(chat_id, text, reply_markup=kb.main_menu())


# ================= START =================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    user = message.from_user
    missing = _check_channels(user.id)

    if missing:
        bot.send_message(
            message.chat.id,
            "❌ আগে এই চ্যানেলগুলো join করুন:\n\n"
            + "\n".join(missing)
            + "\n\nJoin করার পরে /start দিন।",
        )
        return

    db.update_user_info(user.id, user.username or "", user.first_name or "User")
    db.get_user(user.id)
    bal = db.get_balance(user.id)

    _send_main_menu(
        message.chat.id,
        f"🏡 <b>WELCOME TO SMM PANEL</b>\n\n"
        f"👋 স্বাগতম, <b>{user.first_name}</b>!\n"
        f"💼 আপনার ব্যালেন্স: <b>{bal:.0f}৳</b>",
    )


@bot.message_handler(commands=["menu"])
def cmd_menu(message):
    bal = db.get_balance(message.from_user.id)
    _send_main_menu(
        message.chat.id,
        f"💼 আপনার ব্যালেন্স: <b>{bal:.0f}৳</b>\n\nকী করতে চান?",
    )


@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(
        message.chat.id,
        "🤖 <b>Bot Commands</b>\n\n"
        "/start — বট শুরু করুন\n"
        "/menu — মেনু খুলুন\n"
        "/help — সাহায্য\n\n"
        "<b>Features:</b>\n"
        "• 🛒 Order\n• 💳 Deposit\n• 📦 Order Status\n"
        "• 👤 My Account\n• 📊 Price & Info\n• 🆘 Support\n• 📋 History",
        reply_markup=kb.main_menu(),
    )


# ================= ADMIN =================

@bot.message_handler(commands=["add"])
def cmd_add_balance(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        _, user_id, amt = message.text.split()
        user_id, amt = int(user_id), int(amt)

        new_bal = db.add_balance(user_id, amt)
        bot.send_message(user_id, f"✅ {amt}৳ যোগ হয়েছে\n💼 Balance: {new_bal}৳")
        bot.send_message(message.chat.id, "✔ Done")

        _pending_deposit.pop(user_id, None)
    except:
        bot.send_message(message.chat.id, "❌ Use: /add user_id amount")


@bot.message_handler(commands=["reject"])
def cmd_reject(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])

        _pending_deposit.pop(user_id, None)

        bot.send_message(user_id, "❌ Deposit request rejected")
        bot.send_message(message.chat.id, "✔ Rejected")

    except:
        bot.send_message(message.chat.id, "❌ Use: /reject user_id")


# ================= RUN =================

print("Bot running... 🚀")
bot.infinity_polling()
