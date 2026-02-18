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
            
            # Tabla de loots de Tibia
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tibia_loots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    boss_name TEXT NOT NULL,
                    items TEXT NOT NULL,
                    value INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de códigos de acceso residencial
            await db.execute('''
                CREATE TABLE IF NOT EXISTS residential_access_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    resident_name TEXT NOT NULL,
                    code_type TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expiry_date DATETIME,
                    location TEXT,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    revoked_at DATETIME,
                    use_count INTEGER DEFAULT 0
                )
            ''')
            
            # Tabla de historial de uso de códigos
            await db.execute('''
                CREATE TABLE IF NOT EXISTS access_code_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_id INTEGER NOT NULL,
                    used_by INTEGER NOT NULL,
                    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (code_id) REFERENCES residential_access_codes(id)
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
    
    # ===== MÉTODOS PARA TIBIA LOOTS =====
    
    async def add_tibia_loot(self, user_id: int, guild_id: int, boss_name: str, 
                            items: str, value: int):
        """Añade un registro de loot de Tibia"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO tibia_loots (user_id, guild_id, boss_name, items, value) 
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, guild_id, boss_name, items, value)
            )
            await db.commit()
            logger.info(f"Loot de Tibia registrado: {boss_name} - {value}gp")
    
    async def get_user_loots(self, user_id: int, guild_id: int, limit: int = 10) -> List[Dict]:
        """Obtiene el historial de loots de un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT * FROM tibia_loots 
                   WHERE user_id = ? AND guild_id = ? 
                   ORDER BY timestamp DESC LIMIT ?''',
                (user_id, guild_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_boss_stats(self, guild_id: int, boss_name: str = None) -> List[Dict]:
        """Obtiene estadísticas de drops por criatura"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            if boss_name:
                async with db.execute(
                    '''SELECT boss_name, COUNT(*) as kills, AVG(value) as avg_value, 
                       SUM(value) as total_value, MAX(value) as best_loot
                       FROM tibia_loots 
                       WHERE guild_id = ? AND boss_name = ?
                       GROUP BY boss_name''',
                    (guild_id, boss_name)
                ) as cursor:
                    row = await cursor.fetchone()
                    return [dict(row)] if row else []
            else:
                async with db.execute(
                    '''SELECT boss_name, COUNT(*) as kills, AVG(value) as avg_value, 
                       SUM(value) as total_value, MAX(value) as best_loot
                       FROM tibia_loots 
                       WHERE guild_id = ?
                       GROUP BY boss_name
                       ORDER BY kills DESC
                       LIMIT 10''',
                    (guild_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def get_top_loots(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Obtiene los mejores loots registrados"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT * FROM tibia_loots 
                   WHERE guild_id = ? 
                   ORDER BY value DESC LIMIT ?''',
                (guild_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_total_loot_value(self, user_id: int, guild_id: int) -> int:
        """Obtiene el valor total de loots ganados por un usuario"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT SUM(value) FROM tibia_loots WHERE user_id = ? AND guild_id = ?',
                (user_id, guild_id)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result and result[0] else 0
    
    # ===== MÉTODOS PARA CÓDIGOS DE ACCESO RESIDENCIAL =====
    
    async def create_access_code(
        self,
        guild_id: int,
        code: str,
        resident_name: str,
        code_type: str,
        created_by: int,
        expiry_date: Optional[datetime] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Crea un nuevo código de acceso residencial"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO residential_access_codes 
                   (guild_id, code, resident_name, code_type, created_by, 
                    expiry_date, location, notes) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (guild_id, code.upper(), resident_name, code_type, created_by,
                 expiry_date.isoformat() if expiry_date else None, location, notes)
            )
            await db.commit()
            logger.info(f"Código de acceso {code} creado para {resident_name}")
    
    async def get_access_code_by_code(
        self,
        guild_id: int,
        code: str
    ) -> Optional[Dict]:
        """Obtiene un código de acceso por su código"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT * FROM residential_access_codes 
                   WHERE guild_id = ? AND code = ?''',
                (guild_id, code.upper())
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_active_access_codes(
        self,
        guild_id: int,
        code_type: Optional[str] = None,
        resident_name: Optional[str] = None
    ) -> List[Dict]:
        """Obtiene todos los códigos de acceso activos"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            
            query = '''SELECT * FROM residential_access_codes 
                      WHERE guild_id = ? AND is_active = 1'''
            params = [guild_id]
            
            if code_type:
                query += ' AND code_type = ?'
                params.append(code_type)
            
            if resident_name:
                query += ' AND resident_name LIKE ?'
                params.append(f'%{resident_name}%')
            
            query += ' ORDER BY created_at DESC'
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def revoke_access_code(self, code_id: int):
        """Revoca un código de acceso"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''UPDATE residential_access_codes 
                   SET is_active = 0, revoked_at = ? 
                   WHERE id = ?''',
                (datetime.now().isoformat(), code_id)
            )
            await db.commit()
            logger.info(f"Código de acceso ID {code_id} revocado")
    
    async def register_access_code_use(self, code_id: int, used_by: int):
        """Registra el uso de un código de acceso"""
        async with aiosqlite.connect(self.db_name) as db:
            # Incrementar contador de usos
            await db.execute(
                '''UPDATE residential_access_codes 
                   SET use_count = use_count + 1 
                   WHERE id = ?''',
                (code_id,)
            )
            
            # Registrar en el historial
            await db.execute(
                '''INSERT INTO access_code_history (code_id, used_by) 
                   VALUES (?, ?)''',
                (code_id, used_by)
            )
            
            await db.commit()
            logger.info(f"Uso registrado para código ID {code_id} por usuario {used_by}")
    
    async def get_access_code_history(self, code_id: int) -> List[Dict]:
        """Obtiene el historial de uso de un código"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT * FROM access_code_history 
                   WHERE code_id = ? 
                   ORDER BY used_at DESC''',
                (code_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_expired_codes(self, guild_id: int) -> List[Dict]:
        """Obtiene códigos expirados que aún están activos"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT * FROM residential_access_codes 
                   WHERE guild_id = ? 
                   AND is_active = 1 
                   AND expiry_date IS NOT NULL 
                   AND expiry_date < ?''',
                (guild_id, datetime.now().isoformat())
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_access_code_stats(self, guild_id: int) -> Dict:
        """Obtiene estadísticas generales de códigos de acceso"""
        async with aiosqlite.connect(self.db_name) as db:
            stats = {}
            
            # Total de códigos activos
            async with db.execute(
                'SELECT COUNT(*) FROM residential_access_codes WHERE guild_id = ? AND is_active = 1',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                stats['active_codes'] = result[0] if result else 0
            
            # Total de códigos revocados
            async with db.execute(
                'SELECT COUNT(*) FROM residential_access_codes WHERE guild_id = ? AND is_active = 0',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                stats['revoked_codes'] = result[0] if result else 0
            
            # Total de usos
            async with db.execute(
                'SELECT SUM(use_count) FROM residential_access_codes WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                stats['total_uses'] = result[0] if result and result[0] else 0
            
            # Códigos temporales activos
            async with db.execute(
                '''SELECT COUNT(*) FROM residential_access_codes
                   WHERE guild_id = ? AND is_active = 1 AND code_type = 'temporal' ''',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                stats['temporal_codes'] = result[0] if result else 0
            
            # Códigos permanentes activos
            async with db.execute(
                '''SELECT COUNT(*) FROM residential_access_codes
                   WHERE guild_id = ? AND is_active = 1 AND code_type = 'permanente' ''',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                stats['permanent_codes'] = result[0] if result else 0
            
            return stats


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()