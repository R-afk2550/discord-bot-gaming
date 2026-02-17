"""
Cog para comandos específicos de Tibia, incluyendo gestión de loot
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from database.db_manager import db_manager
from utils.embeds import (
    create_success_embed,
    create_error_embed,
    create_info_embed,
    create_tibia_loot_session_embed,
    create_tibia_loot_summary_embed
)

logger = logging.getLogger('discord_bot')


class TibiaCog(commands.Cog):
    """Comandos para el juego Tibia"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="tibia_loot_start", description="Inicia una sesión de loot para Tibia")
    async def tibia_loot_start(self, interaction: discord.Interaction):
        """Inicia una nueva sesión de loot de Tibia en el canal actual"""
        # Verificar si ya hay una sesión activa en este canal
        existing_session = await db_manager.get_active_tibia_session(interaction.channel_id)
        
        if existing_session:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sesión Activa",
                    f"Ya existe una sesión de loot activa en este canal (ID: #{existing_session['id']}). "
                    "Usa `/tibia_loot_split` para cerrarla o `/tibia_loot_cancel` para cancelarla."
                ),
                ephemeral=True
            )
            return
        
        # Crear nueva sesión
        session_id = await db_manager.create_tibia_loot_session(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            creator_id=interaction.user.id
        )
        
        # Añadir al creador como participante
        await db_manager.add_tibia_participant(session_id, interaction.user.id)
        
        logger.info(f"Sesión de loot de Tibia #{session_id} iniciada por {interaction.user.name}")
        
        await interaction.response.send_message(
            embed=create_tibia_loot_session_embed(session_id, interaction.user)
        )
    
    @app_commands.command(name="tibia_loot_join", description="Únete a la sesión de loot activa")
    async def tibia_loot_join(self, interaction: discord.Interaction):
        """Permite a un usuario unirse a la sesión de loot activa"""
        # Verificar que hay una sesión activa
        session = await db_manager.get_active_tibia_session(interaction.channel_id)
        
        if not session:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Sesión Activa",
                    "No hay ninguna sesión de loot activa en este canal. Usa `/tibia_loot_start` para crear una."
                ),
                ephemeral=True
            )
            return
        
        # Añadir participante
        await db_manager.add_tibia_participant(session['id'], interaction.user.id)
        
        # Obtener el número actual de participantes
        participants = await db_manager.get_tibia_participants(session['id'])
        
        await interaction.response.send_message(
            embed=create_success_embed(
                "Unido a la Sesión",
                f"{interaction.user.mention} se ha unido a la sesión de loot #{session['id']}. "
                f"Total de participantes: {len(participants)}"
            )
        )
    
    @app_commands.command(name="tibia_loot_add", description="Añade un item al loot")
    @app_commands.describe(
        item="Nombre del item",
        cantidad="Cantidad del item",
        valor="Valor total del item en gold pieces"
    )
    async def tibia_loot_add(
        self,
        interaction: discord.Interaction,
        item: str,
        cantidad: int,
        valor: int
    ):
        """Añade un item al loot de la sesión activa"""
        # Validar que la cantidad y valor sean positivos
        if cantidad <= 0 or valor <= 0:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Valores Inválidos",
                    "La cantidad y el valor deben ser números positivos."
                ),
                ephemeral=True
            )
            return
        
        # Verificar que hay una sesión activa
        session = await db_manager.get_active_tibia_session(interaction.channel_id)
        
        if not session:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Sesión Activa",
                    "No hay ninguna sesión de loot activa en este canal. Usa `/tibia_loot_start` para crear una."
                ),
                ephemeral=True
            )
            return
        
        # Añadir el item
        await db_manager.add_tibia_loot_item(
            session_id=session['id'],
            item_name=item,
            quantity=cantidad,
            value=valor,
            added_by=interaction.user.id
        )
        
        # Obtener el total actual
        items = await db_manager.get_tibia_loot_items(session['id'])
        total_value = sum(item['value'] for item in items)
        
        await interaction.response.send_message(
            embed=create_success_embed(
                "Item Añadido",
                f"**{item}** x{cantidad} ({valor:,} gp) añadido al loot.\n"
                f"Total acumulado: {total_value:,} gp"
            )
        )
    
    @app_commands.command(name="tibia_loot_split", description="Calcula y muestra la división del loot")
    async def tibia_loot_split(self, interaction: discord.Interaction):
        """Calcula la división del loot entre todos los participantes"""
        # Verificar que hay una sesión activa
        session = await db_manager.get_active_tibia_session(interaction.channel_id)
        
        if not session:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Sesión Activa",
                    "No hay ninguna sesión de loot activa en este canal."
                ),
                ephemeral=True
            )
            return
        
        # Obtener items y participantes
        items = await db_manager.get_tibia_loot_items(session['id'])
        participants = await db_manager.get_tibia_participants(session['id'])
        
        if not items:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Items",
                    "No se han añadido items al loot. Usa `/tibia_loot_add` para añadir items."
                ),
                ephemeral=True
            )
            return
        
        if not participants:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Participantes",
                    "No hay participantes en la sesión."
                ),
                ephemeral=True
            )
            return
        
        # Calcular totales
        total_value = sum(item['value'] for item in items)
        per_person = total_value // len(participants)
        
        # Cerrar la sesión
        await db_manager.close_tibia_session(session['id'])
        
        logger.info(f"Sesión de loot de Tibia #{session['id']} cerrada. Total: {total_value} gp, {len(participants)} participantes")
        
        # Enviar resumen
        await interaction.response.send_message(
            embed=create_tibia_loot_summary_embed(items, participants, total_value, per_person)
        )
    
    @app_commands.command(name="tibia_loot_cancel", description="Cancela la sesión de loot activa")
    async def tibia_loot_cancel(self, interaction: discord.Interaction):
        """Cancela la sesión de loot activa sin calcular división"""
        # Verificar que hay una sesión activa
        session = await db_manager.get_active_tibia_session(interaction.channel_id)
        
        if not session:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Sesión Activa",
                    "No hay ninguna sesión de loot activa en este canal."
                ),
                ephemeral=True
            )
            return
        
        # Verificar que el usuario es el creador o tiene permisos de moderador
        if interaction.user.id != session['creator_id'] and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Permisos",
                    "Solo el creador de la sesión o moderadores pueden cancelarla."
                ),
                ephemeral=True
            )
            return
        
        # Cerrar la sesión
        await db_manager.close_tibia_session(session['id'])
        
        logger.info(f"Sesión de loot de Tibia #{session['id']} cancelada por {interaction.user.name}")
        
        await interaction.response.send_message(
            embed=create_success_embed(
                "Sesión Cancelada",
                f"La sesión de loot #{session['id']} ha sido cancelada."
            )
        )
    
    @app_commands.command(name="tibia_loot_info", description="Muestra información de la sesión activa")
    async def tibia_loot_info(self, interaction: discord.Interaction):
        """Muestra información sobre la sesión de loot activa"""
        # Verificar que hay una sesión activa
        session = await db_manager.get_active_tibia_session(interaction.channel_id)
        
        if not session:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Sin Sesión Activa",
                    "No hay ninguna sesión de loot activa en este canal."
                ),
                ephemeral=True
            )
            return
        
        # Obtener items y participantes
        items = await db_manager.get_tibia_loot_items(session['id'])
        participants = await db_manager.get_tibia_participants(session['id'])
        
        # Calcular totales
        total_value = sum(item['value'] for item in items)
        per_person = total_value // len(participants) if participants else 0
        
        # Crear embed informativo
        embed = create_info_embed(
            "🗡️ Información de Sesión de Loot",
            f"Sesión #{session['id']} creada por <@{session['creator_id']}>",
            **{
                "📦 Items Registrados": str(len(items)),
                "💰 Total Acumulado": f"{total_value:,} gp",
                "👥 Participantes": str(len(participants)),
                "💵 Por Persona": f"{per_person:,} gp" if participants else "N/A"
            }
        )
        
        # Añadir lista de participantes si hay
        if participants:
            participant_mentions = [f"<@{p['user_id']}>" for p in participants]
            embed.add_field(
                name="Lista de Participantes",
                value=", ".join(participant_mentions),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(TibiaCog(bot))
    logger.info("TibiaCog cargado")
