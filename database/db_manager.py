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


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()
