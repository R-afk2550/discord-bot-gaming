"""
Cog para el sistema de bienvenida
"""
import discord
from discord.ext import commands
import logging

from config.settings import WELCOME_CHANNEL_ID
from utils.embeds import create_welcome_embed

logger = logging.getLogger('discord_bot')


class WelcomeCog(commands.Cog):
    """Sistema de bienvenida para nuevos miembros"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Se ejecuta cuando un miembro se une al servidor"""
        logger.info(f"Nuevo miembro: {member.name} (ID: {member.id}) se unió a {member.guild.name}")
        
        # Determinar el canal de bienvenida
        welcome_channel = None
        
        if WELCOME_CHANNEL_ID:
            # Usar el canal configurado en .env
            welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        
        if not welcome_channel:
            # Buscar un canal llamado "bienvenida" o "welcome"
            for channel in member.guild.text_channels:
                if channel.name.lower() in ['bienvenida', 'welcome', 'bienvenidas']:
                    welcome_channel = channel
                    break
        
        if not welcome_channel:
            # Usar el primer canal donde el bot pueda escribir
            for channel in member.guild.text_channels:
                if channel.permissions_for(member.guild.me).send_messages:
                    welcome_channel = channel
                    break
        
        if not welcome_channel:
            logger.warning(f"No se encontró canal de bienvenida en {member.guild.name}")
            return
        
        # Crear y enviar el embed de bienvenida
        try:
            embed = create_welcome_embed(member, member.guild)
            await welcome_channel.send(embed=embed)
            logger.info(f"Mensaje de bienvenida enviado para {member.name}")
        except discord.Forbidden:
            logger.error(f"No tengo permisos para enviar mensajes en {welcome_channel.name}")
        except Exception as e:
            logger.error(f"Error al enviar mensaje de bienvenida: {e}")


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(WelcomeCog(bot))
    logger.info("WelcomeCog cargado")
