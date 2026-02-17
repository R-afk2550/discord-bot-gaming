"""
Gestor de base de datos SQLite para el bot
"""
import aiosqlite
import logging
from typing import List, Dict, Optional
from datetime import datetime
from config.settings import DATABASE_NAME

logger = logging.getLogger('discord_bot')


class DatabaseManager:
    """Gestor de la base de datos SQLite"""
    
    def __init__(self):
        self.db_name = DATABASE_NAME
    
    async def initialize(self):
        """Inicializa la base de datos y crea las tablas necesarias"""
        async with aiosqlite.connect(self.db_name) as db:
            # Tabla de advertencias
            await db.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de perfiles de usuarios
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    games TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de eventos
            await db.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    creator_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    event_date DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT 0
                )
            ''')
            
            # Tabla de niveles y XP
            await db.execute('''
                CREATE TABLE IF NOT EXISTS levels (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    total_messages INTEGER DEFAULT 0,
                    last_xp_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                )
            ''')
            
            # Tabla de economía
            await db.execute('''
                CREATE TABLE IF NOT EXISTS economy (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    balance INTEGER DEFAULT 0,
                    last_daily DATETIME,
                    last_work DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                )
            ''')
            
            # Tabla de sesiones de loot de Tibia
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tibia_loot_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    creator_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    closed BOOLEAN DEFAULT 0
                )
            ''')
            
            # Tabla de items de loot de Tibia
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tibia_loot_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    value INTEGER NOT NULL,
                    added_by INTEGER NOT NULL,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES tibia_loot_sessions (id)
                )
            ''')
            
            # Tabla de participantes de sesiones de Tibia
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tibia_loot_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, user_id),
                    FOREIGN KEY (session_id) REFERENCES tibia_loot_sessions (id)
                )
            ''')
            
            await db.commit()
            logger.info("Base de datos inicializada correctamente")
    
    # ===== MÉTODOS PARA ADVERTENCIAS =====
    
    async def add_warning(self, user_id: int, guild_id: int, moderator_id: int, reason: str):
        """Añade una advertencia a un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'INSERT INTO warnings (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)',
                (user_id, guild_id, moderator_id, reason)
            )
            await db.commit()
            logger.info(f"Advertencia añadida para usuario {user_id}")
    
    async def get_warnings(self, user_id: int, guild_id: int) -> List[Dict]:
        """Obtiene todas las advertencias de un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM warnings WHERE user_id = ? AND guild_id = ? ORDER BY timestamp DESC',
                (user_id, guild_id)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_warning_count(self, user_id: int, guild_id: int) -> int:
        """Obtiene el número total de advertencias de un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    # ===== MÉTODOS PARA PERFILES DE USUARIOS =====
    
    async def update_user_games(self, user_id: int, guild_id: int, games: str):
        """Actualiza los juegos de un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO user_profiles (user_id, guild_id, games, updated_at) 
                   VALUES (?, ?, ?, ?) 
                   ON CONFLICT(user_id) DO UPDATE SET games = ?, updated_at = ?''',
                (user_id, guild_id, games, datetime.now(), games, datetime.now())
            )
            await db.commit()
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Obtiene el perfil de un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM user_profiles WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    # ===== MÉTODOS PARA EVENTOS =====
    
    async def create_event(self, guild_id: int, creator_id: int, title: str, 
                          description: str, event_date: datetime):
        """Crea un nuevo evento"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO events (guild_id, creator_id, title, description, event_date) 
                   VALUES (?, ?, ?, ?, ?)''',
                (guild_id, creator_id, title, description, event_date)
            )
            await db.commit()
            logger.info(f"Evento creado: {title}")
    
    async def get_upcoming_events(self, guild_id: int) -> List[Dict]:
        """Obtiene todos los eventos futuros de un servidor"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT * FROM events 
                   WHERE guild_id = ? AND event_date > datetime('now') 
                   ORDER BY event_date ASC''',
                (guild_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_events_to_notify(self) -> List[Dict]:
        """Obtiene eventos que necesitan notificación (1 hora antes)"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT * FROM events 
                   WHERE notified = 0 
                   AND datetime(event_date, '-1 hour') <= datetime('now')
                   AND event_date > datetime('now')''' 
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def mark_event_notified(self, event_id: int):
        """Marca un evento como notificado"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE events SET notified = 1 WHERE id = ?',
                (event_id,)
            )
            await db.commit()
    
    # ===== MÉTODOS PARA NIVELES Y XP =====
    
    async def add_xp(self, user_id: int, guild_id: int, xp_amount: int):
        """Añade XP a un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO levels (user_id, guild_id, xp, total_messages, last_xp_time) 
                   VALUES (?, ?, ?, 1, ?) 
                   ON CONFLICT(user_id, guild_id) DO UPDATE SET 
                   xp = xp + ?,
                   total_messages = total_messages + 1,
                   last_xp_time = ?''',
                (user_id, guild_id, xp_amount, datetime.now(), xp_amount, datetime.now())
            )
            await db.commit()
    
    async def get_user_level_data(self, user_id: int, guild_id: int) -> Optional[Dict]:
        """Obtiene los datos de nivel de un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM levels WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_level(self, user_id: int, guild_id: int, new_level: int):
        """Actualiza el nivel de un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE levels SET level = ? WHERE user_id = ? AND guild_id = ?',
                (new_level, user_id, guild_id)
            )
            await db.commit()
    
    async def get_top_users(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Obtiene el top de usuarios por XP"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM levels WHERE guild_id = ? ORDER BY xp DESC LIMIT ?',
                (guild_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    # ===== MÉTODOS PARA ECONOMÍA =====
    
    async def get_balance(self, user_id: int, guild_id: int) -> int:
        """Obtiene el balance de un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT balance FROM economy WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def add_money(self, user_id: int, guild_id: int, amount: int):
        """Añade dinero a un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO economy (user_id, guild_id, balance) 
                   VALUES (?, ?, ?) 
                   ON CONFLICT(user_id, guild_id) DO UPDATE SET 
                   balance = balance + ?''',
                (user_id, guild_id, amount, amount)
            )
            await db.commit()
    
    async def remove_money(self, user_id: int, guild_id: int, amount: int) -> bool:
        """Quita dinero a un usuario"""
        balance = await self.get_balance(user_id, guild_id)
        if balance < amount:
            return False
        
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE economy SET balance = balance - ? WHERE user_id = ? AND guild_id = ?',
                (amount, user_id, guild_id)
            )
            await db.commit()
        return True
    
    async def get_last_daily(self, user_id: int, guild_id: int) -> Optional[str]:
        """Obtiene la última vez que el usuario usó /daily"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT last_daily FROM economy WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def update_last_daily(self, user_id: int, guild_id: int):
        """Actualiza el timestamp de /daily"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO economy (user_id, guild_id, last_daily) 
                   VALUES (?, ?, ?) 
                   ON CONFLICT(user_id, guild_id) DO UPDATE SET 
                   last_daily = ?''',
                (user_id, guild_id, datetime.now().isoformat(), datetime.now().isoformat())
            )
            await db.commit()
    
    async def get_last_work(self, user_id: int, guild_id: int) -> Optional[str]:
        """Obtiene la última vez que el usuario usó /work"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT last_work FROM economy WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def update_last_work(self, user_id: int, guild_id: int):
        """Actualiza el timestamp de /work"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO economy (user_id, guild_id, last_work) 
                   VALUES (?, ?, ?) 
                   ON CONFLICT(user_id, guild_id) DO UPDATE SET 
                   last_work = ?''',
                (user_id, guild_id, datetime.now().isoformat(), datetime.now().isoformat())
            )
            await db.commit()
    
    async def get_richest_users(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Obtiene el top de usuarios más ricos"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM economy WHERE guild_id = ? ORDER BY balance DESC LIMIT ?',
                (guild_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    # ===== MÉTODOS PARA LOOT DE TIBIA =====
    
    async def create_tibia_loot_session(self, guild_id: int, channel_id: int, creator_id: int) -> int:
        """Crea una nueva sesión de loot de Tibia y retorna el ID"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                'INSERT INTO tibia_loot_sessions (guild_id, channel_id, creator_id) VALUES (?, ?, ?)',
                (guild_id, channel_id, creator_id)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_active_tibia_session(self, channel_id: int) -> Optional[Dict]:
        """Obtiene la sesión activa de loot en un canal"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM tibia_loot_sessions WHERE channel_id = ? AND closed = 0 ORDER BY created_at DESC LIMIT 1',
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def add_tibia_loot_item(self, session_id: int, item_name: str, quantity: int, value: int, added_by: int):
        """Añade un item al loot de Tibia"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'INSERT INTO tibia_loot_items (session_id, item_name, quantity, value, added_by) VALUES (?, ?, ?, ?, ?)',
                (session_id, item_name, quantity, value, added_by)
            )
            await db.commit()
    
    async def get_tibia_loot_items(self, session_id: int) -> List[Dict]:
        """Obtiene todos los items de loot de una sesión"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM tibia_loot_items WHERE session_id = ? ORDER BY added_at ASC',
                (session_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def add_tibia_participant(self, session_id: int, user_id: int):
        """Añade un participante a una sesión de loot (ignora si ya existe)"""
        async with aiosqlite.connect(self.db_name) as db:
            try:
                await db.execute(
                    'INSERT INTO tibia_loot_participants (session_id, user_id) VALUES (?, ?)',
                    (session_id, user_id)
                )
                await db.commit()
            except aiosqlite.IntegrityError:
                # El participante ya existe, ignorar silenciosamente
                pass
    
    async def get_tibia_participants(self, session_id: int) -> List[Dict]:
        """Obtiene todos los participantes de una sesión"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM tibia_loot_participants WHERE session_id = ? ORDER BY added_at ASC',
                (session_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def close_tibia_session(self, session_id: int):
        """Cierra una sesión de loot"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE tibia_loot_sessions SET closed = 1 WHERE id = ?',
                (session_id,)
            )
            await db.commit()


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()