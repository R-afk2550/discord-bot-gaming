"""
Sistema completo de integración con Tibia para Discord Bot
Incluye 10 módulos principales con comandos slash
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
import aiohttp
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from database.db_manager import db_manager
import asyncio

logger = logging.getLogger('discord_bot')

# Constantes de Tibia
TIBIA_BLUE = 0x1D4E89
TIBIA_GREEN = 0x00A86B
TIBIA_API_BASE = "https://api.tibiadata.com/v4"

# Ubicaciones de Rashid por día de la semana (0=Lunes, 6=Domingo)
RASHID_LOCATIONS = {
    0: {"city": "Svargrond", "location": "Dankwart's tavern, one floor up"},
    1: {"city": "Liberty Bay", "location": "Lyonel's tavern, second floor"},
    2: {"city": "Port Hope", "location": "Clyde's tavern, ground floor"},
    3: {"city": "Ankrahmun", "location": "Arito's tavern, ground floor"},
    4: {"city": "Darashia", "location": "Razan's tavern, ground floor"},
    5: {"city": "Edron", "location": "Mirabell's tavern, second floor"},
    6: {"city": "Carlin", "location": "Tuck's tavern, second floor"}
}

# Cache simple para respuestas de API (5 minutos)
api_cache = {}
CACHE_DURATION = 300  # 5 minutos en segundos


class TibiaCog(commands.Cog):
    """Sistema completo de integración con Tibia"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = None
    
    async def cog_load(self):
        """Inicializa la sesión de aiohttp al cargar el cog"""
        self.session = aiohttp.ClientSession()
        logger.info("Sesión HTTP inicializada para TibiaCog")
    
    async def cog_unload(self):
        """Cierra la sesión de aiohttp al descargar el cog"""
        if self.session:
            await self.session.close()
            logger.info("Sesión HTTP cerrada para TibiaCog")
    
    # ===== FUNCIONES AUXILIARES =====
    
    async def fetch_tibia_api(self, endpoint: str) -> Optional[Dict]:
        """
        Realiza una petición a la API de Tibia con manejo de errores y caché
        
        Args:
            endpoint: Endpoint de la API (ej: "/character/Name")
            
        Returns:
            Diccionario con la respuesta o None si hay error
        """
        url = f"{TIBIA_API_BASE}{endpoint}"
        
        # Verificar caché
        cache_key = url
        if cache_key in api_cache:
            cached_data, timestamp = api_cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < CACHE_DURATION:
                logger.debug(f"Usando caché para {endpoint}")
                return cached_data
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    # Guardar en caché
                    api_cache[cache_key] = (data, datetime.now())
                    logger.debug(f"API request exitoso: {endpoint}")
                    return data
                else:
                    logger.error(f"API request falló: {endpoint} - Status {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout en API request: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Error en API request: {endpoint} - {e}")
            return None
    
    def format_number(self, num: int) -> str:
        """
        Formatea números grandes al estilo de Tibia (1kk, 100k, etc.)
        
        Args:
            num: Número a formatear
            
        Returns:
            String formateado
        """
        if num >= 1000000:
            return f"{num / 1000000:.2f}kk"
        elif num >= 1000:
            return f"{num / 1000:.1f}k"
        else:
            return str(num)
    
    def get_rashid_location(self, days_offset: int = 0) -> Dict[str, str]:
        """
        Calcula la ubicación de Rashid según el día de la semana
        
        Args:
            days_offset: Días a sumar (0=hoy, 1=mañana, etc.)
            
        Returns:
            Diccionario con city y location
        """
        target_date = datetime.now() + timedelta(days=days_offset)
        weekday = target_date.weekday()
        return RASHID_LOCATIONS[weekday]
    
    def calculate_exp_needed(self, current_level: int, target_level: int) -> int:
        """
        Calcula la experiencia necesaria entre dos niveles
        Fórmula de Tibia: 50/3 * (nivel³ - nivel_anterior³)
        
        Args:
            current_level: Nivel actual
            target_level: Nivel objetivo
            
        Returns:
            Experiencia total necesaria
        """
        if target_level <= current_level:
            return 0
        
        exp_needed = 0
        for level in range(current_level + 1, target_level + 1):
            exp_needed += int((50 / 3) * ((level ** 3) - ((level - 1) ** 3)))
        
        return exp_needed
    
    # ===== MÓDULO 1: SISTEMA DE LOOT TRACKER =====
    
    loot_group = app_commands.Group(name="loot", description="Sistema de registro de loots de Tibia")
    
    @loot_group.command(name="registrar", description="Registrar un loot obtenido")
    @app_commands.describe(
        boss="Nombre del boss o criatura",
        items="Items obtenidos (separados por comas)",
        valor="Valor total del loot en gold (opcional)"
    )
    async def loot_registrar(
        self, 
        interaction: discord.Interaction, 
        boss: str, 
        items: str, 
        valor: int = 0
    ):
        """Registra un loot obtenido en una hunt o boss"""
        try:
            await db_manager.add_tibia_loot(
                interaction.user.id,
                interaction.guild.id,
                boss,
                items,
                valor
            )
            
            embed = discord.Embed(
                title="💰 Loot Registrado",
                description=f"**Boss/Criatura:** {boss}\n**Items:** {items}",
                color=TIBIA_GREEN
            )
            
            if valor > 0:
                embed.add_field(
                    name="Valor",
                    value=f"{self.format_number(valor)} gp",
                    inline=False
                )
            
            embed.set_footer(text=f"Registrado por {interaction.user.name}")
            embed.timestamp = datetime.now()
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"{interaction.user.name} registró loot: {boss} - {valor}gp")
            
        except Exception as e:
            logger.error(f"Error al registrar loot: {e}")
            await interaction.response.send_message(
                "❌ Error al registrar el loot. Por favor intenta de nuevo.",
                ephemeral=True
            )
    
    @loot_group.command(name="historial", description="Ver historial de loots")
    @app_commands.describe(usuario="Usuario del que ver el historial (opcional)")
    async def loot_historial(
        self, 
        interaction: discord.Interaction, 
        usuario: Optional[discord.Member] = None
    ):
        """Muestra el historial de loots de un usuario"""
        target = usuario or interaction.user
        
        try:
            loots = await db_manager.get_user_loots(target.id, interaction.guild.id, limit=10)
            
            if not loots:
                await interaction.response.send_message(
                    f"📊 {target.mention} no tiene loots registrados aún.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"📜 Historial de Loots - {target.name}",
                color=TIBIA_BLUE
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            for loot in loots[:10]:
                timestamp = datetime.fromisoformat(loot['timestamp'])
                value_str = f"{self.format_number(loot['value'])} gp" if loot['value'] > 0 else "N/A"
                
                embed.add_field(
                    name=f"🗡️ {loot['boss_name']}",
                    value=f"**Items:** {loot['items'][:100]}...\n**Valor:** {value_str}\n**Fecha:** {timestamp.strftime('%d/%m/%Y %H:%M')}",
                    inline=False
                )
            
            embed.set_footer(text=f"Mostrando últimos {len(loots)} loots")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener historial: {e}")
            await interaction.response.send_message(
                "❌ Error al obtener el historial.",
                ephemeral=True
            )
    
    @loot_group.command(name="stats", description="Estadísticas de drops por criatura")
    @app_commands.describe(criatura="Nombre de la criatura (opcional, muestra top 10 si no se especifica)")
    async def loot_stats(
        self, 
        interaction: discord.Interaction, 
        criatura: Optional[str] = None
    ):
        """Muestra estadísticas de drops por criatura"""
        try:
            stats = await db_manager.get_boss_stats(interaction.guild.id, criatura)
            
            if not stats:
                msg = f"📊 No hay estadísticas para '{criatura}'." if criatura else "📊 No hay loots registrados en este servidor."
                await interaction.response.send_message(msg, ephemeral=True)
                return
            
            if criatura:
                # Estadísticas de una criatura específica
                stat = stats[0]
                embed = discord.Embed(
                    title=f"📊 Estadísticas - {stat['boss_name']}",
                    color=TIBIA_BLUE
                )
                embed.add_field(name="Kills", value=f"⚔️ {stat['kills']}", inline=True)
                embed.add_field(
                    name="Promedio", 
                    value=f"💰 {self.format_number(int(stat['avg_value']))} gp", 
                    inline=True
                )
                embed.add_field(
                    name="Total", 
                    value=f"💎 {self.format_number(int(stat['total_value']))} gp", 
                    inline=True
                )
                embed.add_field(
                    name="Mejor Loot", 
                    value=f"🏆 {self.format_number(int(stat['best_loot']))} gp", 
                    inline=False
                )
            else:
                # Top 10 criaturas más cazadas
                embed = discord.Embed(
                    title="📊 Top 10 Criaturas Cazadas",
                    description="Criaturas con más kills en el servidor",
                    color=TIBIA_BLUE
                )
                
                for i, stat in enumerate(stats[:10], 1):
                    embed.add_field(
                        name=f"{i}. {stat['boss_name']}",
                        value=f"⚔️ {stat['kills']} kills | 💰 {self.format_number(int(stat['avg_value']))} gp promedio",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener stats: {e}")
            await interaction.response.send_message(
                "❌ Error al obtener estadísticas.",
                ephemeral=True
            )
    
    @loot_group.command(name="mejores", description="Top 10 mejores loots registrados")
    async def loot_mejores(self, interaction: discord.Interaction):
        """Muestra los 10 mejores loots del servidor"""
        try:
            top_loots = await db_manager.get_top_loots(interaction.guild.id, limit=10)
            
            if not top_loots:
                await interaction.response.send_message(
                    "📊 No hay loots registrados en este servidor aún.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="🏆 Top 10 Mejores Loots",
                description="Los loots más valiosos del servidor",
                color=0xFFD700  # Dorado
            )
            
            for i, loot in enumerate(top_loots, 1):
                user = await self.bot.fetch_user(loot['user_id'])
                username = user.name if user else "Usuario Desconocido"
                timestamp = datetime.fromisoformat(loot['timestamp'])
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                embed.add_field(
                    name=f"{medal} {loot['boss_name']} - {self.format_number(loot['value'])} gp",
                    value=f"**Por:** {username}\n**Fecha:** {timestamp.strftime('%d/%m/%Y')}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener mejores loots: {e}")
            await interaction.response.send_message(
                "❌ Error al obtener los mejores loots.",
                ephemeral=True
            )
    
    @loot_group.command(name="total", description="Valor total de loots ganados")
    @app_commands.describe(usuario="Usuario del que ver el total (opcional)")
    async def loot_total(
        self, 
        interaction: discord.Interaction, 
        usuario: Optional[discord.Member] = None
    ):
        """Muestra el valor total de loots ganados por un usuario"""
        target = usuario or interaction.user
        
        try:
            total = await db_manager.get_total_loot_value(target.id, interaction.guild.id)
            
            embed = discord.Embed(
                title=f"💎 Valor Total de Loots",
                description=f"**Usuario:** {target.mention}",
                color=TIBIA_GREEN
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(
                name="Total Acumulado",
                value=f"💰 **{self.format_number(total)} gp**",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener total de loots: {e}")
            await interaction.response.send_message(
                "❌ Error al obtener el total.",
                ephemeral=True
            )
    
    # ===== MÓDULO 2: INFORMACIÓN DE PERSONAJES =====
    
    tibia_group = app_commands.Group(name="tibia", description="Comandos de información de Tibia")
    
    @tibia_group.command(name="char", description="Ver estadísticas de un personaje")
    @app_commands.describe(nombre="Nombre del personaje")
    async def tibia_char(self, interaction: discord.Interaction, nombre: str):
        """Muestra información detallada de un personaje de Tibia"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api(f"/character/{nombre}")
            
            if not data or 'character' not in data or 'character' not in data['character']:
                await interaction.followup.send(
                    f"❌ No se encontró el personaje **{nombre}**. Verifica el nombre e intenta de nuevo.",
                    ephemeral=True
                )
                return
            
            char_data = data['character']['character']
            
            embed = discord.Embed(
                title=f"👤 {char_data['name']}",
                color=TIBIA_BLUE
            )
            
            # Información básica
            embed.add_field(name="Nivel", value=f"⭐ {char_data['level']}", inline=True)
            embed.add_field(name="Vocación", value=f"🎯 {char_data['vocation']}", inline=True)
            embed.add_field(name="Mundo", value=f"🌍 {char_data['world']}", inline=True)
            
            if 'guild' in char_data and char_data['guild']:
                guild_info = char_data['guild']
                embed.add_field(
                    name="Guild",
                    value=f"🛡️ {guild_info['name']}\n*{guild_info.get('rank', 'Member')}*",
                    inline=False
                )
            
            # Achievement points
            if 'achievement_points' in char_data:
                embed.add_field(
                    name="Achievement Points",
                    value=f"🏆 {char_data['achievement_points']}",
                    inline=True
                )
            
            # Residence
            if 'residence' in char_data:
                embed.add_field(
                    name="Residencia",
                    value=f"🏠 {char_data['residence']}",
                    inline=True
                )
            
            # Account status
            status_text = "✅ Online" if char_data.get('status') == 'online' else "⭕ Offline"
            embed.add_field(name="Estado", value=status_text, inline=True)
            
            embed.set_footer(text="Datos obtenidos de TibiaData API")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener personaje: {e}")
            await interaction.followup.send(
                "❌ Error al obtener información del personaje.",
                ephemeral=True
            )
    
    @tibia_group.command(name="online", description="Ver jugadores online en un mundo")
    @app_commands.describe(mundo="Nombre del mundo de Tibia")
    async def tibia_online(self, interaction: discord.Interaction, mundo: str):
        """Muestra los jugadores online en un mundo específico"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api(f"/world/{mundo}")
            
            if not data or 'world' not in data or 'world' not in data['world']:
                await interaction.followup.send(
                    f"❌ No se encontró el mundo **{mundo}**.",
                    ephemeral=True
                )
                return
            
            world_data = data['world']['world']
            online_players = data['world'].get('online_players', [])
            
            embed = discord.Embed(
                title=f"🌍 {world_data['name']} - Jugadores Online",
                description=f"**{world_data['players_online']}** jugadores online",
                color=TIBIA_GREEN
            )
            
            embed.add_field(
                name="Información del Mundo",
                value=f"**Tipo:** {world_data.get('world_type', 'N/A')}\n"
                      f"**PvP Type:** {world_data.get('pvp_type', 'N/A')}\n"
                      f"**Location:** {world_data.get('location', 'N/A')}",
                inline=False
            )
            
            if online_players:
                # Mostrar top 20 jugadores por nivel
                top_players = sorted(online_players, key=lambda x: x['level'], reverse=True)[:20]
                
                players_text = "\n".join([
                    f"**{p['name']}** - Lvl {p['level']} ({p['vocation']})"
                    for p in top_players
                ])
                
                embed.add_field(
                    name=f"Top 20 por Nivel",
                    value=players_text[:1024] if len(players_text) < 1024 else players_text[:1020] + "...",
                    inline=False
                )
            
            embed.set_footer(text="Datos actualizados")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener mundo: {e}")
            await interaction.followup.send(
                "❌ Error al obtener información del mundo.",
                ephemeral=True
            )
    
    @tibia_group.command(name="deaths", description="Ver últimas muertes de un personaje")
    @app_commands.describe(nombre="Nombre del personaje")
    async def tibia_deaths(self, interaction: discord.Interaction, nombre: str):
        """Muestra las últimas muertes de un personaje"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api(f"/character/{nombre}")
            
            if not data or 'character' not in data:
                await interaction.followup.send(
                    f"❌ No se encontró el personaje **{nombre}**.",
                    ephemeral=True
                )
                return
            
            deaths = data['character'].get('deaths', [])
            
            if not deaths:
                await interaction.followup.send(
                    f"✨ **{nombre}** no tiene muertes recientes registradas.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"💀 Muertes Recientes - {nombre}",
                color=discord.Color.red()
            )
            
            for i, death in enumerate(deaths[:10], 1):
                killers = death.get('killers', [])
                killer_names = ", ".join([k.get('name', 'Unknown') for k in killers[:3]])
                
                if len(killers) > 3:
                    killer_names += f" y {len(killers) - 3} más"
                
                level = death.get('level', 'N/A')
                time = death.get('time', 'N/A')
                
                embed.add_field(
                    name=f"💀 Muerte {i}",
                    value=f"**Nivel:** {level}\n**Asesinado por:** {killer_names}\n**Fecha:** {time}",
                    inline=False
                )
            
            embed.set_footer(text=f"Mostrando últimas {min(len(deaths), 10)} muertes")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener muertes: {e}")
            await interaction.followup.send(
                "❌ Error al obtener las muertes del personaje.",
                ephemeral=True
            )
    
    @tibia_group.command(name="guild", description="Ver información de una guild")
    @app_commands.describe(nombre="Nombre de la guild")
    async def tibia_guild(self, interaction: discord.Interaction, nombre: str):
        """Muestra información de una guild de Tibia"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api(f"/guild/{nombre}")
            
            if not data or 'guild' not in data or 'guild' not in data['guild']:
                await interaction.followup.send(
                    f"❌ No se encontró la guild **{nombre}**.",
                    ephemeral=True
                )
                return
            
            guild_data = data['guild']['guild']
            
            embed = discord.Embed(
                title=f"🛡️ {guild_data['name']}",
                description=guild_data.get('description', 'Sin descripción')[:200],
                color=TIBIA_BLUE
            )
            
            embed.add_field(name="Mundo", value=f"🌍 {guild_data['world']}", inline=True)
            embed.add_field(name="Fundada", value=f"📅 {guild_data.get('founded', 'N/A')}", inline=True)
            
            if 'members' in data['guild']:
                total_members = len(data['guild']['members'])
                embed.add_field(name="Miembros", value=f"👥 {total_members}", inline=True)
            
            if 'guildhalls' in guild_data and guild_data['guildhalls']:
                hall = guild_data['guildhalls'][0]
                embed.add_field(
                    name="Guildhall",
                    value=f"🏰 {hall.get('name', 'N/A')}",
                    inline=False
                )
            
            embed.set_footer(text="Datos obtenidos de TibiaData API")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener guild: {e}")
            await interaction.followup.send(
                "❌ Error al obtener información de la guild.",
                ephemeral=True
            )
    
    # ===== MÓDULO 3: INFORMACIÓN DE MUNDOS =====
    
    @tibia_group.command(name="worlds", description="Ver lista de todos los mundos de Tibia")
    async def tibia_worlds(self, interaction: discord.Interaction):
        """Muestra la lista de todos los mundos de Tibia"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api("/worlds")
            
            if not data or 'worlds' not in data or 'regular_worlds' not in data['worlds']:
                await interaction.followup.send(
                    "❌ Error al obtener la lista de mundos.",
                    ephemeral=True
                )
                return
            
            worlds = data['worlds']['regular_worlds']
            
            embed = discord.Embed(
                title="🌍 Mundos de Tibia",
                description=f"Total: **{len(worlds)}** mundos disponibles",
                color=TIBIA_BLUE
            )
            
            # Agrupar por ubicación
            locations = {}
            for world in worlds:
                loc = world.get('location', 'Unknown')
                if loc not in locations:
                    locations[loc] = []
                locations[loc].append(world)
            
            for location, loc_worlds in locations.items():
                worlds_text = ", ".join([
                    f"{w['name']} ({w['players_online']} online)"
                    for w in sorted(loc_worlds, key=lambda x: x['name'])[:10]
                ])
                
                embed.add_field(
                    name=f"📍 {location}",
                    value=worlds_text if len(worlds_text) < 1024 else worlds_text[:1020] + "...",
                    inline=False
                )
            
            embed.set_footer(text="Usa /tibia world <nombre> para más información")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener mundos: {e}")
            await interaction.followup.send(
                "❌ Error al obtener la lista de mundos.",
                ephemeral=True
            )
    
    @tibia_group.command(name="world", description="Ver información detallada de un mundo")
    @app_commands.describe(nombre="Nombre del mundo")
    async def tibia_world(self, interaction: discord.Interaction, nombre: str):
        """Muestra información detallada de un mundo específico"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api(f"/world/{nombre}")
            
            if not data or 'world' not in data or 'world' not in data['world']:
                await interaction.followup.send(
                    f"❌ No se encontró el mundo **{nombre}**.",
                    ephemeral=True
                )
                return
            
            world_data = data['world']['world']
            
            embed = discord.Embed(
                title=f"🌍 {world_data['name']}",
                color=TIBIA_GREEN
            )
            
            embed.add_field(
                name="Jugadores Online",
                value=f"👥 **{world_data['players_online']}**",
                inline=True
            )
            embed.add_field(
                name="Record Online",
                value=f"🏆 {world_data.get('record_players', 'N/A')}\n{world_data.get('record_date', '')}",
                inline=True
            )
            embed.add_field(
                name="Ubicación",
                value=f"📍 {world_data.get('location', 'N/A')}",
                inline=True
            )
            
            embed.add_field(
                name="Tipo de Mundo",
                value=f"🌐 {world_data.get('world_type', 'N/A')}",
                inline=True
            )
            embed.add_field(
                name="Tipo de PvP",
                value=f"⚔️ {world_data.get('pvp_type', 'N/A')}",
                inline=True
            )
            embed.add_field(
                name="BattlEye",
                value=f"{'✅' if world_data.get('battleye_protected') else '❌'} {'Protegido' if world_data.get('battleye_protected') else 'No protegido'}",
                inline=True
            )
            
            if world_data.get('premium_only'):
                embed.add_field(
                    name="Premium",
                    value="⭐ Solo Premium",
                    inline=True
                )
            
            embed.set_footer(text="Datos obtenidos de TibiaData API")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener mundo: {e}")
            await interaction.followup.send(
                "❌ Error al obtener información del mundo.",
                ephemeral=True
            )
    
    @tibia_group.command(name="battleye", description="Ver lista de mundos con BattlEye")
    async def tibia_battleye(self, interaction: discord.Interaction):
        """Muestra la lista de mundos con protección BattlEye"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api("/worlds")
            
            if not data or 'worlds' not in data or 'regular_worlds' not in data['worlds']:
                await interaction.followup.send(
                    "❌ Error al obtener la lista de mundos.",
                    ephemeral=True
                )
                return
            
            all_worlds = data['worlds']['regular_worlds']
            battleye_worlds = [w for w in all_worlds if w.get('battleye_protected')]
            
            embed = discord.Embed(
                title="🛡️ Mundos con BattlEye",
                description=f"**{len(battleye_worlds)}** de {len(all_worlds)} mundos tienen protección BattlEye",
                color=TIBIA_GREEN
            )
            
            # Agrupar por tipo de PvP
            pvp_types = {}
            for world in battleye_worlds:
                pvp = world.get('pvp_type', 'Unknown')
                if pvp not in pvp_types:
                    pvp_types[pvp] = []
                pvp_types[pvp].append(world)
            
            for pvp_type, worlds in pvp_types.items():
                worlds_text = ", ".join([
                    f"{w['name']} ({w['players_online']} online)"
                    for w in sorted(worlds, key=lambda x: x['players_online'], reverse=True)
                ])
                
                embed.add_field(
                    name=f"⚔️ {pvp_type}",
                    value=worlds_text if len(worlds_text) < 1024 else worlds_text[:1020] + "...",
                    inline=False
                )
            
            embed.set_footer(text="BattlEye protege contra bots y cheats")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener mundos BattlEye: {e}")
            await interaction.followup.send(
                "❌ Error al obtener la lista de mundos.",
                ephemeral=True
            )
    
    # ===== MÓDULO 4: CRIATURA/BOSS BOOSTED =====
    
    @tibia_group.command(name="boosted", description="Ver criatura boosted del día")
    async def tibia_boosted(self, interaction: discord.Interaction):
        """Muestra la criatura boosted del día actual"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api("/boostablebosses")
            
            if not data or 'boostable_bosses' not in data:
                await interaction.followup.send(
                    "❌ Error al obtener información de boosted.",
                    ephemeral=True
                )
                return
            
            boosted_data = data['boostable_bosses']
            boosted = boosted_data.get('boosted', {})
            
            if not boosted:
                await interaction.followup.send(
                    "❌ No se pudo obtener la criatura boosted del día.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="⚡ Criatura Boosted del Día",
                description=f"**{boosted.get('name', 'Unknown')}**",
                color=0xFFD700  # Dorado
            )
            
            if 'image_url' in boosted:
                embed.set_thumbnail(url=boosted['image_url'])
            
            embed.add_field(
                name="Bonus",
                value="⚡ Loot: x2\n⚡ XP: x2",
                inline=False
            )
            
            embed.set_footer(text="La criatura boosted cambia cada día a las 10:00 CEST")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener boosted: {e}")
            await interaction.followup.send(
                "❌ Error al obtener la criatura boosted.",
                ephemeral=True
            )
    
    # ===== MÓDULO 5: CALCULADORAS =====
    
    @tibia_group.command(name="exp", description="Calcular XP necesaria entre niveles")
    @app_commands.describe(
        nivel_actual="Nivel actual del personaje",
        nivel_objetivo="Nivel objetivo a alcanzar"
    )
    async def tibia_exp(
        self, 
        interaction: discord.Interaction, 
        nivel_actual: int, 
        nivel_objetivo: int
    ):
        """Calcula la experiencia necesaria entre dos niveles"""
        if nivel_actual < 1 or nivel_objetivo < 1:
            await interaction.response.send_message(
                "❌ Los niveles deben ser mayores a 0.",
                ephemeral=True
            )
            return
        
        if nivel_objetivo <= nivel_actual:
            await interaction.response.send_message(
                "❌ El nivel objetivo debe ser mayor al nivel actual.",
                ephemeral=True
            )
            return
        
        exp_needed = self.calculate_exp_needed(nivel_actual, nivel_objetivo)
        
        embed = discord.Embed(
            title="🧮 Calculadora de Experiencia",
            color=TIBIA_BLUE
        )
        
        embed.add_field(
            name="Niveles",
            value=f"**{nivel_actual}** → **{nivel_objetivo}**",
            inline=False
        )
        embed.add_field(
            name="Experiencia Necesaria",
            value=f"⭐ **{self.format_number(exp_needed)}** exp",
            inline=False
        )
        
        # Estimaciones de tiempo
        exp_per_hour_good = 1000000  # 1kk/hora
        exp_per_hour_great = 2000000  # 2kk/hora
        
        hours_good = exp_needed / exp_per_hour_good
        hours_great = exp_needed / exp_per_hour_great
        
        embed.add_field(
            name="Estimación de Tiempo",
            value=f"⏱️ A 1kk/h: ~{hours_good:.1f} horas\n"
                  f"⏱️ A 2kk/h: ~{hours_great:.1f} horas",
            inline=False
        )
        
        embed.set_footer(text="Estimaciones basadas en rates de XP comunes")
        
        await interaction.response.send_message(embed=embed)
    
    @tibia_group.command(name="stamina", description="Calcular bonus de stamina")
    @app_commands.describe(horas="Horas de stamina actual (0-42)")
    async def tibia_stamina(self, interaction: discord.Interaction, horas: int):
        """Calcula el bonus de stamina actual"""
        if horas < 0 or horas > 42:
            await interaction.response.send_message(
                "❌ La stamina debe estar entre 0 y 42 horas.",
                ephemeral=True
            )
            return
        
        # Cálculo de bonus
        if horas > 40:
            bonus_text = "⚡ **x1.5 XP** (Happy Hour - Verde)"
            bonus_color = 0x00FF00
        elif horas >= 14:
            bonus_text = "✅ **x1.0 XP** (Normal - Verde)"
            bonus_color = TIBIA_GREEN
        else:
            bonus_text = f"⚠️ **x0.5 XP** (Reducido - Naranja)"
            bonus_color = 0xFF8C00
        
        embed = discord.Embed(
            title="⏰ Calculadora de Stamina",
            color=bonus_color
        )
        
        embed.add_field(
            name="Stamina Actual",
            value=f"🕐 **{horas}h** de 42h",
            inline=False
        )
        embed.add_field(
            name="Bonus de XP",
            value=bonus_text,
            inline=False
        )
        
        # Tiempo para recuperar stamina completa
        if horas < 42:
            hours_to_full = 42 - horas
            embed.add_field(
                name="Tiempo para Recuperar",
                value=f"⏱️ {hours_to_full} horas offline (3 minutos reales = 1 hora stamina)",
                inline=False
            )
        
        embed.set_footer(text="La stamina se regenera 1 hora cada 3 minutos estando offline")
        
        await interaction.response.send_message(embed=embed)
    
    # ===== MÓDULO 6: UBICACIÓN DE RASHID =====
    
    @tibia_group.command(name="rashid", description="Ver ubicación actual de Rashid")
    async def tibia_rashid(self, interaction: discord.Interaction):
        """Muestra la ubicación actual de Rashid"""
        location = self.get_rashid_location(0)
        tomorrow = self.get_rashid_location(1)
        
        embed = discord.Embed(
            title="🏪 Ubicación de Rashid",
            description=f"**Hoy está en {location['city']}**",
            color=0xFFD700  # Dorado
        )
        
        embed.add_field(
            name="Ubicación Exacta",
            value=f"📍 {location['location']}",
            inline=False
        )
        
        embed.add_field(
            name="Mañana",
            value=f"🗓️ {tomorrow['city']} - {tomorrow['location']}",
            inline=False
        )
        
        weekday_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        schedule_text = ""
        for i, day_name in enumerate(weekday_names):
            loc = RASHID_LOCATIONS[i]
            schedule_text += f"**{day_name}:** {loc['city']}\n"
        
        embed.add_field(
            name="Horario Semanal",
            value=schedule_text,
            inline=False
        )
        
        embed.set_footer(text="Rashid compra items raros y valiosos")
        
        await interaction.response.send_message(embed=embed)
    
    # ===== MÓDULO 7: NOTICIAS DE TIBIA =====
    
    @tibia_group.command(name="news", description="Ver últimas noticias de Tibia")
    async def tibia_news(self, interaction: discord.Interaction):
        """Muestra las últimas noticias oficiales de Tibia"""
        await interaction.response.defer()
        
        try:
            data = await self.fetch_tibia_api("/news/latest")
            
            if not data or 'news' not in data:
                await interaction.followup.send(
                    "❌ Error al obtener las noticias.",
                    ephemeral=True
                )
                return
            
            news_list = data['news']
            
            if not news_list:
                await interaction.followup.send(
                    "📰 No hay noticias disponibles en este momento.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📰 Últimas Noticias de Tibia",
                color=TIBIA_BLUE
            )
            
            for news in news_list[:5]:
                date = news.get('date', 'N/A')
                title = news.get('title', 'Sin título')
                category = news.get('category', 'General')
                
                embed.add_field(
                    name=f"📌 {title}",
                    value=f"**Categoría:** {category}\n**Fecha:** {date}",
                    inline=False
                )
            
            embed.set_footer(text="Visita Tibia.com para más detalles")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener noticias: {e}")
            await interaction.followup.send(
                "❌ Error al obtener las noticias.",
                ephemeral=True
            )
    
    # ===== MÓDULO 8: EVENTOS DEL JUEGO =====
    
    @tibia_group.command(name="events", description="Ver eventos activos en Tibia")
    async def tibia_events(self, interaction: discord.Interaction):
        """Muestra los eventos activos en Tibia"""
        embed = discord.Embed(
            title="🎉 Eventos de Tibia",
            description="Información sobre eventos especiales",
            color=0x9B59B6  # Morado
        )
        
        embed.add_field(
            name="ℹ️ Información",
            value="Consulta el sitio oficial de Tibia para ver los eventos activos actuales.",
            inline=False
        )
        
        # Eventos regulares
        embed.add_field(
            name="📅 Eventos Regulares",
            value="• **Rapid Respawn** - Fines de semana\n"
                  "• **Double XP/Skill** - Eventos especiales\n"
                  "• **Boss Rush** - Eventos temporales",
            inline=False
        )
        
        embed.set_footer(text="Los eventos se anuncian en Tibia.com")
        
        await interaction.response.send_message(embed=embed)
    
    @tibia_group.command(name="rapid", description="Información sobre Rapid Respawn")
    async def tibia_rapid(self, interaction: discord.Interaction):
        """Muestra información sobre el evento Rapid Respawn"""
        embed = discord.Embed(
            title="⚡ Rapid Respawn Weekend",
            description="Información sobre el evento de respawn rápido",
            color=0xFF6B6B
        )
        
        embed.add_field(
            name="¿Qué es?",
            value="Durante este evento, todas las criaturas reaparecen 2x más rápido de lo normal.",
            inline=False
        )
        
        embed.add_field(
            name="📅 Cuándo",
            value="Generalmente los fines de semana\nDesde Viernes a las 10:00 hasta Lunes a las 10:00 (server save)",
            inline=False
        )
        
        embed.add_field(
            name="💡 Ventajas",
            value="• Más criaturas para cazar\n"
                  "• Mayor XP por hora\n"
                  "• Más loot\n"
                  "• Ideal para completar bestiario",
            inline=False
        )
        
        embed.set_footer(text="Verifica el calendario oficial en Tibia.com")
        
        await interaction.response.send_message(embed=embed)
    
    @tibia_group.command(name="doublexp", description="Información sobre Double XP")
    async def tibia_doublexp(self, interaction: discord.Interaction):
        """Muestra información sobre eventos de Double XP"""
        embed = discord.Embed(
            title="⭐ Double XP/Skill Event",
            description="Información sobre eventos de experiencia doble",
            color=0xFFD700  # Dorado
        )
        
        embed.add_field(
            name="¿Qué es?",
            value="Durante estos eventos especiales, obtienes el doble de experiencia y/o skills.",
            inline=False
        )
        
        embed.add_field(
            name="📅 Cuándo",
            value="Eventos especiales anunciados por CipSoft\n"
                  "• Aniversario de Tibia\n"
                  "• Celebraciones especiales\n"
                  "• Eventos sorpresa",
            inline=False
        )
        
        embed.add_field(
            name="💡 Tipos de Bonus",
            value="• **Double XP** - 2x experiencia\n"
                  "• **Double Skill** - 2x velocidad de training\n"
                  "• **Ambos** - En eventos grandes",
            inline=False
        )
        
        embed.set_footer(text="Estate atento a los anuncios oficiales")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Función de setup para cargar el cog"""
    await bot.add_cog(TibiaCog(bot))
    logger.info("TibiaCog cargado correctamente")
