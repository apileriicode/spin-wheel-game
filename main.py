import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import random
from datetime import datetime
from config import *
from database import Database

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ініціалізація БД
db = Database()

# ========== КОМАНДИ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Перевірити чи є в БД
    user = db.get_user(user_id)
    if not user:
        # Перевірити чи є реферер
        referrer_id = None
        if context.args and context.args[0].isdigit():
            referrer_id = int(context.args[0])
        
        db.create_user(user_id, username, referrer_id)
        
        # Якщо є реферер, дати бонус
        if referrer_id:
            db.update_balance(referrer_id, REFERRAL_BONUS, 'add')
            db.add_referral(referrer_id, user_id)
    
    # Меню
    keyboard = [
        [InlineKeyboardButton("🎡 Крутити колесо", callback_data='spin_menu')],
        [InlineKeyboardButton("👤 Мій профіль", callback_data='profile')],
        [InlineKeyboardButton("👥 Мої реферали", callback_data='referrals')],
        [InlineKeyboardButton("🏆 Лідерборд", callback_data='leaderboard')],
        [InlineKeyboardButton("❓ Допомога", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎡 Ласкаво просимо в **Spin Wheel Game**!\n\n"
        f"Крутіть колесо удачі та вигравайте призи! 🎁\n\n"
        f"Оберіть дію:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    help_text = """
🎡 **Як грати?**

1️⃣ Натисніть "Крутити колесо"
2️⃣ Виберіть суму (від 1 до 999,999,999 зірок)
3️⃣ Чекайте результат 🌀
4️⃣ Вигравайте призи! 🎁

💰 **Система рефералів:**
• За запрошення друга: +3 зірки
• Якщо друг поповнить: +2 зірки

📊 **Статистика:**
• Переглядайте свій профіль
• Перевіряйте заробітки
• Займайте місце в лідербордом

💡 **Поради:**
• Чим більша ставка, тим більший виграш
• Розповсюджуйте посилання друзям
• Граймо розумно 😉
    """
    
    if update.message:
        await update.message.reply_text(help_text, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(help_text, parse_mode='Markdown')

# ========== CALLBACK ОБРОБНИКИ ==========

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробка кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'spin_menu':
        await show_spin_menu(query, context)
    elif query.data == 'profile':
        await show_profile(query, context)
    elif query.data == 'referrals':
        await show_referrals(query, context)
    elif query.data == 'leaderboard':
        await show_leaderboard(query, context)
    elif query.data == 'help':
        await help_command(update, context)
    elif query.data.startswith('spin_'):
        await process_spin(query, context)

async def show_spin_menu(query, context):
    """Меню прокруту"""
    user_id = query.from_user.id
    user = db.get_user(user_id)
    
    text = f"""
🎡 **Крутити колесо**

Ваш баланс: **{user['balance']} ⭐**

Виберіть суму для ставки:
    """
    
    amounts = [1, 10, 100, 1000, 10000, 50000, 100000, 999999999]
    keyboard = []
    
    for amount in amounts:
        if amount <= user['balance']:
            keyboard.append([InlineKeyboardButton(f"{amount} ⭐", callback_data=f"spin_{amount}")])
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='back_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def process_spin(query, context):
    """Обробити спін"""
    user_id = query.from_user.id
    user = db.get_user(user_id)
    
    bet = int(query.data.split('_')[1])
    
    if user['balance'] < bet:
        await query.edit_message_text(
            "❌ Недостатньо коштів на рахунку!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data='spin_menu')]])
        )
        return
    
    # Списати ставку
    db.update_balance(user_id, bet, 'subtract')
    
    # Генерувати результат
    multiplier = random.choice(SPIN_MULTIPLIERS)
    winnings = int(bet * multiplier)
    
    # Додати виграш
    db.update_balance(user_id, winnings, 'add')
    
    # Записати спін
    db.record_spin(user_id, bet, multiplier, winnings, 'STARS')
    db.add_transaction(user_id, -bet, 'spin', 'STARS', f"Ставка на колесо")
    db.add_transaction(user_id, winnings, 'win', 'STARS', f"Виграш на колесі (x{multiplier})")
    
    # Новий баланс
    updated_user = db.get_user(user_id)
    new_balance = updated_user['balance']
    
    # Формування результату
    if multiplier == 0.5:
        emoji = "😢 Мало повезло"
    elif multiplier == 0.75:
        emoji = "😐 Так собі"
    elif multiplier == 1.0:
        emoji = "😊 Нічия"
    elif multiplier <= 2.0:
        emoji = "😄 Гарно!"
    else:
        emoji = "🤩 СУПЕР! Великий виграш!"
    
    text = f"""
🎡 **Колесо крутиться...** ✨

{emoji}

💰 Ставка: {bet} ⭐
✨ Множник: x{multiplier}
🎁 Виграш: {winnings} ⭐

💵 Новий баланс: {new_balance} ⭐
    """
    
    keyboard = [
        [InlineKeyboardButton("🎡 Крутити ще", callback_data='spin_menu')],
        [InlineKeyboardButton("👤 Профіль", callback_data='profile')],
        [InlineKeyboardButton("🏠 Головне меню", callback_data='back_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_profile(query, context):
    """Показати профіль"""
    user_id = query.from_user.id
    user = db.get_user(user_id)
    ref_earnings = db.get_referral_earnings(user_id)
    
    ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
    
    text = f"""
👤 **Мій Профіль**

📊 **Статистика:**
• Баланс: {user['balance']} ⭐
• Всього спінів: {user['total_spins']}
• Виграно: {user['total_won']} ⭐

👥 **Рефералки:**
• Бонус за запрошення: {ref_earnings['total_bonus']} ⭐
• Бонус за поповнення: {ref_earnings['total_deposit_bonus']} ⭐
• Всього від рефералів: {ref_earnings['total_bonus'] + ref_earnings['total_deposit_bonus']} ⭐

🔗 **Ваше реф-посилання:**
`{ref_link}`
    """
    
    keyboard = [
        [InlineKeyboardButton("👥 Мої реферали", callback_data='referrals')],
        [InlineKeyboardButton("📋 Останні спіни", callback_data='recent_spins')],
        [InlineKeyboardButton("↩️ Назад", callback_data='back_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_referrals(query, context):
    """Показати рефералів"""
    user_id = query.from_user.id
    referrals = db.get_referrals(user_id)
    
    if not referrals:
        text = "👥 **У вас ще немає рефералів**\n\nПоділіться посиланням з друзями!"
    else:
        text = f"👥 **Ваші реферали** ({len(referrals)}):\n\n"
        for i, ref in enumerate(referrals, 1):
            text += f"{i}. @{ref['username'] or 'Unknown'} - Баланс: {ref['balance']} ⭐\n"
    
    keyboard = [
        [InlineKeyboardButton("👤 Профіль", callback_data='profile')],
        [InlineKeyboardButton("↩️ Назад", callback_data='back_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_leaderboard(query, context):
    """Показати лідерборд"""
    leaderboard = db.get_leaderboard(10)
    
    text = "🏆 **Топ 10 Гравців**\n\n"
    
    medals = ['🥇', '🥈', '🥉']
    for i, user in enumerate(leaderboard, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        text += f"{medal} @{user['username'] or 'Unknown'} - {user['balance']} ⭐\n"
    
    keyboard = [[InlineKeyboardButton("↩️ Назад", callback_data='back_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(query, context):
    """Повернутися в меню"""
    keyboard = [
        [InlineKeyboardButton("🎡 Крутити колесо", callback_data='spin_menu')],
        [InlineKeyboardButton("👤 Мій профіль", callback_data='profile')],
        [InlineKeyboardButton("👥 Мої реферали", callback_data='referrals')],
        [InlineKeyboardButton("🏆 Лідерборд", callback_data='leaderboard')],
        [InlineKeyboardButton("❓ Допомога", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎡 Ласкаво просимо в **Spin Wheel Game**!\n\nОберіть дію:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== ОСНОВНА ФУНКЦІЯ ==========

async def error_handler(update, context):
    """Обробник помилок"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    """Запуск бота"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Команди
    application.add_handler(CommandHandler('start', start, pass_args=True))
    application.add_handler(CommandHandler('help', help_command))
    
    # Кнопки
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='back_menu'))
    
    # Помилки
    application.add_error_handler(error_handler)
    
    print("🚀 Бот запущено!")
    print(f"Слухаю токен: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    application.run_polling()

if __name__ == '__main__':
    main()