"""
Sistema de economía con Zero Coins para el bot
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
DAILY_REWARD = 100
WORK_REWARD_MIN = 50
WORK_REWARD_MAX = 150
WORK_COOLDOWN = 3600  # 1 hora en segundos
DAILY_COOLDOWN = 86400  # 24 horas en segundos


class EconomyCog(commands.Cog):
    """Sistema de economía con Zero Coins"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="balance", description="Ver tu balance de Zero Coins")
    async def balance(self, interaction: discord.Interaction, usuario: discord.Member = None):
        """Muestra el balance de Zero Coins de un usuario"""
        target = usuario or interaction.user
        
        balance = await db_manager.get_balance(target.id, interaction.guild.id)
        
        if balance is None:
            balance = 0
        
        embed = discord.Embed(
            title=f"💰 Balance de {target.name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(
            name="Zero Coins",
            value=f"⏰ **{balance}** Zero Coins",
            inline=False
        )
        
        # Obtener nivel si existe
        user_data = await db_manager.get_user_level_data(target.id, interaction.guild.id)
        if user_data:
            level = user_data.get('level', 1)
            embed.add_field(name="Nivel", value=f"⭐ {level}", inline=True)
        
        embed.set_footer(text=f"Usa /daily y /work para ganar más Zero Coins")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="daily", description="Reclamar tu recompensa diaria")
    async def daily(self, interaction: discord.Interaction):
        """Reclama la recompensa diaria de Zero Coins"""
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        # Verificar última vez que usó daily
        last_daily = await db_manager.get_last_daily(user_id, guild_id)
        
        if last_daily:
            try:
                last_time = datetime.fromisoformat(last_daily) if isinstance(last_daily, str) else last_daily
                time_diff = datetime.now() - last_time
                
                if time_diff.total_seconds() < DAILY_COOLDOWN:
                    remaining = DAILY_COOLDOWN - time_diff.total_seconds()
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)
                    
                    embed = discord.Embed(
                        title="⏰ Recompensa no disponible",
                        description=f"Ya reclamaste tu recompensa diaria hoy.\n\n**Tiempo restante:** {hours}h {minutes}m",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            except:
                pass
        
        # Dar recompensa
        await db_manager.add_money(user_id, guild_id, DAILY_REWARD)
        await db_manager.update_last_daily(user_id, guild_id)
        
        embed = discord.Embed(
            title="🎁 ¡Recompensa Diaria!",
            description=f"¡Recibiste **{DAILY_REWARD}** ⏰ Zero Coins!\n\nVuelve mañana para reclamar más.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"{interaction.user.name} reclamó su recompensa diaria")
    
    @app_commands.command(name="work", description="Trabajar para ganar Zero Coins")
    async def work(self, interaction: discord.Interaction):
        """Trabaja para ganar Zero Coins"""
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        # Verificar última vez que trabajó
        last_work = await db_manager.get_last_work(user_id, guild_id)
        
        if last_work:
            try:
                last_time = datetime.fromisoformat(last_work) if isinstance(last_work, str) else last_work
                time_diff = datetime.now() - last_time
                
                if time_diff.total_seconds() < WORK_COOLDOWN:
                    remaining = WORK_COOLDOWN - time_diff.total_seconds()
                    minutes = int(remaining // 60)
                    seconds = int(remaining % 60)
                    
                    embed = discord.Embed(
                        title="😴 Estás cansado",
                        description=f"Necesitas descansar antes de trabajar de nuevo.\n\n**Tiempo restante:** {minutes}m {seconds}s",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            except:
                pass
        
        # Calcular ganancia aleatoria
        earnings = random.randint(WORK_REWARD_MIN, WORK_REWARD_MAX)
        
        # Trabajos aleatorios
        jobs = [
            "programaste un bot de Discord",
            "moderaste el servidor",
            "organizaste un torneo",
            "ayudaste a nuevos miembros",
            "creaste memes épicos",
            "streamaste en Twitch",
            "ganaste una partida ranked",
            "editaste videos",
            "diseñaste un logo",
            "escribiste una guía"
        ]
        
        job = random.choice(jobs)
        
        # Dar recompensa
        await db_manager.add_money(user_id, guild_id, earnings)
        await db_manager.update_last_work(user_id, guild_id)
        
        embed = discord.Embed(
            title="💼 ¡Trabajo Completado!",
            description=f"**{interaction.user.mention}** {job}\n\n**Ganaste:** {earnings} ⏰ Zero Coins",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Puedes trabajar cada hora")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"{interaction.user.name} trabajó y ganó {earnings} coins")
    
    @app_commands.command(name="transfer", description="Transferir Zero Coins a otro usuario")
    async def transfer(self, interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
        """Transfiere Zero Coins a otro usuario"""
        if usuario.bot:
            await interaction.response.send_message("❌ No puedes transferir coins a bots.", ephemeral=True)
            return
        
        if usuario.id == interaction.user.id:
            await interaction.response.send_message("❌ No puedes transferirte coins a ti mismo.", ephemeral=True)
            return
        
        if cantidad <= 0:
            await interaction.response.send_message("❌ La cantidad debe ser mayor a 0.", ephemeral=True)
            return
        
        # Verificar balance del remitente
        sender_balance = await db_manager.get_balance(interaction.user.id, interaction.guild.id)
        
        if sender_balance is None or sender_balance < cantidad:
            await interaction.response.send_message(
                f"❌ No tienes suficientes Zero Coins. Tu balance: {sender_balance or 0} ⏰",
                ephemeral=True
            )
            return
        
        # Realizar transferencia
        success = await db_manager.remove_money(interaction.user.id, interaction.guild.id, cantidad)
        
        if not success:
            await interaction.response.send_message("❌ Error al realizar la transferencia.", ephemeral=True)
            return
        
        await db_manager.add_money(usuario.id, interaction.guild.id, cantidad)
        
        embed = discord.Embed(
            title="💸 Transferencia Exitosa",
            description=f"**{interaction.user.mention}** transfirió **{cantidad}** ⏰ Zero Coins a **{usuario.mention}**",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"{interaction.user.name} transfirió {cantidad} coins a {usuario.name}")
    
    @app_commands.command(name="coinflip", description="Apuesta Zero Coins en cara o cruz")
    async def coinflip(self, interaction: discord.Interaction, lado: str, apuesta: int):
        """Juego de cara o cruz con apuesta"""
        lado = lado.lower()
        
        if lado not in ['cara', 'cruz']:
            await interaction.response.send_message("❌ Debes elegir 'cara' o 'cruz'.", ephemeral=True)
            return
        
        if apuesta <= 0:
            await interaction.response.send_message("❌ La apuesta debe ser mayor a 0.", ephemeral=True)
            return
        
        # Verificar balance
        balance = await db_manager.get_balance(interaction.user.id, interaction.guild.id)
        
        if balance is None or balance < apuesta:
            await interaction.response.send_message(
                f"❌ No tienes suficientes Zero Coins para apostar. Tu balance: {balance or 0} ⏰",
                ephemeral=True
            )
            return
        
        # Lanzar moneda
        resultado = random.choice(['cara', 'cruz'])
        
        if resultado == lado:
            # Ganó
            await db_manager.add_money(interaction.user.id, interaction.guild.id, apuesta)
            
            embed = discord.Embed(
                title="🪙 ¡GANASTE!",
                description=f"La moneda cayó en **{resultado}**\n\n**Ganaste:** {apuesta} ⏰ Zero Coins",
                color=discord.Color.green()
            )
        else:
            # Perdió
            await db_manager.remove_money(interaction.user.id, interaction.guild.id, apuesta)
            
            embed = discord.Embed(
                title="🪙 Perdiste",
                description=f"La moneda cayó en **{resultado}**\n\n**Perdiste:** {apuesta} ⏰ Zero Coins",
                color=discord.Color.red()
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="Ver el top 10 de usuarios más ricos")
    async def leaderboard(self, interaction: discord.Interaction):
        """Muestra el ranking de usuarios con más Zero Coins"""
        richest = await db_manager.get_richest_users(interaction.guild.id, limit=10)
        
        if not richest:
            embed = discord.Embed(
                title="💰 Ranking vacío",
                description="Aún no hay usuarios en el ranking económico.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="💰 TOP 10 - Usuarios Más Ricos",
            description="Los usuarios con más Zero Coins del servidor",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user_data in enumerate(richest, 1):
            user_id = user_data['user_id']
            balance = user_data['balance']
            
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except:
                name = f"Usuario {user_id}"
            
            medal = medals[i-1] if i <= 3 else f"`#{i}`"
            
            embed.add_field(
                name=f"{medal} {name}",
                value=f"⏰ {balance} Zero Coins",
                inline=False
            )
        
        embed.set_footer(text=f"Solicitado por {interaction.user.name}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="setmoney", description="[ADMIN] Establecer dinero de un usuario")
    @app_commands.checks.has_permissions(administrator=True)
    async def setmoney(self, interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
        """Establece el dinero de un usuario (solo administradores)"""
        # Obtener balance actual
        current_balance = await db_manager.get_balance(usuario.id, interaction.guild.id) or 0
        
        # Calcular diferencia
        difference = cantidad - current_balance
        
        if difference > 0:
            await db_manager.add_money(usuario.id, interaction.guild.id, difference)
        elif difference < 0:
            await db_manager.remove_money(usuario.id, interaction.guild.id, abs(difference))
        
        embed = discord.Embed(
            title="✅ Dinero Actualizado",
            description=f"Se estableció el balance de **{usuario.mention}** a **{cantidad}** ⏰ Zero Coins",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"{interaction.user.name} estableció el dinero de {usuario.name} a {cantidad}")


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(EconomyCog(bot))
    logger.info("EconomyCog cargado")
