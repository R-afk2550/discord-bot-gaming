"""
Cog para el sistema de roles por juego
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging

from config.settings import GAMES, COLORS
from utils.helpers import get_or_create_role, assign_role, remove_role
from utils.embeds import create_success_embed, create_error_embed, create_info_embed
from database.db_manager import db_manager

logger = logging.getLogger('discord_bot')


class RoleButton(discord.ui.Button):
    """Botón para asignar/remover un rol de juego"""
    
    def __init__(self, game: str, emoji: str):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=game,
            emoji=emoji,
            custom_id=f"role_{game}"
        )
        self.game = game
    
    async def callback(self, interaction: discord.Interaction):
        """Se ejecuta cuando se presiona el botón"""
        # Obtener o crear el rol
        role = await get_or_create_role(interaction.guild, self.game)
        
        if not role:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No pude crear el rol. Verifica los permisos del bot."
                ),
                ephemeral=True
            )
            return
        
        # Verificar si el usuario ya tiene el rol
        if role in interaction.user.roles:
            # Remover el rol
            success = await remove_role(interaction.user, role)
            if success:
                await interaction.response.send_message(
                    embed=create_success_embed(
                        "Rol Removido",
                        f"Se te ha removido el rol de **{self.game}**"
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Error",
                        "No pude remover el rol. Verifica los permisos del bot."
                    ),
                    ephemeral=True
                )
        else:
            # Asignar el rol
            success = await assign_role(interaction.user, role)
            if success:
                # Actualizar perfil del usuario
                current_profile = await db_manager.get_user_profile(interaction.user.id)
                games_list = current_profile['games'].split(',') if current_profile and current_profile['games'] else []
                if self.game not in games_list:
                    games_list.append(self.game)
                await db_manager.update_user_games(
                    interaction.user.id,
                    interaction.guild.id,
                    ','.join(games_list)
                )
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        "Rol Asignado",
                        f"¡Ahora tienes el rol de **{self.game}**! 🎮"
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Error",
                        "No pude asignar el rol. Verifica los permisos del bot."
                    ),
                    ephemeral=True
                )


class RoleView(discord.ui.View):
    """Vista con botones para seleccionar roles"""
    
    def __init__(self):
        super().__init__(timeout=None)  # No timeout para mensajes persistentes
        
        # Añadir un botón por cada juego
        for game_key, game_data in GAMES.items():
            self.add_item(RoleButton(game_key, game_data['emoji']))


class RolesCog(commands.Cog):
    """Comandos para gestión de roles por juego"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="roles", description="Panel para seleccionar tus juegos favoritos")
    async def roles(self, interaction: discord.Interaction):
        """Muestra el panel de selección de roles"""
        embed = discord.Embed(
            title="🎮 Selección de Roles de Juego",
            description=(
                "Haz clic en los botones de abajo para obtener o remover los roles de tus juegos favoritos.\n\n"
                "**Juegos disponibles:**\n"
            ),
            color=COLORS['info']
        )
        
        # Añadir información de cada juego
        for game_key, game_data in GAMES.items():
            embed.add_field(
                name=f"{game_data['emoji']} {game_data['name']}",
                value=f"Rol: `{game_key}`",
                inline=True
            )
        
        embed.set_footer(text="Puedes tener múltiples roles de juegos")
        
        view = RoleView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="crear_roles", description="Crea todos los roles de juegos (Solo Admin)")
    @app_commands.default_permissions(administrator=True)
    async def crear_roles(self, interaction: discord.Interaction):
        """Crea todos los roles de juegos en el servidor (comando admin)"""
        await interaction.response.defer(ephemeral=True)
        
        created_roles = []
        existing_roles = []
        
        for game_key in GAMES.keys():
            role = await get_or_create_role(interaction.guild, game_key)
            if role:
                if role.id not in [r.id for r in interaction.guild.roles]:
                    created_roles.append(game_key)
                else:
                    existing_roles.append(game_key)
        
        description = ""
        if created_roles:
            description += f"**Roles creados:** {', '.join(created_roles)}\n"
        if existing_roles:
            description += f"**Roles existentes:** {', '.join(existing_roles)}\n"
        
        if not description:
            description = "No se pudieron crear los roles. Verifica los permisos del bot."
        
        embed = create_success_embed("Roles de Juegos", description)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(RolesCog(bot))
    logger.info("RolesCog cargado")
