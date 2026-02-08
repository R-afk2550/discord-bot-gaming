"""
Sistema de niveles y experiencia para el bot
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timedelta
from database.db_manager import db_manager

logger = logging.getLogger('discord_bot')

# Configuración
XP_PER_MESSAGE = 10
XP_COOLDOWN = 60  # segundos entre mensajes que otorgan XP
LEVEL_MULTIPLIER = 100  # XP necesaria para el siguiente nivel = nivel actual * multiplicador


class LevelsCog(commands.Cog):
    """Sistema de niveles y experiencia"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.xp_cooldowns = {}  # {(user_id, guild_id): datetime}
    
    def calculate_xp_for_level(self, level: int) -> int:
        """Calcula la XP necesaria para alcanzar un nivel"""
        return level * LEVEL_MULTIPLIER
    
    def calculate_level_from_xp(self, xp: int) -> int:
        """Calcula el nivel basado en la XP total"""
        level = 1
        xp_needed = self.calculate_xp_for_level(level)
        while xp >= xp_needed:
            level += 1
            xp_needed = self.calculate_xp_for_level(level)
        return level - 1
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Otorga XP por mensajes"""
        # Ignorar mensajes de bots
        if message.author.bot:
            return
        
        # Verificar si está en servidor
        if not message.guild:
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        cooldown_key = (user_id, guild_id)
        
        # Verificar cooldown
        now = datetime.now()
        if cooldown_key in self.xp_cooldowns:
            time_since_last = (now - self.xp_cooldowns[cooldown_key]).total_seconds()
            if time_since_last < XP_COOLDOWN:
                return
        
        # Actualizar cooldown
        self.xp_cooldowns[cooldown_key] = now
        
        # Obtener datos actuales del usuario
        user_data = await db_manager.get_user_level_data(user_id, guild_id)
        
        if user_data is None:
            # Crear nuevo registro
            await db_manager.init_user_stats(user_id, guild_id)
            user_data = await db_manager.get_user_level_data(user_id, guild_id)
        
        # Calcular nueva XP
        current_xp = user_data['xp']
        new_xp = current_xp + XP_PER_MESSAGE
        current_level = user_data['level']
        new_level = self.calculate_level_from_xp(new_xp)
        
        # Actualizar base de datos
        await db_manager.add_xp(user_id, guild_id, XP_PER_MESSAGE)
        
        # Si subió de nivel, notificar
        if new_level > current_level:
            await db_manager.update_level(user_id, guild_id, new_level)
            
            embed = discord.Embed(
                title="🎉 ¡Subiste de Nivel!",
                description=f"{message.author.mention} ha alcanzado el **Nivel {new_level}**!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            await message.channel.send(embed=embed)
    
    @app_commands.command(name="nivel", description="Ver tu nivel y experiencia")
    async def nivel(self, interaction: discord.Interaction, usuario: discord.Member = None):
        """Muestra el nivel y XP de un usuario"""
        target = usuario or interaction.user
        
        user_data = await db_manager.get_user_level_data(target.id, interaction.guild.id)
        
        if user_data is None:
            await db_manager.init_user_stats(target.id, interaction.guild.id)
            user_data = await db_manager.get_user_level_data(target.id, interaction.guild.id)
        
        level = user_data['level']
        xp = user_data['xp']
        xp_needed = self.calculate_xp_for_level(level + 1)
        xp_progress = xp - self.calculate_xp_for_level(level)
        xp_for_current = self.calculate_xp_for_level(level)
        
        embed = discord.Embed(
            title=f"📊 Nivel de {target.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(
            name="Nivel",
            value=f"⭐ **{level}**",
            inline=True
        )
        embed.add_field(
            name="XP Total",
            value=f"💎 **{xp}** XP",
            inline=True
        )
        embed.add_field(
            name="Progreso",
            value=f"📈 **{xp_progress}/{LEVEL_MULTIPLIER}** XP para nivel {level + 1}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ranking", description="Ver el ranking de niveles del servidor")
    async def ranking(self, interaction: discord.Interaction, limite: int = 10):
        """Muestra el ranking de niveles"""
        if limite > 25:
            limite = 25
        
        top_users = await db_manager.get_top_users(interaction.guild.id, limite)
        
        if not top_users:
            await interaction.response.send_message("No hay datos de niveles aún.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🏆 Top {len(top_users)} Usuarios por Nivel",
            color=discord.Color.gold()
        )
        
        description = ""
        for i, user_data in enumerate(top_users, 1):
            user = interaction.guild.get_member(user_data['user_id'])
            if user:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                description += f"{medal} **{user.name}** - Nivel {user_data['level']} ({user_data['xp']} XP)\n"
        
        embed.description = description
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(LevelsCog(bot))