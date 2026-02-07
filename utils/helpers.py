"""
Funciones auxiliares para el bot
"""
import discord
from typing import Optional
import logging

logger = logging.getLogger('discord_bot')


async def get_or_create_role(guild: discord.Guild, role_name: str, color: discord.Color = None) -> Optional[discord.Role]:
    """
    Obtiene un rol existente o lo crea si no existe
    
    Args:
        guild: El servidor de Discord
        role_name: Nombre del rol
        color: Color del rol (opcional)
    
    Returns:
        El rol encontrado o creado
    """
    # Buscar si el rol ya existe
    role = discord.utils.get(guild.roles, name=role_name)
    
    if role:
        return role
    
    # Si no existe, crear el rol
    try:
        color = color or discord.Color.blue()
        role = await guild.create_role(name=role_name, color=color, mentionable=True)
        logger.info(f"Rol '{role_name}' creado en el servidor {guild.name}")
        return role
    except discord.Forbidden:
        logger.error(f"No tengo permisos para crear el rol '{role_name}' en {guild.name}")
        return None
    except Exception as e:
        logger.error(f"Error al crear el rol '{role_name}': {e}")
        return None


async def assign_role(member: discord.Member, role: discord.Role) -> bool:
    """
    Asigna un rol a un miembro
    
    Args:
        member: El miembro de Discord
        role: El rol a asignar
    
    Returns:
        True si se asignó correctamente, False en caso contrario
    """
    try:
        await member.add_roles(role)
        logger.info(f"Rol '{role.name}' asignado a {member.name}")
        return True
    except discord.Forbidden:
        logger.error(f"No tengo permisos para asignar roles a {member.name}")
        return False
    except Exception as e:
        logger.error(f"Error al asignar rol: {e}")
        return False


async def remove_role(member: discord.Member, role: discord.Role) -> bool:
    """
    Remueve un rol de un miembro
    
    Args:
        member: El miembro de Discord
        role: El rol a remover
    
    Returns:
        True si se removió correctamente, False en caso contrario
    """
    try:
        await member.remove_roles(role)
        logger.info(f"Rol '{role.name}' removido de {member.name}")
        return True
    except discord.Forbidden:
        logger.error(f"No tengo permisos para remover roles de {member.name}")
        return False
    except Exception as e:
        logger.error(f"Error al remover rol: {e}")
        return False


def has_permissions(member: discord.Member, **permissions) -> bool:
    """
    Verifica si un miembro tiene los permisos especificados
    
    Args:
        member: El miembro a verificar
        **permissions: Los permisos a verificar (ej: kick_members=True)
    
    Returns:
        True si tiene todos los permisos, False en caso contrario
    """
    member_permissions = member.guild_permissions
    return all(getattr(member_permissions, perm, False) for perm in permissions)


def format_datetime(dt) -> str:
    """
    Formatea una fecha/hora a string legible
    
    Args:
        dt: datetime object
    
    Returns:
        String formateado
    """
    return dt.strftime("%d/%m/%Y %H:%M:%S") if dt else "N/A"


def truncate_text(text: str, max_length: int = 1024) -> str:
    """
    Trunca un texto si excede la longitud máxima
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
    
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


async def send_log(guild: discord.Guild, log_channel_id: Optional[int], embed: discord.Embed):
    """
    Envía un mensaje de log al canal configurado
    
    Args:
        guild: El servidor de Discord
        log_channel_id: ID del canal de logs
        embed: El embed a enviar
    """
    if not log_channel_id:
        return
    
    try:
        channel = guild.get_channel(log_channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Error al enviar log: {e}")
