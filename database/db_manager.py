import aiosqlite
import logging
from typing import List, Dict, Optional
from datetime import datetime

DATABASE_NAME = 'your_database_name_here'  # Update with actual database name

class DatabaseManager:
    def __init__(self):
        self.db_name = DATABASE_NAME

    async def initialize(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('CREATE TABLE IF NOT EXISTS warnings (user_id TEXT, warning TEXT)')
            await db.execute('CREATE TABLE IF NOT EXISTS user_profiles (user_id TEXT, profile_data TEXT)')
            await db.execute('CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY, event_data TEXT)')
            await db.execute('CREATE TABLE IF NOT EXISTS levels (user_id TEXT, level INTEGER, xp INTEGER)')
            await db.execute('CREATE TABLE IF NOT EXISTS economy (user_id TEXT, balance INTEGER)')
            await db.commit()

    async def add_warning(self, user_id: str, warning: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('INSERT INTO warnings (user_id, warning) VALUES (?, ?)', (user_id, warning))
            await db.commit()

    async def get_warnings(self, user_id: str) -> List[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT * FROM warnings WHERE user_id = ?', (user_id,)) as cursor:
                return [dict(row) for row in cursor]

    async def get_warning_count(self, user_id: str) -> int:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT COUNT(*) FROM warnings WHERE user_id = ?', (user_id,)) as cursor:
                count = await cursor.fetchone()
                return count[0] if count else 0

    async def update_user_games(self, user_id: str, games: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE user_profiles SET profile_data = ? WHERE user_id = ?', (games, user_id))
            await db.commit()

    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,)) as cursor:
                return dict(await cursor.fetchone()) if cursor else None

    async def create_event(self, event_data: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('INSERT INTO events (event_data) VALUES (?)', (event_data,))
            await db.commit()

    async def get_upcoming_events(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT * FROM events WHERE event_data > ?', (datetime.now(),)) as cursor:
                return [dict(row) for row in cursor]

    async def get_events_to_notify(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT * FROM events WHERE event_data <= ?', (datetime.now(),)) as cursor:
                return [dict(row) for row in cursor]

    async def mark_event_notified(self, event_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('DELETE FROM events WHERE event_id = ?', (event_id,))
            await db.commit()

    async def add_xp(self, user_id: str, xp: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE levels SET xp = xp + ? WHERE user_id = ?', (xp, user_id))
            await db.commit()

    async def get_user_level_data(self, user_id: str) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT * FROM levels WHERE user_id = ?', (user_id,)) as cursor:
                return dict(await cursor.fetchone()) if cursor else None

    async def update_level(self, user_id: str, level: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE levels SET level = ? WHERE user_id = ?', (level, user_id))
            await db.commit()

    async def get_top_users(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT user_id, level FROM levels ORDER BY level DESC LIMIT 10') as cursor:
                return [dict(row) for row in cursor]

    async def get_balance(self, user_id: str) -> Optional[int]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT balance FROM economy WHERE user_id = ?', (user_id,)) as cursor:
                balance = await cursor.fetchone()
                return balance[0] if balance else None

    async def add_money(self, user_id: str, amount: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE economy SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            await db.commit()

    async def remove_money(self, user_id: str, amount: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE economy SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
            await db.commit()

    async def get_last_daily(self, user_id: str) -> Optional[datetime]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT last_daily FROM economy WHERE user_id = ?', (user_id,)) as cursor:
                last_daily = await cursor.fetchone()
                return last_daily[0] if last_daily else None

    async def update_last_daily(self, user_id: str, last_daily: datetime):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE economy SET last_daily = ? WHERE user_id = ?', (last_daily, user_id))
            await db.commit()

    async def get_last_work(self, user_id: str) -> Optional[datetime]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT last_work FROM economy WHERE user_id = ?', (user_id,)) as cursor:
                last_work = await cursor.fetchone()
                return last_work[0] if last_work else None

    async def update_last_work(self, user_id: str, last_work: datetime):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE economy SET last_work = ? WHERE user_id = ?', (last_work, user_id))
            await db.commit()

    async def get_richest_users(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT user_id, balance FROM economy ORDER BY balance DESC LIMIT 10') as cursor:
                return [dict(row) for row in cursor]

# Global instance
# Replace `your_database_name_here` with the actual database name used in the config settings.
db_manager = DatabaseManager()