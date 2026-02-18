"""
Cog para gestión de códigos de acceso residencial
Sistema para generar, validar y administrar códigos de acceso a residenciales
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
import secrets
import string
from typing import Optional, Literal
from datetime import datetime, timedelta

from database.db_manager import db_manager
from utils.embeds import create_info_embed, create_success_embed, create_error_embed

logger = logging.getLogger('discord_bot')


class ResidentialAccessCog(commands.Cog):
    """Comandos para gestión de códigos de acceso residencial"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def generate_access_code(self, length: int = 6, include_letters: bool = True) -> str:
        """Genera un código de acceso aleatorio"""
        if include_letters:
            characters = string.ascii_uppercase + string.digits
        else:
            characters = string.digits
        
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @app_commands.command(
        name="generar_codigo",
        description="Generar código de acceso residencial"
    )
    @app_commands.describe(
        residente="Nombre del residente o visitante",
        tipo="Tipo de código (temporal o permanente)",
        duracion_horas="Duración en horas (solo para códigos temporales)",
        ubicacion="Ubicación o unidad residencial",
        notas="Notas adicionales sobre el código"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def generar_codigo(
        self,
        interaction: discord.Interaction,
        residente: str,
        tipo: Literal["temporal", "permanente"] = "temporal",
        duracion_horas: int = 24,
        ubicacion: Optional[str] = None,
        notas: Optional[str] = None
    ):
        """Genera un nuevo código de acceso residencial"""
        
        # Generar código único
        code = self.generate_access_code()
        
        # Verificar que el código no exista (muy poco probable pero verificamos)
        existing = await db_manager.get_access_code_by_code(interaction.guild_id, code)
        while existing:
            code = self.generate_access_code()
            existing = await db_manager.get_access_code_by_code(interaction.guild_id, code)
        
        # Calcular fecha de expiración
        expiry_date = None
        if tipo == "temporal":
            expiry_date = datetime.now() + timedelta(hours=duracion_horas)
        
        # Guardar en base de datos
        await db_manager.create_access_code(
            guild_id=interaction.guild_id,
            code=code,
            resident_name=residente,
            code_type=tipo,
            created_by=interaction.user.id,
            expiry_date=expiry_date,
            location=ubicacion,
            notes=notas
        )
        
        # Crear embed de respuesta
        embed = create_success_embed(
            "✅ Código de Acceso Generado",
            f"Se ha generado un nuevo código de acceso exitosamente."
        )
        
        embed.add_field(name="🔑 Código", value=f"`{code}`", inline=True)
        embed.add_field(name="👤 Residente", value=residente, inline=True)
        embed.add_field(name="📋 Tipo", value=tipo.capitalize(), inline=True)
        
        if ubicacion:
            embed.add_field(name="📍 Ubicación", value=ubicacion, inline=True)
        
        if tipo == "temporal":
            expiry_str = expiry_date.strftime("%d/%m/%Y %H:%M")
            embed.add_field(name="⏰ Expira", value=expiry_str, inline=True)
            embed.add_field(name="⌛ Duración", value=f"{duracion_horas}h", inline=True)
        else:
            embed.add_field(name="♾️ Validez", value="Permanente", inline=True)
        
        if notas:
            embed.add_field(name="📝 Notas", value=notas, inline=False)
        
        embed.set_footer(text=f"Generado por {interaction.user.name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"Código de acceso {code} generado por {interaction.user.name} para {residente}")
    
    @app_commands.command(
        name="validar_codigo",
        description="Validar un código de acceso residencial"
    )
    @app_commands.describe(
        codigo="El código a validar"
    )
    async def validar_codigo(
        self,
        interaction: discord.Interaction,
        codigo: str
    ):
        """Valida un código de acceso residencial"""
        
        # Buscar código en la base de datos
        code_data = await db_manager.get_access_code_by_code(
            interaction.guild_id,
            codigo.upper()
        )
        
        if not code_data:
            embed = create_error_embed(
                "❌ Código No Encontrado",
                f"El código `{codigo.upper()}` no existe o fue revocado."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar si el código está activo
        if not code_data['is_active']:
            embed = create_error_embed(
                "❌ Código Revocado",
                f"El código `{codigo.upper()}` ha sido revocado y ya no es válido."
            )
            embed.add_field(
                name="📅 Revocado el",
                value=datetime.fromisoformat(code_data['revoked_at']).strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Verificar si el código expiró
        if code_data['expiry_date']:
            expiry = datetime.fromisoformat(code_data['expiry_date'])
            if expiry < datetime.now():
                embed = create_error_embed(
                    "❌ Código Expirado",
                    f"El código `{codigo.upper()}` expiró y ya no es válido."
                )
                embed.add_field(
                    name="⏰ Expiró el",
                    value=expiry.strftime("%d/%m/%Y %H:%M"),
                    inline=True
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Código válido - registrar el uso
        await db_manager.register_access_code_use(code_data['id'], interaction.user.id)
        
        # Crear embed de código válido
        embed = create_success_embed(
            "✅ Código Válido",
            f"El código `{codigo.upper()}` es válido y ha sido registrado."
        )
        
        embed.add_field(name="👤 Residente", value=code_data['resident_name'], inline=True)
        embed.add_field(name="📋 Tipo", value=code_data['code_type'].capitalize(), inline=True)
        
        if code_data['location']:
            embed.add_field(name="📍 Ubicación", value=code_data['location'], inline=True)
        
        if code_data['expiry_date']:
            expiry = datetime.fromisoformat(code_data['expiry_date'])
            time_left = expiry - datetime.now()
            hours_left = int(time_left.total_seconds() / 3600)
            embed.add_field(
                name="⏰ Expira en",
                value=f"{hours_left}h ({expiry.strftime('%d/%m/%Y %H:%M')})",
                inline=True
            )
        else:
            embed.add_field(name="♾️ Validez", value="Permanente", inline=True)
        
        # Mostrar número de usos
        use_count = code_data['use_count'] + 1  # +1 porque acabamos de registrar el uso
        embed.add_field(name="📊 Veces usado", value=f"{use_count}", inline=True)
        
        if code_data['notes']:
            embed.add_field(name="📝 Notas", value=code_data['notes'], inline=False)
        
        created_at = datetime.fromisoformat(code_data['created_at'])
        embed.set_footer(text=f"Creado el {created_at.strftime('%d/%m/%Y %H:%M')}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"Código {codigo.upper()} validado por {interaction.user.name}")
    
    @app_commands.command(
        name="listar_codigos",
        description="Listar códigos de acceso activos"
    )
    @app_commands.describe(
        filtro="Filtrar por tipo de código",
        residente="Buscar códigos de un residente específico"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def listar_codigos(
        self,
        interaction: discord.Interaction,
        filtro: Optional[Literal["temporal", "permanente", "todos"]] = "todos",
        residente: Optional[str] = None
    ):
        """Lista todos los códigos de acceso activos"""
        
        codes = await db_manager.get_active_access_codes(
            interaction.guild_id,
            code_type=None if filtro == "todos" else filtro,
            resident_name=residente
        )
        
        if not codes:
            embed = create_info_embed(
                "📋 Sin Códigos",
                "No hay códigos de acceso que coincidan con los filtros especificados."
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Crear embed con la lista
        title = "📋 Códigos de Acceso Activos"
        if filtro != "todos":
            title += f" ({filtro.capitalize()})"
        if residente:
            title += f" - {residente}"
        
        embed = discord.Embed(
            title=title,
            description=f"Total: **{len(codes)}** código(s) activo(s)",
            color=0x3498db
        )
        
        # Agrupar códigos (máximo 25 campos en Discord)
        for i, code in enumerate(codes[:25], 1):
            expiry_info = ""
            if code['expiry_date']:
                expiry = datetime.fromisoformat(code['expiry_date'])
                if expiry < datetime.now():
                    expiry_info = "⚠️ EXPIRADO"
                else:
                    time_left = expiry - datetime.now()
                    hours_left = int(time_left.total_seconds() / 3600)
                    expiry_info = f"⏰ {hours_left}h restantes"
            else:
                expiry_info = "♾️ Permanente"
            
            location_info = f"📍 {code['location']}" if code['location'] else ""
            
            field_value = (
                f"👤 {code['resident_name']}\n"
                f"🔑 `{code['code']}`\n"
                f"{expiry_info}"
            )
            if location_info:
                field_value += f"\n{location_info}"
            
            embed.add_field(
                name=f"{i}. {code['code_type'].capitalize()}",
                value=field_value,
                inline=True
            )
        
        if len(codes) > 25:
            embed.set_footer(text=f"Mostrando 25 de {len(codes)} códigos")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name="revocar_codigo",
        description="Revocar un código de acceso residencial"
    )
    @app_commands.describe(
        codigo="El código a revocar"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def revocar_codigo(
        self,
        interaction: discord.Interaction,
        codigo: str
    ):
        """Revoca un código de acceso residencial"""
        
        # Buscar código en la base de datos
        code_data = await db_manager.get_access_code_by_code(
            interaction.guild_id,
            codigo.upper()
        )
        
        if not code_data:
            embed = create_error_embed(
                "❌ Código No Encontrado",
                f"El código `{codigo.upper()}` no existe."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not code_data['is_active']:
            embed = create_error_embed(
                "❌ Código Ya Revocado",
                f"El código `{codigo.upper()}` ya fue revocado anteriormente."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Revocar el código
        await db_manager.revoke_access_code(code_data['id'])
        
        embed = create_success_embed(
            "✅ Código Revocado",
            f"El código `{codigo.upper()}` ha sido revocado exitosamente."
        )
        
        embed.add_field(name="👤 Residente", value=code_data['resident_name'], inline=True)
        embed.add_field(name="📋 Tipo", value=code_data['code_type'].capitalize(), inline=True)
        embed.add_field(name="📊 Veces usado", value=str(code_data['use_count']), inline=True)
        
        embed.set_footer(text=f"Revocado por {interaction.user.name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"Código {codigo.upper()} revocado por {interaction.user.name}")
    
    @app_commands.command(
        name="historial_codigo",
        description="Ver historial de uso de un código de acceso"
    )
    @app_commands.describe(
        codigo="El código a consultar"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def historial_codigo(
        self,
        interaction: discord.Interaction,
        codigo: str
    ):
        """Muestra el historial de uso de un código de acceso"""
        
        # Buscar código en la base de datos
        code_data = await db_manager.get_access_code_by_code(
            interaction.guild_id,
            codigo.upper()
        )
        
        if not code_data:
            embed = create_error_embed(
                "❌ Código No Encontrado",
                f"El código `{codigo.upper()}` no existe."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Obtener historial de usos
        history = await db_manager.get_access_code_history(code_data['id'])
        
        # Crear embed con información del código
        status = "✅ Activo" if code_data['is_active'] else "❌ Revocado"
        if code_data['expiry_date']:
            expiry = datetime.fromisoformat(code_data['expiry_date'])
            if expiry < datetime.now() and code_data['is_active']:
                status = "⚠️ Expirado"
        
        embed = discord.Embed(
            title=f"📊 Historial del Código `{codigo.upper()}`",
            description=f"**Estado:** {status}",
            color=0x3498db
        )
        
        embed.add_field(name="👤 Residente", value=code_data['resident_name'], inline=True)
        embed.add_field(name="📋 Tipo", value=code_data['code_type'].capitalize(), inline=True)
        embed.add_field(name="📊 Total de usos", value=str(code_data['use_count']), inline=True)
        
        if code_data['location']:
            embed.add_field(name="📍 Ubicación", value=code_data['location'], inline=True)
        
        created_at = datetime.fromisoformat(code_data['created_at'])
        embed.add_field(
            name="📅 Creado",
            value=created_at.strftime("%d/%m/%Y %H:%M"),
            inline=True
        )
        
        if code_data['expiry_date']:
            expiry = datetime.fromisoformat(code_data['expiry_date'])
            embed.add_field(
                name="⏰ Expira",
                value=expiry.strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
        
        if not code_data['is_active'] and code_data['revoked_at']:
            revoked = datetime.fromisoformat(code_data['revoked_at'])
            embed.add_field(
                name="🚫 Revocado",
                value=revoked.strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
        
        # Agregar historial de usos recientes
        if history:
            history_text = ""
            for entry in history[:10]:  # Últimos 10 usos
                used_at = datetime.fromisoformat(entry['used_at'])
                user_id = entry['used_by']
                history_text += f"• <@{user_id}> - {used_at.strftime('%d/%m/%Y %H:%M')}\n"
            
            embed.add_field(
                name=f"📜 Últimos Usos ({len(history[:10])} de {len(history)})",
                value=history_text or "Sin registros",
                inline=False
            )
        else:
            embed.add_field(name="📜 Historial de Usos", value="Sin usos registrados", inline=False)
        
        if code_data['notes']:
            embed.add_field(name="📝 Notas", value=code_data['notes'], inline=False)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(ResidentialAccessCog(bot))
