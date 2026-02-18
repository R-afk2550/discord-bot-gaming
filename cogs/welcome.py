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
        
        # Crear y enviar el embed de bienvenida en el canal público
        try:
            embed = create_welcome_embed(member, member.guild)
            await welcome_channel.send(embed=embed)
            logger.info(f"Mensaje de bienvenida enviado para {member.name}")
        except discord.Forbidden:
            logger.error(f"No tengo permisos para enviar mensajes en {welcome_channel.name}")
        except Exception as e:
            logger.error(f"Error al enviar mensaje de bienvenida: {e}")
        
        # Enviar DM con lista de comandos
        try:
            dm_embed = discord.Embed(
                title=f"¡Bienvenido a {member.guild.name}! 👋",
                description="Aquí está la lista de comandos disponibles que puedes usar:",
                color=discord.Color.green()
            )
            
            # 💰 Economía
            dm_embed.add_field(
                name="💰 Economía",
                value=(
                    "```\n"
                    "/balance - Ver tu balance de monedas\n"
                    "/daily - Reclamar tu recompensa diaria\n"
                    "/work - Trabajar para ganar monedas\n"
                    "/transfer <usuario> <cantidad> - Transferir monedas\n"
                    "/coinflip <cantidad> - Apostar en cara o cruz\n"
                    "/leaderboard - Top 10 usuarios más ricos\n"
                    "```"
                ),
                inline=False
            )
            
            # 📊 Niveles
            dm_embed.add_field(
                name="📊 Niveles",
                value=(
                    "```\n"
                    "/nivel [usuario] - Ver nivel y XP\n"
                    "/ranking - Top 10 niveles del servidor\n"
                    "/setxp <usuario> <xp> - Establecer XP (admin)\n"
                    "```"
                ),
                inline=False
            )
            
            # 🎮 Tibia - Información
            dm_embed.add_field(
                name="🎮 Tibia - Información",
                value=(
                    "`/tibia char` `/tibia online` `/tibia deaths` `/tibia guild` "
                    "`/tibia worlds` `/tibia world` `/tibia battleye` `/tibia boosted` `/tibia news`"
                ),
                inline=False
            )
            
            # 💎 Tibia - Loot Tracker
            dm_embed.add_field(
                name="💎 Tibia - Loot Tracker",
                value=(
                    "`/loot registrar` `/loot historial` `/loot stats` "
                    "`/loot mejores` `/loot total`"
                ),
                inline=False
            )
            
            # 🧮 Tibia - Calculadoras
            dm_embed.add_field(
                name="🧮 Tibia - Calculadoras",
                value="`/tibia exp` `/tibia stamina`",
                inline=False
            )
            
            # 🏪 Tibia - Utilidades
            dm_embed.add_field(
                name="🏪 Tibia - Utilidades",
                value="`/tibia rashid` - Ubicación de Rashid",
                inline=False
            )
            
            # 🛠️ Moderación
            dm_embed.add_field(
                name="🛠️ Moderación (solo admins)",
                value=(
                    "```\n"
                    "/warn <usuario> <razón> - Advertir usuario\n"
                    "/kick <usuario> [razón] - Expulsar usuario\n"
                    "/ban <usuario> [razón] - Banear usuario\n"
                    "/clear <cantidad> - Borrar mensajes\n"
                    "/mute <usuario> <tiempo> - Silenciar usuario\n"
                    "```"
                ),
                inline=False
            )
            
            # 👥 Utilidades y más
            dm_embed.add_field(
                name="👥 Utilidades y Más",
                value=(
                    "`/roles` `/ayuda` `/ping` `/serverinfo` `/userinfo` "
                    "`/perfil` `/evento` `/eventos` `/lfg`"
                ),
                inline=False
            )
            
            dm_embed.set_footer(text="Usa / en el chat para ver todos los comandos disponibles con autocompletado")
            
            # Opcional: agregar thumbnail del servidor si está disponible
            if member.guild.icon:
                dm_embed.set_thumbnail(url=member.guild.icon.url)
            
            await member.send(embed=dm_embed)
            logger.info(f"Mensaje de bienvenida DM enviado a {member.name}")
            
        except discord.Forbidden:
            # El usuario tiene los DMs desactivados
            logger.warning(f"No se pudo enviar DM a {member.name} (DMs desactivados)")
        except Exception as e:
            logger.error(f"Error al enviar mensaje de bienvenida por DM: {e}")


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(WelcomeCog(bot))
    logger.info("WelcomeCog cargado")
