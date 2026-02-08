"""
Bot de Discord para Servidor Gaming Multi-Juego
Autor: R-afk2550
"""
import discord
from discord.ext import commands
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

from config.settings import DISCORD_TOKEN, GUILD_ID
from database.db_manager import db_manager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('discord_bot')


class GamingBot(commands.Bot):
    """Bot principal de Discord para gaming"""
    
    def __init__(self):
        # Configurar intents necesarios
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',  # Prefijo legacy (usamos slash commands principalmente)
            intents=intents,
            help_command=None  # Desactivamos el comando de ayuda por defecto
        )
        
        self.start_time = datetime.now(timezone.utc)
    
    async def setup_hook(self):
        """Se ejecuta antes de que el bot inicie sesión"""
        logger.info("Iniciando setup del bot...")
        
        # Inicializar base de datos
        await db_manager.initialize()
        
        # Cargar todos los cogs
        await self.load_cogs()
        
        # Sincronizar comandos slash (opcional: solo para un servidor específico)
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Comandos sincronizados para el servidor {GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("Comandos sincronizados globalmente")
    
    async def load_cogs(self):
        """Carga todos los cogs del directorio cogs/"""
        cogs_dir = Path(__file__).parent / 'cogs'
        
        # Lista de cogs a cargar
        cog_files = [
            'roles',
            'lfg',
            'welcome',
            'moderation',
            'utility',
            'events',
            'levels',
            'economy',
            'logging'
        ]
        
        for cog_file in cog_files:
            try:
                await self.load_extension(f'cogs.{cog_file}')
                logger.info(f"Cog '{cog_file}' cargado correctamente")
            except Exception as e:
                logger.error(f"Error al cargar el cog '{cog_file}': {e}")
    
    async def on_ready(self):
        """Se ejecuta cuando el bot está listo"""
        logger.info(f"Bot conectado como {self.user.name} (ID: {self.user.id})")
        logger.info(f"Discord.py versión: {discord.__version__}")
        logger.info(f"Servidores: {len(self.guilds)}")
        logger.info("Bot listo para usar!")
        
        # Establecer actividad del bot
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="🎮 /ayuda para comandos"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
    
    async def on_command_error(self, ctx, error):
        """Manejo global de errores"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignorar comandos no encontrados
        
        logger.error(f"Error en comando: {error}")


def main():
    """Función principal para iniciar el bot"""
    # Verificar que existe el token
    if not DISCORD_TOKEN:
        logger.error("ERROR: No se encontró DISCORD_TOKEN en las variables de entorno")
        logger.error("Por favor, configura el archivo .env con tu token de Discord")
        sys.exit(1)
    
    # Crear e iniciar el bot
    bot = GamingBot()
    
    try:
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("ERROR: Token de Discord inválido")
        sys.exit(1)
    except Exception as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()