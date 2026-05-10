from telebot.types import ReplyKeyboardMarkup

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛒 Order", "💳 Deposit")
    kb.row("📦 Order Status", "👤 My Account")
    kb.row("📊 Price & Info", "🆘 Support")
    kb.row("📋 History")
    return kb
