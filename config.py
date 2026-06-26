import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Database
DATABASE_URL = 'sqlite:///spin_wheel.db'

# Game Settings
SPIN_MIN_BET = 1  # Мінімум 1 зірка
SPIN_MAX_BET = 999999999  # Максимум 999,999,999 зірок
SPIN_MULTIPLIERS = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]  # Можливі множники виграшу

# Referral System
REFERRAL_BONUS = 3  # Бонус за запрошення друга
REFERRAL_DEPOSIT_BONUS = 2  # Бонус якщо друг поповнить

# Supported Currencies
SUPPORTED_CURRENCIES = ['TON', 'USDT', 'STARS']  # Telegram Stars

# Admin Settings
ADMIN_IDS = []

# Debug
DEBUG = os.getenv('DEBUG', 'False') == 'True'