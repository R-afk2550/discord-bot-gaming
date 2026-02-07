"""
Cog para el sistema de eventos
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from datetime import datetime, timezone
import pytz

from utils.embeds import create_event_embed, create_success_embed, create_error_embed, create_info_embed
from database.db_manager import db_manager

logger = logging.getLogger('discord_bot')


class EventsCog(commands.Cog):
    """Sistema de gestión de eventos"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_event_notifications.start()
    
    def cog_unload(self):
        """Detiene las tareas al descargar el cog"""
        self.check_event_notifications.cancel()
    
    @app_commands.command(name="evento", description="Crear un nuevo evento")
    @app_commands.describe(
        titulo="Título del evento",
        fecha="Fecha y hora (formato: DD/MM/YYYY HH:MM)",
        descripcion="Descripción del evento (opcional)"
    )
    async def evento(
        self,
        interaction: discord.Interaction,
        titulo: str,
        fecha: str,
        descripcion: str = ""
    ):
        """Crea un nuevo evento en el servidor"""
        try:
            # Parsear la fecha
            try:
                event_date = datetime.strptime(fecha, "%d/%m/%Y %H:%M")
            except ValueError:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Error de Formato",
                        "Formato de fecha incorrecto. Usa: DD/MM/YYYY HH:MM\n"
                        "Ejemplo: 25/12/2024 20:00"
                    ),
                    ephemeral=True
                )
                return
            
            # Verificar que la fecha sea futura
            if event_date <= datetime.now():
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Error",
                        "La fecha del evento debe ser en el futuro."
                    ),
                    ephemeral=True
                )
                return
            
            # Guardar evento en la base de datos
            await db_manager.create_event(
                interaction.guild.id,
                interaction.user.id,
                titulo,
                descripcion,
                event_date
            )
            
            # Crear embed del evento
            embed = create_event_embed(
                titulo,
                descripcion or "Sin descripción",
                event_date.strftime("%d/%m/%Y a las %H:%M"),
                interaction.user.mention
            )
            
            # Enviar el evento
            await interaction.response.send_message(
                content="📅 **¡Nuevo Evento Creado!** @everyone",
                embed=embed
            )
            
            logger.info(f"Evento creado por {interaction.user.name}: {titulo}")
            
        except Exception as e:
            logger.error(f"Error al crear evento: {e}")
            await interaction.response.send_message(
                embed=create_error_embed("Error", f"Ocurrió un error: {str(e)}"),
                ephemeral=True
            )
    
    @app_commands.command(name="eventos", description="Ver los próximos eventos")
    async def eventos(self, interaction: discord.Interaction):
        """Muestra todos los eventos próximos del servidor"""
        try:
            # Obtener eventos de la base de datos
            events = await db_manager.get_upcoming_events(interaction.guild.id)
            
            if not events:
                await interaction.response.send_message(
                    embed=create_info_embed(
                        "Próximos Eventos",
                        "No hay eventos programados en este momento."
                    ),
                    ephemeral=True
                )
                return
            
            # Crear embed con la lista de eventos
            embed = discord.Embed(
                title="📅 Próximos Eventos",
                description=f"Hay {len(events)} evento(s) programado(s)",
                color=0x9b59b6,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Mostrar hasta 10 eventos
            for i, event in enumerate(events[:10], 1):
                # Parsear la fecha
                event_date = datetime.fromisoformat(event['event_date'])
                
                # Obtener creador
                creator = interaction.guild.get_member(event['creator_id'])
                creator_name = creator.mention if creator else f"ID: {event['creator_id']}"
                
                # Formatear descripción
                description = event['description'] if event['description'] else "Sin descripción"
                if len(description) > 100:
                    description = description[:97] + "..."
                
                embed.add_field(
                    name=f"{i}. {event['title']}",
                    value=(
                        f"📆 {event_date.strftime('%d/%m/%Y a las %H:%M')}\n"
                        f"👤 Organizador: {creator_name}\n"
                        f"📝 {description}"
                    ),
                    inline=False
                )
            
            if len(events) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(events)} eventos")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error al obtener eventos: {e}")
            await interaction.response.send_message(
                embed=create_error_embed("Error", f"Ocurrió un error: {str(e)}"),
                ephemeral=True
            )
    
    @tasks.loop(minutes=5)
    async def check_event_notifications(self):
        """Tarea que verifica eventos para notificar (cada 5 minutos)"""
        try:
            # Obtener eventos que necesitan notificación
            events = await db_manager.get_events_to_notify()
            
            for event in events:
                try:
                    # Obtener el servidor
                    guild = self.bot.get_guild(event['guild_id'])
                    if not guild:
                        continue
                    
                    # Buscar un canal general para enviar la notificación
                    channel = None
                    for ch in guild.text_channels:
                        if ch.name.lower() in ['general', 'eventos', 'announcements', 'anuncios']:
                            channel = ch
                            break
                    
                    if not channel:
                        # Usar el primer canal donde el bot pueda escribir
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                channel = ch
                                break
                    
                    if channel:
                        # Parsear fecha
                        event_date = datetime.fromisoformat(event['event_date'])
                        
                        # Obtener creador
                        creator = guild.get_member(event['creator_id'])
                        creator_mention = creator.mention if creator else "Desconocido"
                        
                        # Crear embed de recordatorio
                        embed = create_event_embed(
                            f"🔔 Recordatorio: {event['title']}",
                            event['description'] or "Sin descripción",
                            event_date.strftime("%d/%m/%Y a las %H:%M"),
                            creator_mention
                        )
                        embed.add_field(
                            name="⏰ ¡Comienza en menos de 1 hora!",
                            value="Prepárate para participar",
                            inline=False
                        )
                        
                        # Enviar notificación
                        await channel.send(content="@everyone", embed=embed)
                        
                        # Marcar como notificado
                        await db_manager.mark_event_notified(event['id'])
                        
                        logger.info(f"Notificación de evento enviada: {event['title']}")
                
                except Exception as e:
                    logger.error(f"Error al notificar evento {event.get('id')}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error en check_event_notifications: {e}")
    
    @check_event_notifications.before_loop
    async def before_check_notifications(self):
        """Espera a que el bot esté listo antes de iniciar la tarea"""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(EventsCog(bot))
    logger.info("EventsCog cargado")
