"""
Cog para comandos de utilidad
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional
from datetime import datetime, timezone

from config.settings import GAMES
from utils.embeds import (
    create_info_embed,
    create_profile_embed,
    create_userinfo_embed,
    create_serverinfo_embed
)
from database.db_manager import db_manager

logger = logging.getLogger('discord_bot')


class UtilityCog(commands.Cog):
    """Comandos de utilidad general"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="Ver la latencia del bot")
    async def ping(self, interaction: discord.Interaction):
        """Muestra la latencia del bot"""
        latency = round(self.bot.latency * 1000)
        
        embed = create_info_embed(
            "🏓 Pong!",
            f"Latencia: **{latency}ms**"
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="serverinfo", description="Ver información del servidor")
    async def serverinfo(self, interaction: discord.Interaction):
        """Muestra información del servidor"""
        embed = create_serverinfo_embed(interaction.guild)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Ver información de un usuario")
    @app_commands.describe(usuario="El usuario a consultar (opcional, por defecto tú)")
    async def userinfo(
        self,
        interaction: discord.Interaction,
        usuario: Optional[discord.Member] = None
    ):
        """Muestra información de un usuario"""
        target = usuario or interaction.user
        embed = create_userinfo_embed(target)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="perfil", description="Ver tu perfil de gaming")
    async def perfil(self, interaction: discord.Interaction):
        """Muestra el perfil de gaming del usuario"""
        try:
            # Obtener perfil de la base de datos
            profile = await db_manager.get_user_profile(interaction.user.id)
            
            # Obtener advertencias
            warning_count = await db_manager.get_warning_count(
                interaction.user.id,
                interaction.guild.id
            )
            
            # Formatear juegos
            games_str = "Ninguno"
            if profile and profile['games']:
                games_list = profile['games'].split(',')
                games_str = ", ".join([f"{GAMES.get(game, {}).get('emoji', '')} {game}" for game in games_list])
            
            # Crear embed
            embed = create_profile_embed(
                interaction.user,
                games_str,
                warning_count
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error al obtener perfil: {e}")
            embed = create_info_embed(
                "Perfil de Gaming",
                "No se pudo cargar tu perfil. Intenta más tarde."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="ayuda", description="Ver la lista de comandos disponibles")
    async def ayuda(self, interaction: discord.Interaction):
        """Muestra todos los comandos disponibles"""
        embed = discord.Embed(
            title="📚 Lista de Comandos",
            description="Aquí están todos los comandos disponibles del bot:",
            color=0x3498db
        )
        
        # Comandos de Roles
        embed.add_field(
            name="🎮 Roles de Juegos",
            value=(
                "`/roles` - Panel para seleccionar tus juegos favoritos\n"
                "`/crear_roles` - Crear todos los roles de juegos (Admin)"
            ),
            inline=False
        )
        
        # Comandos de LFG
        embed.add_field(
            name="🔍 Buscar Grupo (LFG)",
            value=(
                "`/lfg <juego> [descripción]` - Buscar compañeros para jugar\n"
                "`/lfg_lol <rol> [rango]` - Buscar grupo para League of Legends\n"
                "`/lfg_wow <tipo> <rol>` - Buscar grupo para World of Warcraft"
            ),
            inline=False
        )
        
        # Comandos de Moderación
        embed.add_field(
            name="🛡️ Moderación",
            value=(
                "`/kick <usuario> [razón]` - Expulsar usuario\n"
                "`/ban <usuario> [razón]` - Banear usuario\n"
                "`/warn <usuario> <razón>` - Advertir usuario\n"
                "`/warnings <usuario>` - Ver advertencias\n"
                "`/clear <cantidad>` - Borrar mensajes (1-100)\n"
                "`/mute <usuario> [tiempo]` - Silenciar usuario"
            ),
            inline=False
        )
        
        # Comandos de Eventos
        embed.add_field(
            name="📅 Eventos",
            value=(
                "`/evento <título> <fecha> <descripción>` - Crear evento\n"
                "`/eventos` - Ver próximos eventos"
            ),
            inline=False
        )
        
        # Comandos de Utilidad
        embed.add_field(
            name="🔧 Utilidad",
            value=(
                "`/ping` - Ver latencia del bot\n"
                "`/serverinfo` - Información del servidor\n"
                "`/userinfo [@usuario]` - Información de usuario\n"
                "`/perfil` - Ver tu perfil de gaming\n"
                "`/ayuda` - Mostrar este mensaje"
            ),
            inline=False
        )
        
        # Información de juegos disponibles
        games_list = ", ".join([f"{data['emoji']} {key}" for key, data in GAMES.items()])
        embed.add_field(
            name="🎯 Juegos Disponibles",
            value=games_list,
            inline=False
        )
        
        embed.set_footer(text="Usa /roles para comenzar a jugar con la comunidad!")
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(UtilityCog(bot))
    logger.info("UtilityCog cargado")
