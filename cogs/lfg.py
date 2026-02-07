"""
Cog para el sistema de búsqueda de partidas (LFG - Looking For Group)
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from config.settings import GAMES
from utils.embeds import create_lfg_embed, create_error_embed
from utils.helpers import get_or_create_role

logger = logging.getLogger('discord_bot')


class LFGCog(commands.Cog):
    """Comandos para buscar compañeros de juego"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="lfg", description="Buscar compañeros para jugar")
    @app_commands.describe(
        juego="El juego para el que buscas compañeros",
        descripcion="Descripción adicional (opcional)"
    )
    async def lfg(
        self,
        interaction: discord.Interaction,
        juego: str,
        descripcion: Optional[str] = None
    ):
        """Comando general para buscar grupo en cualquier juego"""
        # Validar que el juego existe
        juego_upper = juego.upper()
        if juego_upper not in GAMES:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Juego no válido",
                    f"El juego '{juego}' no está en la lista. Juegos disponibles: {', '.join(GAMES.keys())}"
                ),
                ephemeral=True
            )
            return
        
        # Obtener el rol del juego
        role = await get_or_create_role(interaction.guild, juego_upper)
        
        # Crear el embed
        embed = create_lfg_embed(
            game=GAMES[juego_upper]['name'],
            user=interaction.user,
            description=descripcion
        )
        
        # Mensaje con mención del rol
        mention_text = f"{role.mention} - ¡Alguien busca grupo!" if role else ""
        
        await interaction.response.send_message(content=mention_text, embed=embed)
    
    @app_commands.command(name="lfg_lol", description="Buscar compañeros para League of Legends")
    @app_commands.describe(
        rol="Tu rol preferido (Top, Jungle, Mid, ADC, Support)",
        rango="Tu rango actual (opcional)"
    )
    async def lfg_lol(
        self,
        interaction: discord.Interaction,
        rol: str,
        rango: Optional[str] = None
    ):
        """Comando específico para buscar grupo en League of Legends"""
        # Validar rol
        if rol.capitalize() not in GAMES['LOL']['roles']:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Rol no válido",
                    f"Roles disponibles: {', '.join(GAMES['LOL']['roles'])}"
                ),
                ephemeral=True
            )
            return
        
        # Validar rango si se proporciona
        if rango and rango.capitalize() not in GAMES['LOL']['ranks']:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Rango no válido",
                    f"Rangos disponibles: {', '.join(GAMES['LOL']['ranks'])}"
                ),
                ephemeral=True
            )
            return
        
        # Obtener el rol del juego
        role = await get_or_create_role(interaction.guild, 'LOL')
        
        # Crear el embed
        embed = create_lfg_embed(
            game="League of Legends",
            user=interaction.user,
            description="¡Buscando compañeros para jugar LoL!",
            **{
                "Rol": rol.capitalize(),
                "Rango": rango.capitalize() if rango else "No especificado"
            }
        )
        
        # Mensaje con mención del rol
        mention_text = f"{role.mention} - ¡Alguien busca grupo para LoL!" if role else ""
        
        await interaction.response.send_message(content=mention_text, embed=embed)
    
    @app_commands.command(name="lfg_wow", description="Buscar compañeros para World of Warcraft")
    @app_commands.describe(
        tipo="Tipo de actividad (Raid, Mythic+, PvP, Arena, Dungeons)",
        rol="Tu rol (Tank, Healer, DPS)"
    )
    async def lfg_wow(
        self,
        interaction: discord.Interaction,
        tipo: str,
        rol: str
    ):
        """Comando específico para buscar grupo en World of Warcraft"""
        # Validar tipo
        if tipo.capitalize() not in GAMES['WoW']['types'] and tipo != 'Mythic+':
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Tipo no válido",
                    f"Tipos disponibles: {', '.join(GAMES['WoW']['types'])}"
                ),
                ephemeral=True
            )
            return
        
        # Validar rol
        if rol.upper() not in GAMES['WoW']['roles']:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Rol no válido",
                    f"Roles disponibles: {', '.join(GAMES['WoW']['roles'])}"
                ),
                ephemeral=True
            )
            return
        
        # Obtener el rol del juego
        role = await get_or_create_role(interaction.guild, 'WoW')
        
        # Crear el embed
        embed = create_lfg_embed(
            game="World of Warcraft",
            user=interaction.user,
            description="¡Buscando compañeros para jugar WoW!",
            **{
                "Actividad": tipo.capitalize() if tipo != 'Mythic+' else 'Mythic+',
                "Rol": rol.upper()
            }
        )
        
        # Mensaje con mención del rol
        mention_text = f"{role.mention} - ¡Alguien busca grupo para WoW!" if role else ""
        
        await interaction.response.send_message(content=mention_text, embed=embed)
    
    @lfg.autocomplete('juego')
    async def lfg_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para el parámetro juego"""
        games = list(GAMES.keys())
        return [
            app_commands.Choice(name=f"{GAMES[game]['emoji']} {GAMES[game]['name']}", value=game)
            for game in games
            if current.lower() in game.lower() or current.lower() in GAMES[game]['name'].lower()
        ][:25]
    
    @lfg_lol.autocomplete('rol')
    async def lfg_lol_rol_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para roles de LoL"""
        return [
            app_commands.Choice(name=rol, value=rol)
            for rol in GAMES['LOL']['roles']
            if current.lower() in rol.lower()
        ][:25]
    
    @lfg_lol.autocomplete('rango')
    async def lfg_lol_rango_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para rangos de LoL"""
        return [
            app_commands.Choice(name=rango, value=rango)
            for rango in GAMES['LOL']['ranks']
            if current.lower() in rango.lower()
        ][:25]
    
    @lfg_wow.autocomplete('tipo')
    async def lfg_wow_tipo_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para tipos de actividad en WoW"""
        return [
            app_commands.Choice(name=tipo, value=tipo)
            for tipo in GAMES['WoW']['types']
            if current.lower() in tipo.lower()
        ][:25]
    
    @lfg_wow.autocomplete('rol')
    async def lfg_wow_rol_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocompletado para roles en WoW"""
        return [
            app_commands.Choice(name=rol, value=rol)
            for rol in GAMES['WoW']['roles']
            if current.lower() in rol.lower()
        ][:25]


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(LFGCog(bot))
    logger.info("LFGCog cargado")
