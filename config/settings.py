"""
Configuración centralizada del bot de Discord
"""
import os

# Intentar cargar dotenv solo si está disponible (local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # En Railway no necesitamos dotenv
    pass

# Token del bot (REQUERIDO)
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# IDs opcionales
GUILD_ID = os.getenv('GUILD_ID')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID')) if os.getenv('WELCOME_CHANNEL_ID') else None
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID')) if os.getenv('LOG_CHANNEL_ID') else None

# Prefijo de comandos
PREFIX = os.getenv('PREFIX', '/')

# Colores para embeds (formato hexadecimal)
COLORS = {
    'info': 0x3498db,      # Azul
    'success': 0x2ecc71,   # Verde
    'error': 0xe74c3c,     # Rojo
    'warning': 0xe67e22,   # Naranja
    'event': 0x9b59b6      # Morado
}

# Juegos disponibles
GAMES = {
    'LOL': {
        'name': 'League of Legends',
        'emoji': '🎮',
        'roles': ['Top', 'Jungle', 'Mid', 'ADC', 'Support'],
        'ranks': ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Challenger']
    },
    'WoW': {
        'name': 'World of Warcraft',
        'emoji': '⚔️',
        'roles': ['Tank', 'Healer', 'DPS'],
        'types': ['Raid', 'Mythic+', 'PvP', 'Arena', 'Dungeons']
    },
    'Minecraft': {
        'name': 'Minecraft',
        'emoji': '⛏️',
        'types': ['Survival', 'Creative', 'Minijuegos', 'Modded']
    },
    'Tibia': {
        'name': 'Tibia',
        'emoji': '🗡️',
        'types': ['Hunt', 'Quest', 'Boss']
    },
    'PokéXGames': {
        'name': 'PokéXGames',
        'emoji': '⚡',
        'types': ['PvP', 'Hunt', 'Clan Wars']
    }
}

# Nombre de la base de datos
DATABASE_NAME = 'gaming_bot.db'