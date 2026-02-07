"""
Plantillas de embeds para el bot
"""
import discord
from datetime import datetime
from config.settings import COLORS


def create_info_embed(title: str, description: str, **kwargs) -> discord.Embed:
    """Crea un embed informativo (azul)"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=COLORS['info'],
        timestamp=datetime.utcnow()
    )
    for key, value in kwargs.items():
        embed.add_field(name=key, value=value, inline=False)
    return embed


def create_success_embed(title: str, description: str) -> discord.Embed:
    """Crea un embed de éxito (verde)"""
    return discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=COLORS['success'],
        timestamp=datetime.utcnow()
    )


def create_error_embed(title: str, description: str) -> discord.Embed:
    """Crea un embed de error (rojo)"""
    return discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=COLORS['error'],
        timestamp=datetime.utcnow()
    )


def create_warning_embed(title: str, description: str) -> discord.Embed:
    """Crea un embed de advertencia (naranja)"""
    return discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=COLORS['warning'],
        timestamp=datetime.utcnow()
    )


def create_event_embed(title: str, description: str, event_date: str, creator: str) -> discord.Embed:
    """Crea un embed de evento (morado)"""
    embed = discord.Embed(
        title=f"📅 {title}",
        description=description,
        color=COLORS['event'],
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Fecha del Evento", value=event_date, inline=True)
    embed.add_field(name="Organizador", value=creator, inline=True)
    return embed


def create_welcome_embed(member: discord.Member, guild: discord.Guild) -> discord.Embed:
    """Crea un embed de bienvenida"""
    embed = discord.Embed(
        title=f"¡Bienvenido/a a {guild.name}! 🎮",
        description=f"¡Hola {member.mention}! Nos alegra tenerte aquí.",
        color=COLORS['success'],
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name="📋 Instrucciones",
        value="Usa el comando `/roles` para elegir tus juegos favoritos y unirte a las comunidades.",
        inline=False
    )
    embed.add_field(
        name="📜 Reglas Básicas",
        value="• Respeta a todos los miembros\n• No spam ni publicidad\n• Diviértete y haz amigos",
        inline=False
    )
    embed.add_field(
        name="🎯 Comandos Útiles",
        value="`/ayuda` - Ver todos los comandos\n`/lfg` - Buscar compañeros de juego",
        inline=False
    )
    embed.set_footer(text=f"Miembro #{guild.member_count}")
    return embed


def create_lfg_embed(game: str, user: discord.Member, description: str = None, **kwargs) -> discord.Embed:
    """Crea un embed para búsqueda de grupo (LFG)"""
    embed = discord.Embed(
        title=f"🎮 Buscando grupo para {game}",
        description=description or f"{user.mention} está buscando compañeros para jugar!",
        color=COLORS['info'],
        timestamp=datetime.utcnow()
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    
    for key, value in kwargs.items():
        if value:
            embed.add_field(name=key, value=value, inline=True)
    
    embed.set_footer(text="¡Únete a la partida!")
    return embed


def create_profile_embed(user: discord.Member, games: str, warnings_count: int) -> discord.Embed:
    """Crea un embed de perfil de usuario"""
    embed = discord.Embed(
        title=f"Perfil de {user.display_name}",
        color=COLORS['info'],
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="🎮 Juegos Registrados", value=games or "Ninguno", inline=False)
    embed.add_field(name="⚠️ Advertencias", value=str(warnings_count), inline=True)
    embed.add_field(name="📅 Se unió", value=user.joined_at.strftime("%d/%m/%Y") if user.joined_at else "N/A", inline=True)
    return embed


def create_userinfo_embed(user: discord.Member) -> discord.Embed:
    """Crea un embed con información de usuario"""
    embed = discord.Embed(
        title="Información del Usuario",
        color=COLORS['info'],
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Nombre", value=user.name, inline=True)
    embed.add_field(name="Apodo", value=user.display_name, inline=True)
    embed.add_field(name="ID", value=user.id, inline=True)
    embed.add_field(name="Se unió al servidor", value=user.joined_at.strftime("%d/%m/%Y %H:%M") if user.joined_at else "N/A", inline=False)
    embed.add_field(name="Cuenta creada", value=user.created_at.strftime("%d/%m/%Y %H:%M"), inline=False)
    
    roles = [role.mention for role in user.roles[1:]]  # Excluir @everyone
    embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) if roles else "Sin roles", inline=False)
    
    return embed


def create_serverinfo_embed(guild: discord.Guild) -> discord.Embed:
    """Crea un embed con información del servidor"""
    embed = discord.Embed(
        title=f"Información de {guild.name}",
        color=COLORS['info'],
        timestamp=datetime.utcnow()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="👑 Dueño", value=guild.owner.mention if guild.owner else "N/A", inline=True)
    embed.add_field(name="🆔 ID", value=guild.id, inline=True)
    embed.add_field(name="📅 Creado", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="👥 Miembros", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Canales", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
    
    return embed
