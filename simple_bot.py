import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import random
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проста таблиця даних (в памяті)
users_data = {}

# ========== КОМАНДИ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Ініціалізувати користувача
    if user_id not in users_data:
        users_data[user_id] = {
            'username': username,
            'balance': 1000,  # Стартовий баланс
            'referrals': 0,
            'total_earned': 0
        }
    
    keyboard = [
        [InlineKeyboardButton("🎡 Грати", callback_data='play')],
        [InlineKeyboardButton("💵 Мій баланс", callback_data='balance')],
        [InlineKeyboardButton("👥 Мої реферали", callback_data='referrals')],
        [InlineKeyboardButton("❓ Допомога", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎡 **Ласкаво просимо!**\n\n"
        f"💵 Ваш баланс: {users_data[user_id]['balance']} ⭐\n\n"
        f"Оберіть дію:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = users_data[user_id]
    
    await query.answer()
    
    if query.data == 'play':
        # Можливі гри
        games = [
            {
                'name': '🎡 Кликните кнопку 🔘',
                'reward': random.randint(10, 100),
                'callback': 'game_click'
            },
            {
                'name': '🎢 Вагайте й кликніть',
                'reward': random.randint(20, 150),
                'callback': 'game_wait'
            },
            {
                'name': '🎰 Крутнути колесо',
                'reward': random.randint(50, 500),
                'callback': 'game_spin'
            }
        ]
        
        keyboard = []
        for game in games:
            keyboard.append([InlineKeyboardButton(game['name'], callback_data=game['callback'])])
        keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='back')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🎡 **Оберіть гру:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == 'game_click':
        reward = random.randint(10, 100)
        user['balance'] += reward
        user['total_earned'] += reward
        await query.edit_message_text(
            f"🎁 **Повідомлення!**\n\n"
            f"🎆 Ви виграли: **{reward} ⭐**\n\n"
            f💵 Новий баланс: {user['balance']} ⭐",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data='play')]]),
            parse_mode='Markdown'
        )
    
    elif query.data == 'game_wait':
        reward = random.randint(20, 150)
        user['balance'] += reward
        user['total_earned'] += reward
        await query.edit_message_text(
            f"🎁 **Повідомлення!**\n\n"
            f"🎆 Ви виграли: **{reward} ⭐**\n\n"
            f💵 Новий баланс: {user['balance']} ⭐",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data='play')]]),
            parse_mode='Markdown'
        )
    
    elif query.data == 'game_spin':
        multiplier = random.choice([0.5, 1.0, 1.5, 2.0, 3.0, 5.0])
        bet = 100
        reward = int(bet * multiplier)
        
        if user['balance'] >= bet:
            user['balance'] -= bet
            user['balance'] += reward
            user['total_earned'] += reward
            
            result_text = "🎁 Виграли!" if reward > bet else "😢 Програли..."
            
            await query.edit_message_text(
                f"🎰 **Колесо врталося!**\n\n"
                f"{result_text}\n\n"
                f"💰 Множник: x{multiplier}\n"
                f"🎁 Приз: {reward} ⭐\n\n"
                f💵 Новий баланс: {user['balance']} ⭐",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data='play')]]),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Недостатньо монет для гри!\n"
                f"Необхідно: 100 ⭐, У вас: {user['balance']} ⭐",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data='play')]]),
                parse_mode='Markdown'
            )
    
    elif query.data == 'balance':
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(
            f"💵 **Мій Баланс**\n\n"
            f"💵 Баланс: {user['balance']} ⭐\n"
            f"🎆 Всього зароблено: {user['total_earned']} ⭐\n"
            f"👥 Рефералів: {user['referrals']}\n\n"
            f"🔗 Одержувати тиснуття: `{ref_link}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data='back')]]),
            parse_mode='Markdown'
        )
    
    elif query.data == 'referrals':
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(
            f"👥 **Мої Реферали**\n\n"
            f"👥 Всього рефералів: {user['referrals']}\n"
            f"💵 Отримано від рефералів: +100 ⭐\n\n"
            f"🔗 Поділіться:\n`{ref_link}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data='back')]]),
            parse_mode='Markdown'
        )
    
    elif query.data == 'help':
        await query.edit_message_text(
            "🚀 **Как грати?**\n\n"
            "1️⃣ Кликніть НОВИ\u0425 гро\n"
            "2️⃣ Отримайте усі ⭐\n"
            "3️⃣ Поділіться с друзями + 100⭐\n\n"
            "💰 Точния: Монети та нічий вивод (😉 право)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Назад", callback_data='back')]]),
            parse_mode='Markdown'
        )
    
    elif query.data == 'back':
        user = users_data[user_id]
        keyboard = [
            [InlineKeyboardButton("🎡 Грати", callback_data='play')],
            [InlineKeyboardButton("💵 Мій баланс", callback_data='balance')],
            [InlineKeyboardButton("👥 Мої реферали", callback_data='referrals')],
            [InlineKeyboardButton("❓ Допомога", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎡 **Ласкаво просимо!**\n\n"
            f"💵 Ваш баланс: {user['balance']} ⭐\n\n"
            f"Оберіть дію:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def main():
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 Бот запущено!")
    application.run_polling()

if __name__ == '__main__':
    main()
