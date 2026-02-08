import aiosqlite

class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_file)
        self.cursor = await self.connection.cursor()

    async def close(self):
        await self.cursor.close()
        await self.connection.close()

    async def setup_tables(self):
        # Create levels table
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS levels (
            user_id TEXT,
            guild_id TEXT,
            xp INTEGER,
            level INTEGER,
            total_messages INTEGER,
            last_xp_time TIMESTAMP
        )''')

        # Create economy table
        await self.connection.execute('''CREATE TABLE IF NOT EXISTS economy (
            user_id TEXT,
            guild_id TEXT,
            balance INTEGER,
            last_daily TIMESTAMP,
            last_work TIMESTAMP
        )''')
        await self.connection.commit()

    async def add_xp(self, user_id, guild_id, xp):
        # Method to add XP to a user
        await self.connection.execute('''INSERT INTO levels (user_id, guild_id, xp, total_messages, last_xp_time) VALUES (?, ?, ?, 1, datetime('now'))
        ON CONFLICT(user_id, guild_id) DO UPDATE SET xp = xp + ?, total_messages = total_messages + 1, last_xp_time = datetime('now')''', (user_id, guild_id, xp, xp))
        await self.connection.commit()

    async def get_user_level_data(self, user_id, guild_id):
        # Method to get level data for a user
        await self.cursor.execute('SELECT xp, level, total_messages FROM levels WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
        return await self.cursor.fetchone()

    async def update_level(self, user_id, guild_id):
        # Method to update a user's level based on XP
        user_data = await self.get_user_level_data(user_id, guild_id)
        if user_data:
            xp, level, total_messages = user_data
            new_level = int(xp // 100)  # Example level-up condition
            if new_level > level:
                await self.connection.execute('UPDATE levels SET level = ? WHERE user_id = ? AND guild_id = ?', (new_level, user_id, guild_id))
                await self.connection.commit()

    async def get_top_users(self, guild_id, limit=10):
        # Method to retrieve top users by XP
        await self.cursor.execute('SELECT user_id, xp FROM levels WHERE guild_id = ? ORDER BY xp DESC LIMIT ?', (guild_id, limit))
        return await self.cursor.fetchall()

    async def get_balance(self, user_id, guild_id):
        # Method to get the balance for a user
        await self.cursor.execute('SELECT balance FROM economy WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
        return await self.cursor.fetchone()

    async def add_money(self, user_id, guild_id, amount):
        # Method to add money to a user's balance
        await self.connection.execute('''INSERT INTO economy (user_id, guild_id, balance) VALUES (?, ?, ?) ON CONFLICT(user_id, guild_id) DO UPDATE SET balance = balance + ?''', (user_id, guild_id, amount, amount))
        await self.connection.commit()

    async def remove_money(self, user_id, guild_id, amount):
        # Method to remove money from a user's balance
        await self.connection.execute('''UPDATE economy SET balance = balance - ? WHERE user_id = ? AND guild_id = ? AND balance >= ?''', (amount, user_id, guild_id, amount))
        await self.connection.commit()

    async def get_last_daily(self, user_id, guild_id):
        # Method to get last daily claim time
        await self.cursor.execute('SELECT last_daily FROM economy WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
        return await self.cursor.fetchone()

    async def update_last_daily(self, user_id, guild_id):
        # Method to update last daily claim time
        await self.connection.execute('UPDATE economy SET last_daily = datetime('now') WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
        await self.connection.commit()

    async def get_last_work(self, user_id, guild_id):
        # Method to get last work claim time
        await self.cursor.execute('SELECT last_work FROM economy WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
        return await self.cursor.fetchone()

    async def update_last_work(self, user_id, guild_id):
        # Method to update last work claim time
        await self.connection.execute('UPDATE economy SET last_work = datetime('now') WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
        await self.connection.commit()

    async def get_richest_users(self, guild_id, limit=10):
        # Method to retrieve the richest users by balance
        await self.cursor.execute('SELECT user_id, balance FROM economy WHERE guild_id = ? ORDER BY balance DESC LIMIT ?', (guild_id, limit))
        return await self.cursor.fetchall()
