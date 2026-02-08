import sqlite3

class DatabaseManager():
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    async def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            warning_reason TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            level INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            event_name TEXT NOT NULL,
            event_date TIMESTAMP NOT NULL
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS levels (
            id INTEGER PRIMARY KEY,
            level_name TEXT NOT NULL,
            exp_needed INTEGER NOT NULL
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS economy (
            id INTEGER PRIMARY KEY,
            user_id TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        self.conn.commit()

    async def add_warning(self, user_id, warning_reason):
        self.cursor.execute('INSERT INTO warnings (user_id, warning_reason) VALUES (?, ?)', (user_id, warning_reason))
        self.conn.commit()

    async def get_warnings(self, user_id):
        self.cursor.execute('SELECT * FROM warnings WHERE user_id = ?', (user_id,))
        return self.cursor.fetchall()

    async def add_user_profile(self, user_id, username):
        self.cursor.execute('INSERT INTO user_profiles (user_id, username) VALUES (?, ?)', (user_id, username))
        self.conn.commit()

    async def get_user_profile(self, user_id):
        self.cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()

    async def add_event(self, event_name, event_date):
        self.cursor.execute('INSERT INTO events (event_name, event_date) VALUES (?, ?)', (event_name, event_date))
        self.conn.commit()

    async def get_events(self):
        self.cursor.execute('SELECT * FROM events')
        return self.cursor.fetchall()

    async def add_level(self, level_name, exp_needed):
        self.cursor.execute('INSERT INTO levels (level_name, exp_needed) VALUES (?, ?)', (level_name, exp_needed))
        self.conn.commit()

    async def get_levels(self):
        self.cursor.execute('SELECT * FROM levels')
        return self.cursor.fetchall()

    async def update_balance(self, user_id, amount):
        self.cursor.execute('UPDATE economy SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()

    async def get_balance(self, user_id):
        self.cursor.execute('SELECT balance FROM economy WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()

# Create a db_manager instance
if __name__ == '__main__':
    db_manager = DatabaseManager('my_database.db')
    import asyncio
    asyncio.run(db_manager.create_tables())