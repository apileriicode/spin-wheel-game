import random
from config import SPIN_MULTIPLIERS

def get_random_multiplier():
    """Отримати випадковий множник"""
    return random.choice(SPIN_MULTIPLIERS)

def format_currency(amount: int, currency: str = 'STARS') -> str:
    """Форматувати валюту"""
    if currency == 'STARS':
        return f"{amount} ⭐"
    elif currency == 'TON':
        return f"{amount} TON"
    elif currency == 'USDT':
        return f"${amount}"
    return f"{amount} {currency}"

def validate_bet(amount: int) -> tuple[bool, str]:
    """Перевірити ставку"""
    from config import SPIN_MIN_BET, SPIN_MAX_BET
    
    if amount < SPIN_MIN_BET:
        return False, f"Мінімальна ставка: {SPIN_MIN_BET}"
    if amount > SPIN_MAX_BET:
        return False, f"Максимальна ставка: {SPIN_MAX_BET}"
    return True, "OK"

def calculate_referral_link(user_id: int, bot_username: str) -> str:
    """Розрахувати реф-посилання"""
    return f"https://t.me/{bot_username}?start={user_id}"