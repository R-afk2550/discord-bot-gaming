import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.initialize()

    def initialize(self):
        # Existing table creation
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS warnings ...''')  # Existing warnings table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_profiles ...''')  # Existing user profiles table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS events ...''')  # Existing events table
        # New levels table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS levels (
            user_id TEXT,
            guild_id TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            total_messages INTEGER DEFAULT 0,
            last_xp_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )''')
        # New economy table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS economy (
            user_id TEXT,
            guild_id TEXT,
            balance INTEGER DEFAULT 0,
            last_daily DATETIME,
            last_work DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )''')
        self.connection.commit()

    async def add_xp(self, user_id, guild_id, xp_amount):
        self.cursor.execute('''UPDATE levels SET xp = xp + ?, total_messages = total_messages + 1,
                              last_xp_time = ? WHERE user_id = ? AND guild_id = ?''',
                            (xp_amount, datetime.now(), user_id, guild_id))
        self.connection.commit()

    async def get_user_level_data(self, user_id, guild_id):
        self.cursor.execute('''SELECT * FROM levels WHERE user_id = ? AND guild_id = ?''', (user_id, guild_id))
        return self.cursor.fetchone()

    async def update_level(self, user_id, guild_id, new_level):
        self.cursor.execute('''UPDATE levels SET level = ? WHERE user_id = ? AND guild_id = ?''',
                            (new_level, user_id, guild_id))
        self.connection.commit()

    async def get_top_users(self, guild_id, limit=10):
        self.cursor.execute('''SELECT user_id, guild_id, xp FROM levels WHERE guild_id = ? ORDER BY xp DESC LIMIT ?''',
                            (guild_id, limit))
        return self.cursor.fetchall()

    async def get_balance(self, user_id, guild_id):
        self.cursor.execute('''SELECT balance FROM economy WHERE user_id = ? AND guild_id = ?''',
                            (user_id, guild_id))
        return self.cursor.fetchone()  # returns (balance,)

    async def add_money(self, user_id, guild_id, amount):
        self.cursor.execute('''UPDATE economy SET balance = balance + ? WHERE user_id = ? AND guild_id = ?''',
                            (amount, user_id, guild_id))
        self.connection.commit()

    async def remove_money(self, user_id, guild_id, amount):
        self.cursor.execute('''UPDATE economy SET balance = balance - ? WHERE user_id = ? AND guild_id = ?''',
                            (amount, user_id, guild_id))
        if self.cursor.rowcount < 0:
            return False  # Insufficient funds
        self.connection.commit()
        return True

    async def get_last_daily(self, user_id, guild_id):
        self.cursor.execute('''SELECT last_daily FROM economy WHERE user_id = ? AND guild_id = ?''',
                            (user_id, guild_id))
        return self.cursor.fetchone()  # returns (last_daily,)

    async def update_last_daily(self, user_id, guild_id):
        self.cursor.execute('''UPDATE economy SET last_daily = ? WHERE user_id = ? AND guild_id = ?''',
                            (datetime.now(), user_id, guild_id))
        self.connection.commit()

    async def get_last_work(self, user_id, guild_id):
        self.cursor.execute('''SELECT last_work FROM economy WHERE user_id = ? AND guild_id = ?''',
                            (user_id, guild_id))
        return self.cursor.fetchone()  # returns (last_work,)

    async def update_last_work(self, user_id, guild_id):
        self.cursor.execute('''UPDATE economy SET last_work = ? WHERE user_id = ? AND guild_id = ?''',
                            (datetime.now(), user_id, guild_id))
        self.connection.commit()

    async def get_richest_users(self, guild_id, limit=10):
        self.cursor.execute('''SELECT user_id, guild_id, balance FROM economy WHERE guild_id = ? ORDER BY balance DESC LIMIT ?''',
                            (guild_id, limit))
        return self.cursor.fetchall()