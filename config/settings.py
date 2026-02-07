"""
Configuración centralizada del bot de Discord
"""
import os

# DEBUG: Imprimir todas las variables de entorno para diagnosticar
print("=" * 50)
print("DEBUG: Variables de entorno disponibles:")
for key in os.environ:
    if 'TOKEN' in key or 'DISCORD' in key:
        print(f"  {key} = {'*' * 10} (existe)")
print("=" * 50)

# Intentar cargar dotenv solo si está disponible (local)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("DEBUG: dotenv cargado")
except ImportError:
    print("DEBUG: dotenv no disponible (normal en Railway)")
    pass

# Token del bot (REQUERIDO)
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN') or os.environ.get('DISCORD_TOKEN')

# DEBUG: Verificar si se cargó el token
if DISCORD_TOKEN:
    print(f"DEBUG: DISCORD_TOKEN encontrado (longitud: {len(DISCORD_TOKEN)} caracteres)")
else:
    print("DEBUG: DISCORD_TOKEN NO encontrado")
    print(f"DEBUG: Total de variables de entorno: {len(os.environ)}")

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