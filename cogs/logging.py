"""
Sistema de logs automático para el servidor
Registra eventos importantes en el canal de logs
"""
import discord
from discord.ext import commands
import logging
from datetime import datetime

logger = logging.getLogger('discord_bot')

# Nombre del canal de logs
LOG_CHANNEL_NAME = "📋・logs"


class LoggingCog(commands.Cog):
    """Sistema de logs automático para eventos del servidor"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def get_log_channel(self, guild: discord.Guild):
        """Obtiene el canal de logs del servidor"""
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        
        if not channel:
            logger.warning(f"Canal de logs '{LOG_CHANNEL_NAME}' no encontrado en {guild.name}")
        
        return channel
    
    # ===== EVENTOS DE MENSAJES =====
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Registra cuando se elimina un mensaje"""
        if message.author.bot or not message.guild:
            return
        
        log_channel = await self.get_log_channel(message.guild)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🗑️ Mensaje Eliminado",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Usuario", value=message.author.mention, inline=True)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Contenido", value=message.content[:1024] if message.content else "*Sin contenido*", inline=False)
        
        if message.attachments:
            embed.add_field(name="Archivos adjuntos", value=f"{len(message.attachments)} archivo(s)", inline=False)
        
        embed.set_footer(text=f"ID del mensaje: {message.id}")
        embed.set_thumbnail(url=message.author.display_avatar.url)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Registra cuando se edita un mensaje"""
        if before.author.bot or not before.guild:
            return
        
        # Ignorar si el contenido no cambió
        if before.content == after.content:
            return
        
        log_channel = await self.get_log_channel(before.guild)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="✏️ Mensaje Editado",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Usuario", value=before.author.mention, inline=True)
        embed.add_field(name="Canal", value=before.channel.mention, inline=True)
        embed.add_field(name="Antes", value=before.content[:1024] if before.content else "*Sin contenido*", inline=False)
        embed.add_field(name="Después", value=after.content[:1024] if after.content else "*Sin contenido*", inline=False)
        embed.add_field(name="Link", value=f"[Ir al mensaje]({after.jump_url})", inline=False)
        
        embed.set_footer(text=f"ID del mensaje: {before.id}")
        embed.set_thumbnail(url=before.author.display_avatar.url)
        
        await log_channel.send(embed=embed)
    
    # ===== EVENTOS DE MIEMBROS =====
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Registra cuando un usuario se une al servidor"""
        log_channel = await self.get_log_channel(member.guild)
        if not log_channel:
            return
        
        # Calcular antigüedad de la cuenta
        account_age = datetime.now() - member.created_at
        days_old = account_age.days
        
        embed = discord.Embed(
            title="👋 Nuevo Miembro",
            description=f"**{member.mention}** se unió al servidor",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Usuario", value=f"{member.name}", inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Antigüedad de cuenta", value=f"{days_old} días", inline=True)
        embed.add_field(name="Miembro #", value=f"{member.guild.member_count}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Cuenta creada")
        embed.timestamp = member.created_at
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Registra cuando un usuario sale del servidor"""
        log_channel = await self.get_log_channel(member.guild)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="👋 Miembro Salió",
            description=f"**{member.name}** salió del servidor",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Usuario", value=f"{member.name}", inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        
        # Calcular tiempo en el servidor
        if member.joined_at:
            time_in_server = datetime.now() - member.joined_at
            days = time_in_server.days
            embed.add_field(name="Tiempo en servidor", value=f"{days} días", inline=True)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Registra cuando se actualiza un miembro (roles, nickname, etc)"""
        log_channel = await self.get_log_channel(before.guild)
        if not log_channel:
            return
        
        embed = None
        
        # Cambio de nickname
        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Nickname Cambiado",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Usuario", value=after.mention, inline=True)
            embed.add_field(name="Antes", value=before.nick or "*Sin nickname*", inline=True)
            embed.add_field(name="Después", value=after.nick or "*Sin nickname*", inline=True)
        
        # Cambio de roles
        elif before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="🎭 Roles Actualizados",
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Usuario", value=after.mention, inline=False)
                
                if added_roles:
                    roles_text = ", ".join([role.mention for role in added_roles])
                    embed.add_field(name="✅ Roles Añadidos", value=roles_text, inline=False)
                
                if removed_roles:
                    roles_text = ", ".join([role.mention for role in removed_roles])
                    embed.add_field(name="❌ Roles Removidos", value=roles_text, inline=False)
        
        if embed:
            embed.set_thumbnail(url=after.display_avatar.url)
            await log_channel.send(embed=embed)
    
    # ===== EVENTOS DE SERVIDOR =====
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Registra cuando se crea un canal"""
        log_channel = await self.get_log_channel(channel.guild)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="📢 Canal Creado",
            description=f"Se creó el canal {channel.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Nombre", value=channel.name, inline=True)
        embed.add_field(name="Tipo", value=str(channel.type), inline=True)
        embed.add_field(name="ID", value=f"`{channel.id}`", inline=True)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Registra cuando se elimina un canal"""
        log_channel = await self.get_log_channel(channel.guild)
        if not log_channel or channel.id == log_channel.id:
            return
        
        embed = discord.Embed(
            title="🗑️ Canal Eliminado",
            description=f"Se eliminó el canal **#{channel.name}**",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Nombre", value=channel.name, inline=True)
        embed.add_field(name="Tipo", value=str(channel.type), inline=True)
        embed.add_field(name="ID", value=f"`{channel.id}`", inline=True)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """Registra cuando se crea un rol"""
        log_channel = await self.get_log_channel(role.guild)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🎭 Rol Creado",
            description=f"Se creó el rol {role.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Nombre", value=role.name, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Registra cuando se elimina un rol"""
        log_channel = await self.get_log_channel(role.guild)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🗑️ Rol Eliminado",
            description=f"Se eliminó el rol **@{role.name}**",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Nombre", value=role.name, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        
        await log_channel.send(embed=embed)
    
    # ===== EVENTOS DE MODERACIÓN =====
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Registra cuando se banea un usuario"""
        log_channel = await self.get_log_channel(guild)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🔨 Usuario Baneado",
            description=f"**{user.name}** fue baneado del servidor",
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Usuario", value=f"{user.name}", inline=True)
        embed.add_field(name="ID", value=f"`{user.id}`", inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Registra cuando se desbanea un usuario"""
        log_channel = await self.get_log_channel(guild)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="✅ Usuario Desbaneado",
            description=f"**{user.name}** fue desbaneado",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Usuario", value=f"{user.name}", inline=True)
        embed.add_field(name="ID", value=f"`{user.id}`", inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await log_channel.send(embed=embed)


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(LoggingCog(bot))
    logger.info("LoggingCog cargado")
