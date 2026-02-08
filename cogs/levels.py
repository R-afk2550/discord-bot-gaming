"""
Sistema de niveles y XP para el bot
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
import random
from datetime import datetime, timedelta
from database.db_manager import db_manager

logger = logging.getLogger('discord_bot')

# Configuración
XP_PER_MESSAGE_MIN = 15
XP_PER_MESSAGE_MAX = 25
XP_COOLDOWN = 60  # segundos entre mensajes que dan XP
LEVEL_ROLES = {
    5: "Activo",
    10: "Veterano", 
    20: "Leyenda",
    50: "Dios"
}

def calculate_xp_for_level(level: int) -> int:
    """Calcula el XP total necesario para alcanzar un nivel"""
    return level * 50 + 50

def calculate_level_from_xp(xp: int) -> int:
    """Calcula el nivel basado en el XP actual"""
    level = 1
    while calculate_xp_for_level(level) <= xp:
        level += 1
    return level - 1


class LevelsCog(commands.Cog):
    """Sistema de niveles y experiencia"""
    
def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Dar XP por cada mensaje"""
        # Ignorar bots y mensajes sin guild
        if message.author.bot or not message.guild:
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Obtener datos del usuario
        user_data = await db_manager.get_user_level_data(user_id, guild_id)
        
        # Verificar cooldown
        if user_data:
            last_xp_time = user_data.get('last_xp_time')
            if last_xp_time:
                try:
                    last_time = datetime.fromisoformat(last_xp_time)
                    if datetime.now() - last_time < timedelta(seconds=XP_COOLDOWN):
                        return  # Aún en cooldown
                except:
                    pass
        
        # Calcular XP aleatorio
        xp_gained = random.randint(XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX)
        
        # Añadir XP
        await db_manager.add_xp(user_id, guild_id, xp_gained)
        
        # Obtener datos actualizados
        user_data = await db_manager.get_user_level_data(user_id, guild_id)
        if not user_data:
            return
        
        current_xp = user_data['xp']
        current_level = user_data['level']
        
        # Calcular nuevo nivel
        new_level = calculate_level_from_xp(current_xp)
        
        # Si subió de nivel
        if new_level > current_level:
            await db_manager.update_level(user_id, guild_id, new_level)
            
            # Bonus de dinero por subir de nivel
            await db_manager.add_money(user_id, guild_id, 100)
            
            # Mensaje de nivel subido
            embed = discord.Embed(
                title="🎉 ¡SUBISTE DE NIVEL!",
                description=f"**{message.author.mention}** alcanzó el nivel **{new_level}**!",
                color=discord.Color.gold()
            )
            embed.add_field(name="XP Total", value=f"{current_xp} XP", inline=True)
            embed.add_field(name="Bonus", value="100 ⏰ Zero Coins", inline=True)
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            await message.channel.send(embed=embed)
            
            # Asignar rol si corresponde
            if new_level in LEVEL_ROLES:
                role_name = LEVEL_ROLES[new_level]
                role = discord.utils.get(message.guild.roles, name=role_name)
                
                if not role:
                    # Crear el rol si no existe
                    try:
                        colors = {
                            "Activo": discord.Color.green(),
                            "Veterano": discord.Color.blue(),
                            "Leyenda": discord.Color.purple(),
                            "Dios": discord.Color.gold()
                        }
                        role = await message.guild.create_role(
                            name=role_name,
                            color=colors.get(role_name, discord.Color.default()),
                            reason=f"Rol de nivel {new_level}"
                        )
                        logger.info(f"Rol '{role_name}' creado automáticamente")
                    except discord.Forbidden:
                        logger.error("No tengo permisos para crear roles")
                        return
                
                # Asignar el rol
                try:
                    await message.author.add_roles(role)
                    await message.channel.send(f"✨ **{message.author.mention}** obtuvo el rol **{role.mention}**!")
                except discord.Forbidden:
                    logger.error("No tengo permisos para asignar roles")
    
    @app_commands.command(name="nivel", description="Ver tu nivel y XP")
    async def nivel(self, interaction: discord.Interaction, usuario: discord.Member = None):
        """Muestra el nivel y XP de un usuario"""
        target = usuario or interaction.user
        
        user_data = await db_manager.get_user_level_data(target.id, interaction.guild.id)
        
        if not user_data:
            embed = discord.Embed(
                title="📊 Sin datos",
                description=f"**{target.mention}** aún no tiene nivel. ¡Empieza a chatear!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        current_xp = user_data['xp']
        current_level = user_data['level']
        total_messages = user_data['total_messages']
        
        # Calcular XP para siguiente nivel
        xp_needed = calculate_xp_for_level(current_level + 1)
        xp_progress = current_xp - calculate_xp_for_level(current_level)
        xp_for_next = xp_needed - calculate_xp_for_level(current_level)
        
        # Barra de progreso
        progress_percent = (xp_progress / xp_for_next) * 100
        bar_length = 20
        filled = int((progress_percent / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        embed = discord.Embed(
            title=f"🎮 Nivel de {target.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Nivel", value=f"⭐ **{current_level}**", inline=True)
        embed.add_field(name="XP Total", value=f"📊 **{current_xp}**", inline=True)
        embed.add_field(name="Mensajes", value=f"💬 **{total_messages}**", inline=True)
        embed.add_field(
            name="Progreso al siguiente nivel",
            value=f"{bar} {progress_percent:.1f}%\n{xp_progress}/{xp_for_next} XP",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ranking", description="Ver el top 10 de usuarios con más XP")
    async def ranking(self, interaction: discord.Interaction):
        """Muestra el ranking de usuarios por XP"""
        top_users = await db_manager.get_top_users(interaction.guild.id, limit=10)
        
        if not top_users:
            embed = discord.Embed(
                title="📊 Ranking vacío",
                description="Aún no hay usuarios en el ranking. ¡Sé el primero!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="🏆 TOP 10 - Ranking de Niveles",
            description="Los usuarios más activos del servidor",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user_data in enumerate(top_users, 1):
            user_id = user_data['user_id']
            xp = user_data['xp']
            level = user_data['level']
            
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except:
                name = f"Usuario {user_id}"
            
            medal = medals[i-1] if i <= 3 else f"`#{i}`"
            
            embed.add_field(
                name=f"{medal} {name}",
                value=f"Nivel {level} • {xp} XP",
                inline=False
            )
        
        embed.set_footer(text=f"Solicitado por {interaction.user.name}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="setxp", description="[ADMIN] Establecer XP de un usuario")
    @app_commands.checks.has_permissions(administrator=True)
    async def setxp(self, interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
        """Establece el XP de un usuario (solo administradores)"""
        # Actualizar XP
        user_data = await db_manager.get_user_level_data(usuario.id, interaction.guild.id)
        
        if user_data:
            current_xp = user_data['xp']
            difference = cantidad - current_xp
            await db_manager.add_xp(usuario.id, interaction.guild.id, difference)
        else:
            await db_manager.add_xp(usuario.id, interaction.guild.id, cantidad)
        
        # Actualizar nivel
        new_level = calculate_level_from_xp(cantidad)
        await db_manager.update_level(usuario.id, interaction.guild.id, new_level)
        
        embed = discord.Embed(
            title="✅ XP Actualizado",
            description=f"Se estableció el XP de **{usuario.mention}** a **{cantidad}** (Nivel {new_level})",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"{interaction.user.name} estableció el XP de {usuario.name} a {cantidad}")


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(LevelsCog(bot))
    logger.info("LevelsCog cargado")
