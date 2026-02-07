"""
Cog para el sistema de selección de juegos con botones
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger('discord_bot')


# Vista con botones persistentes
class GameSelectionView(discord.ui.View):
    """Vista con botones para selección de juegos"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Sin timeout para que sea persistente
    
    async def toggle_role(self, interaction: discord.Interaction, role_name: str, emoji: str):
        """Alterna el rol del usuario"""
        # Buscar el rol
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        
        if not role:
            # Si el rol no existe, crearlo
            try:
                role = await interaction.guild.create_role(
                    name=role_name,
                    reason="Rol de juego creado automáticamente"
                )
                logger.info(f"Rol '{role_name}' creado automáticamente")
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ No tengo permisos para crear roles. Contacta a un administrador.",
                    ephemeral=True
                )
                return
        
        # Verificar si el usuario ya tiene el rol
        if role in interaction.user.roles:
            # Quitar el rol
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(
                f"❌ Se quitó el rol **{role_name}** {emoji}",
                ephemeral=True
            )
            logger.info(f"Rol '{role_name}' quitado a {interaction.user.name}")
        else:
            # Agregar el rol
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"✅ Se agregó el rol **{role_name}** {emoji}\n¡Ahora puedes ver los canales de {role_name}!",
                ephemeral=True
            )
            logger.info(f"Rol '{role_name}' agregado a {interaction.user.name}")
    
    @discord.ui.button(label="League of Legends", emoji="🎯", style=discord.ButtonStyle.primary, custom_id="game_lol")
    async def lol_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "LoL", "🎯")
    
    @discord.ui.button(label="World of Warcraft", emoji="⚔️", style=discord.ButtonStyle.primary, custom_id="game_wow")
    async def wow_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "WoW", "⚔️")
    
    @discord.ui.button(label="Minecraft", emoji="⛏️", style=discord.ButtonStyle.primary, custom_id="game_minecraft")
    async def minecraft_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "Minecraft", "⛏️")
    
    @discord.ui.button(label="Tibia", emoji="🐉", style=discord.ButtonStyle.primary, custom_id="game_tibia")
    async def tibia_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "Tibia", "🐉")
    
    @discord.ui.button(label="PokéXGames", emoji="⚡", style=discord.ButtonStyle.primary, custom_id="game_pokexgames")
    async def pokexgames_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "PokéXGames", "⚡")
    
    @discord.ui.button(label="Phasmophobia", emoji="👻", style=discord.ButtonStyle.primary, custom_id="game_phasmophobia")
    async def phasmophobia_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "Phasmophobia", "👻")


class GameSelectionCog(commands.Cog):
    """Sistema de selección de juegos"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Registrar la vista cuando el bot esté listo"""
        self.bot.add_view(GameSelectionView())
        logger.info("Vista de selección de juegos registrada")
    
    @app_commands.command(name="configurar_roles_juegos", description="Configura el mensaje de selección de juegos (Solo Admins)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_game_selection(self, interaction: discord.Interaction):
        """Comando para configurar el mensaje de selección de juegos"""
        
        # Crear embed
        embed = discord.Embed(
            title="🎮 Selecciona tus juegos favoritos",
            description=(
                "Haz clic en los botones de abajo para recibir acceso a los canales de cada juego.\n\n"
                "**Cómo funciona:**\n"
                "• Click en un botón = Recibes el rol y ves los canales\n"
                "• Click de nuevo = Quitas el rol y ocultas los canales\n\n"
                "Puedes seleccionar **todos los juegos** que quieras. ¡Únete a la comunidad!"
            ),
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Juegos disponibles:",
            value=(
                "🎯 **League of Legends**\n"
                "⚔️ **World of Warcraft**\n"
                "⛏️ **Minecraft**\n"
                "🐉 **Tibia**\n"
                "⚡ **PokéXGames**\n"
                "👻 **Phasmophobia**"
            ),
            inline=False
        )
        embed.set_footer(text="Zero Hour • Sistema de Roles")
        
        # Crear la vista con botones
        view = GameSelectionView()
        
        # Enviar el mensaje
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Mensaje de selección de juegos configurado!", ephemeral=True)
        logger.info(f"Mensaje de selección configurado por {interaction.user.name}")


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(GameSelectionCog(bot))
    logger.info("GameSelectionCog cargado")
