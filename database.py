import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_path: str = 'spin_wheel.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Ініціалізація бази даних"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблиця користувачів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                total_spins INTEGER DEFAULT 0,
                total_won INTEGER DEFAULT 0,
                total_lost INTEGER DEFAULT 0,
                referrer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_spin TIMESTAMP
            )
        ''')
        
        # Таблиця рефералів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                bonus_given INTEGER DEFAULT 0,
                deposit_bonus INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблиця спінів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                bet_amount INTEGER,
                multiplier REAL,
                winnings INTEGER,
                currency TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблиця транзакцій
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                currency TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Отримати з'єднання з БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========== КОРИСТУВАЧІ ==========
    
    def create_user(self, user_id: int, username: str, referrer_id: Optional[int] = None) -> bool:
        """Створити нового користувача"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (user_id, username, referrer_id, balance)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, referrer_id, 100))  # Стартовий бонус 100 зірок
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Отримати користувача"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def update_balance(self, user_id: int, amount: int, operation: str = 'add'):
        """Оновити баланс користувача"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if operation == 'add':
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        elif operation == 'subtract':
            cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
        
        conn.commit()
        conn.close()
    
    # ========== РЕФЕРАЛЫ ==========
    
    def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Додати реферала"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id, bonus_given)
                VALUES (?, ?, 1)
            ''', (referrer_id, referred_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_referrals(self, user_id: int) -> List[Dict]:
        """Отримати список рефералів користувача"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, u.username, u.balance 
            FROM referrals r 
            JOIN users u ON r.referred_id = u.user_id 
            WHERE r.referrer_id = ?
        ''', (user_id,))
        referrals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return referrals
    
    def get_referral_earnings(self, user_id: int) -> Dict:
        """Отримати заробітки на рефералах"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                SUM(bonus_given) as total_bonus,
                SUM(deposit_bonus) as total_deposit_bonus
            FROM referrals 
            WHERE referrer_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return {
            'total_bonus': result['total_bonus'] or 0,
            'total_deposit_bonus': result['total_deposit_bonus'] or 0
        }
    
    # ========== СПІНИ ==========
    
    def record_spin(self, user_id: int, bet: int, multiplier: float, winnings: int, currency: str):
        """Записати спін"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO spins (user_id, bet_amount, multiplier, winnings, currency)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, bet, multiplier, winnings, currency))
        
        cursor.execute('''
            UPDATE users 
            SET total_spins = total_spins + 1,
                total_won = total_won + ?,
                last_spin = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (winnings, user_id))
        
        conn.commit()
        conn.close()
    
    def get_user_spins(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Отримати останні спіни користувача"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM spins 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        spins = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return spins
    
    # ========== ЛІДЕРБОРД ==========
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Отримати л��дерборд"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, balance, total_spins, total_won
            FROM users 
            ORDER BY balance DESC 
            LIMIT ?
        ''', (limit,))
        leaderboard = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leaderboard
    
    # ========== ТРАНСАКЦІЇ ==========
    
    def add_transaction(self, user_id: int, amount: int, tx_type: str, currency: str, description: str):
        """Додати транзакцію"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, currency, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, tx_type, currency, description))
        
        conn.commit()
        conn.close()