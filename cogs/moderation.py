"""
Cog para comandos de moderación
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional
from datetime import timedelta

from config.settings import LOG_CHANNEL_ID
from utils.embeds import (
    create_success_embed,
    create_error_embed,
    create_warning_embed,
    create_info_embed
)
from utils.helpers import has_permissions, send_log
from database.db_manager import db_manager

logger = logging.getLogger('discord_bot')


class ModerationCog(commands.Cog):
    """Comandos de moderación del servidor"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="kick", description="Expulsar a un usuario del servidor")
    @app_commands.describe(
        usuario="El usuario a expulsar",
        razon="La razón de la expulsión (opcional)"
    )
    @app_commands.default_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        razon: Optional[str] = "No se especificó razón"
    ):
        """Expulsa a un usuario del servidor"""
        # Verificar permisos
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Permisos",
                    "No tienes permisos para expulsar miembros."
                ),
                ephemeral=True
            )
            return
        
        # No se puede expulsar al dueño del servidor
        if usuario.id == interaction.guild.owner_id:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No puedes expulsar al dueño del servidor."
                ),
                ephemeral=True
            )
            return
        
        # No se puede expulsar a alguien con rol superior
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No puedes expulsar a alguien con un rol igual o superior al tuyo."
                ),
                ephemeral=True
            )
            return
        
        try:
            # Intentar enviar DM al usuario
            try:
                dm_embed = create_warning_embed(
                    f"Expulsado de {interaction.guild.name}",
                    f"Has sido expulsado por {interaction.user.mention}\n**Razón:** {razon}"
                )
                await usuario.send(embed=dm_embed)
            except:
                pass  # Si no se puede enviar DM, continuar de todas formas
            
            # Expulsar al usuario
            await usuario.kick(reason=f"Por {interaction.user.name}: {razon}")
            
            # Responder al moderador
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Usuario Expulsado",
                    f"{usuario.mention} ha sido expulsado.\n**Razón:** {razon}"
                )
            )
            
            # Log
            log_embed = create_warning_embed(
                "Usuario Expulsado",
                f"**Usuario:** {usuario.mention} ({usuario.id})\n"
                f"**Moderador:** {interaction.user.mention}\n"
                f"**Razón:** {razon}"
            )
            await send_log(interaction.guild, LOG_CHANNEL_ID, log_embed)
            
            logger.info(f"{usuario.name} fue expulsado por {interaction.user.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No tengo permisos suficientes para expulsar a este usuario."
                ),
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error al expulsar usuario: {e}")
            await interaction.response.send_message(
                embed=create_error_embed("Error", f"Ocurrió un error: {str(e)}"),
                ephemeral=True
            )
    
    @app_commands.command(name="ban", description="Banear a un usuario del servidor")
    @app_commands.describe(
        usuario="El usuario a banear",
        razon="La razón del baneo (opcional)",
        eliminar_mensajes="Días de mensajes a eliminar (0-7)"
    )
    @app_commands.default_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        razon: Optional[str] = "No se especificó razón",
        eliminar_mensajes: Optional[int] = 0
    ):
        """Banea a un usuario del servidor"""
        # Verificar permisos
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Permisos",
                    "No tienes permisos para banear miembros."
                ),
                ephemeral=True
            )
            return
        
        # No se puede banear al dueño del servidor
        if usuario.id == interaction.guild.owner_id:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No puedes banear al dueño del servidor."
                ),
                ephemeral=True
            )
            return
        
        # No se puede banear a alguien con rol superior
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No puedes banear a alguien con un rol igual o superior al tuyo."
                ),
                ephemeral=True
            )
            return
        
        # Validar días de mensajes a eliminar
        if eliminar_mensajes < 0 or eliminar_mensajes > 7:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "Los días de mensajes a eliminar deben estar entre 0 y 7."
                ),
                ephemeral=True
            )
            return
        
        try:
            # Intentar enviar DM al usuario
            try:
                dm_embed = create_error_embed(
                    f"Baneado de {interaction.guild.name}",
                    f"Has sido baneado por {interaction.user.mention}\n**Razón:** {razon}"
                )
                await usuario.send(embed=dm_embed)
            except:
                pass
            
            # Banear al usuario
            await usuario.ban(
                reason=f"Por {interaction.user.name}: {razon}",
                delete_message_days=eliminar_mensajes
            )
            
            # Responder al moderador
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Usuario Baneado",
                    f"{usuario.mention} ha sido baneado.\n**Razón:** {razon}"
                )
            )
            
            # Log
            log_embed = create_error_embed(
                "Usuario Baneado",
                f"**Usuario:** {usuario.mention} ({usuario.id})\n"
                f"**Moderador:** {interaction.user.mention}\n"
                f"**Razón:** {razon}\n"
                f"**Mensajes eliminados:** {eliminar_mensajes} días"
            )
            await send_log(interaction.guild, LOG_CHANNEL_ID, log_embed)
            
            logger.info(f"{usuario.name} fue baneado por {interaction.user.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No tengo permisos suficientes para banear a este usuario."
                ),
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error al banear usuario: {e}")
            await interaction.response.send_message(
                embed=create_error_embed("Error", f"Ocurrió un error: {str(e)}"),
                ephemeral=True
            )
    
    @app_commands.command(name="warn", description="Advertir a un usuario")
    @app_commands.describe(
        usuario="El usuario a advertir",
        razon="La razón de la advertencia"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        razon: str
    ):
        """Advierte a un usuario y guarda el registro en la base de datos"""
        # Verificar permisos
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Permisos",
                    "No tienes permisos para advertir miembros."
                ),
                ephemeral=True
            )
            return
        
        try:
            # Guardar advertencia en la base de datos
            await db_manager.add_warning(
                usuario.id,
                interaction.guild.id,
                interaction.user.id,
                razon
            )
            
            # Obtener número total de advertencias
            warning_count = await db_manager.get_warning_count(usuario.id, interaction.guild.id)
            
            # Intentar enviar DM al usuario
            try:
                dm_embed = create_warning_embed(
                    f"Advertencia en {interaction.guild.name}",
                    f"Has recibido una advertencia de {interaction.user.mention}\n"
                    f"**Razón:** {razon}\n"
                    f"**Total de advertencias:** {warning_count}"
                )
                await usuario.send(embed=dm_embed)
            except:
                pass
            
            # Responder al moderador
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Advertencia Registrada",
                    f"{usuario.mention} ha sido advertido.\n"
                    f"**Razón:** {razon}\n"
                    f"**Total de advertencias:** {warning_count}"
                )
            )
            
            # Log
            log_embed = create_warning_embed(
                "Usuario Advertido",
                f"**Usuario:** {usuario.mention} ({usuario.id})\n"
                f"**Moderador:** {interaction.user.mention}\n"
                f"**Razón:** {razon}\n"
                f"**Total advertencias:** {warning_count}"
            )
            await send_log(interaction.guild, LOG_CHANNEL_ID, log_embed)
            
            logger.info(f"{usuario.name} fue advertido por {interaction.user.name}")
            
        except Exception as e:
            logger.error(f"Error al advertir usuario: {e}")
            await interaction.response.send_message(
                embed=create_error_embed("Error", f"Ocurrió un error: {str(e)}"),
                ephemeral=True
            )
    
    @app_commands.command(name="warnings", description="Ver las advertencias de un usuario")
    @app_commands.describe(usuario="El usuario cuyas advertencias quieres ver")
    async def warnings(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member
    ):
        """Muestra todas las advertencias de un usuario"""
        try:
            warnings = await db_manager.get_warnings(usuario.id, interaction.guild.id)
            
            if not warnings:
                await interaction.response.send_message(
                    embed=create_info_embed(
                        "Advertencias",
                        f"{usuario.mention} no tiene advertencias."
                    ),
                    ephemeral=True
                )
                return
            
            # Crear embed con las advertencias
            embed = create_warning_embed(
                f"Advertencias de {usuario.display_name}",
                f"Total: {len(warnings)} advertencias"
            )
            
            # Mostrar las últimas 10 advertencias
            for i, warning in enumerate(warnings[:10], 1):
                moderator = interaction.guild.get_member(warning['moderator_id'])
                mod_name = moderator.mention if moderator else f"ID: {warning['moderator_id']}"
                
                embed.add_field(
                    name=f"#{i} - {warning['timestamp']}",
                    value=f"**Moderador:** {mod_name}\n**Razón:** {warning['reason']}",
                    inline=False
                )
            
            if len(warnings) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(warnings)} advertencias")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error al obtener advertencias: {e}")
            await interaction.response.send_message(
                embed=create_error_embed("Error", f"Ocurrió un error: {str(e)}"),
                ephemeral=True
            )
    
    @app_commands.command(name="clear", description="Eliminar mensajes del canal")
    @app_commands.describe(cantidad="Cantidad de mensajes a eliminar (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(
        self,
        interaction: discord.Interaction,
        cantidad: int
    ):
        """Elimina una cantidad específica de mensajes del canal"""
        # Verificar permisos
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Permisos",
                    "No tienes permisos para gestionar mensajes."
                ),
                ephemeral=True
            )
            return
        
        # Validar cantidad
        if cantidad < 1 or cantidad > 100:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "La cantidad debe estar entre 1 y 100."
                ),
                ephemeral=True
            )
            return
        
        try:
            # Eliminar mensajes
            deleted = await interaction.channel.purge(limit=cantidad)
            
            # Responder (mensaje se auto-eliminará)
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Mensajes Eliminados",
                    f"Se eliminaron {len(deleted)} mensajes."
                ),
                delete_after=5
            )
            
            # Log
            log_embed = create_info_embed(
                "Mensajes Eliminados",
                f"**Canal:** {interaction.channel.mention}\n"
                f"**Moderador:** {interaction.user.mention}\n"
                f"**Cantidad:** {len(deleted)} mensajes"
            )
            await send_log(interaction.guild, LOG_CHANNEL_ID, log_embed)
            
            logger.info(f"{interaction.user.name} eliminó {len(deleted)} mensajes en {interaction.channel.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No tengo permisos suficientes para eliminar mensajes."
                ),
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error al eliminar mensajes: {e}")
            await interaction.response.send_message(
                embed=create_error_embed("Error", f"Ocurrió un error: {str(e)}"),
                ephemeral=True
            )
    
    @app_commands.command(name="mute", description="Silenciar a un usuario temporalmente")
    @app_commands.describe(
        usuario="El usuario a silenciar",
        tiempo="Tiempo en minutos (opcional, default: 10)"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        tiempo: Optional[int] = 10
    ):
        """Silencia a un usuario por un tiempo determinado"""
        # Verificar permisos
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Permisos",
                    "No tienes permisos para silenciar miembros."
                ),
                ephemeral=True
            )
            return
        
        # Validar tiempo (máximo 28 días = 40320 minutos)
        if tiempo < 1 or tiempo > 40320:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "El tiempo debe estar entre 1 minuto y 28 días (40320 minutos)."
                ),
                ephemeral=True
            )
            return
        
        try:
            # Silenciar al usuario
            duration = timedelta(minutes=tiempo)
            await usuario.timeout(duration, reason=f"Silenciado por {interaction.user.name}")
            
            # Intentar enviar DM al usuario
            try:
                dm_embed = create_warning_embed(
                    f"Silenciado en {interaction.guild.name}",
                    f"Has sido silenciado por {interaction.user.mention}\n"
                    f"**Duración:** {tiempo} minutos"
                )
                await usuario.send(embed=dm_embed)
            except:
                pass
            
            # Responder al moderador
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Usuario Silenciado",
                    f"{usuario.mention} ha sido silenciado por {tiempo} minutos."
                )
            )
            
            # Log
            log_embed = create_warning_embed(
                "Usuario Silenciado",
                f"**Usuario:** {usuario.mention} ({usuario.id})\n"
                f"**Moderador:** {interaction.user.mention}\n"
                f"**Duración:** {tiempo} minutos"
            )
            await send_log(interaction.guild, LOG_CHANNEL_ID, log_embed)
            
            logger.info(f"{usuario.name} fue silenciado por {interaction.user.name} ({tiempo} min)")
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Error",
                    "No tengo permisos suficientes para silenciar a este usuario."
                ),
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error al silenciar usuario: {e}")
            await interaction.response.send_message(
                embed=create_error_embed("Error", f"Ocurrió un error: {str(e)}"),
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(ModerationCog(bot))
    logger.info("ModerationCog cargado")
