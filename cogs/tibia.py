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
CACHE_DURATION = 300  # 5 minutos en segundos
MAX_CACHE_ENTRIES = 100  # Límite de entradas en caché
TOP_PLAYERS_LIMIT = 20  # Límite de jugadores top a mostrar
MAX_DESCRIPTION_LENGTH = 200  # Longitud máxima para descripciones
MAX_ITEMS_LENGTH = 100  # Longitud máxima para lista de items

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


class TibiaCog(commands.Cog):
    """Sistema completo de integración con Tibia"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = None
        self.api_cache = {}  # Cache a nivel de instancia
        self.session_lock = asyncio.Lock()  # Lock para crear sesión de forma segura
    
    async def cog_load(self):
        """Inicializa la sesión de aiohttp al cargar el cog"""
        async with self.session_lock:
            if self.session is None:
                self.session = aiohttp.ClientSession()
                logger.info("Sesión HTTP inicializada para TibiaCog")
    
    async def cog_unload(self):
        """Cierra la sesión de aiohttp al descargar el cog"""
        if self.session:
            await self.session.close()
            logger.info("Sesión HTTP cerrada para TibiaCog")
    
    def _cleanup_cache(self):
        """Limpia entradas expiradas del caché"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.api_cache.items()
            if (now - timestamp).total_seconds() >= CACHE_DURATION
        ]
        for key in expired_keys:
            del self.api_cache[key]
        
        # Si el caché sigue siendo muy grande, eliminar las entradas más antiguas
        if len(self.api_cache) > MAX_CACHE_ENTRIES:
            sorted_cache = sorted(
                self.api_cache.items(),
                key=lambda x: x[1][1]
            )
            for key, _ in sorted_cache[:len(self.api_cache) - MAX_CACHE_ENTRIES]:
                del self.api_cache[key]
    
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
        
        # Limpiar caché periódicamente
        self._cleanup_cache()
        
        # Verificar caché
        cache_key = url
        if cache_key in self.api_cache:
            cached_data, timestamp = self.api_cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < CACHE_DURATION:
                logger.debug(f"Usando caché para {endpoint}")
                return cached_data
        
        try:
            # Asegurar que la sesión existe con lock
            if not self.session:
                async with self.session_lock:
                    if not self.session:
                        self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    # Guardar en caché
                    self.api_cache[cache_key] = (data, datetime.now())
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
                
                # Truncar items solo si es necesario
                items_text = loot['items']
                if len(items_text) > MAX_ITEMS_LENGTH:
                    items_text = items_text[:MAX_ITEMS_LENGTH] + "..."
                
                embed.add_field(
                    name=f"🗡️ {loot['boss_name']}",
                    value=f"**Items:** {items_text}\n**Valor:** {value_str}\n**Fecha:** {timestamp.strftime('%d/%m/%Y %H:%M')}",
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
                # Usar get_user primero (cache) antes de fetch_user
                user = self.bot.get_user(loot['user_id'])
                if not user:
                    try:
                        user = await self.bot.fetch_user(loot['user_id'])
                    except:
                        pass
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
                # Mostrar top jugadores por nivel
                top_players = sorted(online_players, key=lambda x: x['level'], reverse=True)[:TOP_PLAYERS_LIMIT]
                
                players_text = "\n".join([
                    f"**{p['name']}** - Lvl {p['level']} ({p['vocation']})"
                    for p in top_players
                ])
                
                embed.add_field(
                    name=f"Top {TOP_PLAYERS_LIMIT} por Nivel",
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
            
            # Truncar descripción si es necesario
            description = guild_data.get('description', 'Sin descripción')
            if len(description) > MAX_DESCRIPTION_LENGTH:
                description = description[:MAX_DESCRIPTION_LENGTH] + "..."
            
            embed = discord.Embed(
                title=f"🛡️ {guild_data['name']}",
                description=description,
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
    
    @tibia_group.command(name="skills", description="Calcular tiempo de training de skills")
    @app_commands.describe(
        skill_actual="Nivel de skill actual",
        skill_objetivo="Nivel de skill objetivo",
        vocacion="Vocación del personaje (knight, paladin, mage)"
    )
    async def tibia_skills(
        self, 
        interaction: discord.Interaction, 
        skill_actual: int, 
        skill_objetivo: int,
        vocacion: str = "knight"
    ):
        """Calcula el tiempo aproximado de training para skills"""
        # Validaciones
        if skill_actual < 10 or skill_objetivo < 10:
            await interaction.response.send_message(
                "❌ Los skills deben ser al menos 10.",
                ephemeral=True
            )
            return
        
        if skill_objetivo <= skill_actual:
            await interaction.response.send_message(
                "❌ El skill objetivo debe ser mayor al skill actual.",
                ephemeral=True
            )
            return
        
        if skill_objetivo > 150:
            await interaction.response.send_message(
                "❌ El skill objetivo no puede ser mayor a 150.",
                ephemeral=True
            )
            return
        
        # Normalizar vocación
        vocacion = vocacion.lower()
        vocations_valid = ["knight", "paladin", "mage", "druid", "sorcerer"]
        if vocacion not in vocations_valid:
            await interaction.response.send_message(
                f"❌ Vocación inválida. Usa: {', '.join(vocations_valid)}",
                ephemeral=True
            )
            return
        
        # Cálculo aproximado de tries necesarios
        # Fórmula simplificada: tries = (skill_objetivo^2 - skill_actual^2) * multiplicador
        tries_per_level = {
            "knight": 50,  # Melee skills
            "paladin": 30,  # Distance
            "mage": 70,    # Magic level (más difícil)
            "druid": 70,
            "sorcerer": 70
        }
        
        multiplier = tries_per_level.get(vocacion, 50)
        total_tries = 0
        
        for skill in range(skill_actual, skill_objetivo):
            total_tries += int((skill ** 2) * multiplier)
        
        # Estimaciones de tiempo (tries por hora en diferentes condiciones)
        tries_per_hour_offline = 7200  # Training offline (dummy)
        tries_per_hour_exercise = 36000  # Exercise weapons (rápido pero caro)
        tries_per_hour_online = 14400  # Training online (dummies mejorados)
        
        hours_offline = total_tries / tries_per_hour_offline
        hours_exercise = total_tries / tries_per_hour_exercise
        hours_online = total_tries / tries_per_hour_online
        
        # Convertir a días si es más de 24 horas
        def format_time(hours):
            if hours > 24:
                days = hours / 24
                return f"~{days:.1f} días"
            else:
                return f"~{hours:.1f} horas"
        
        embed = discord.Embed(
            title="🧮 Calculadora de Skills",
            color=TIBIA_BLUE
        )
        
        embed.add_field(
            name="Skills",
            value=f"**{skill_actual}** → **{skill_objetivo}**",
            inline=False
        )
        
        embed.add_field(
            name="Vocación",
            value=f"🎯 {vocacion.capitalize()}",
            inline=False
        )
        
        embed.add_field(
            name="Tries Necesarios",
            value=f"📊 {self.format_number(total_tries)} tries",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Tiempo Estimado",
            value=f"**Offline Training:** {format_time(hours_offline)}\n"
                  f"**Online Training:** {format_time(hours_online)}\n"
                  f"**Exercise Weapons:** {format_time(hours_exercise)}",
            inline=False
        )
        
        embed.add_field(
            name="💡 Recomendación",
            value="Combina diferentes métodos para optimizar tiempo y costo:\n"
                  "• Exercise weapons para avances rápidos\n"
                  "• Offline training constante\n"
                  "• Online training cuando tengas tiempo",
            inline=False
        )
        
        embed.set_footer(text="Estimaciones aproximadas • Los valores reales pueden variar")
        
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
    
    # ===== MÓDULO 7: HUNTING SPOTS =====
    
    @tibia_group.command(name="hunt", description="Sugerencias de hunting spots por nivel")
    @app_commands.describe(
        nivel="Nivel del personaje",
        vocacion="Vocación del personaje (opcional)"
    )
    async def tibia_hunt(
        self, 
        interaction: discord.Interaction, 
        nivel: int,
        vocacion: str = None
    ):
        """Sugiere lugares de caza según el nivel del personaje"""
        # Validación
        if nivel < 1 or nivel > 1500:
            await interaction.response.send_message(
                "❌ El nivel debe estar entre 1 y 1500.",
                ephemeral=True
            )
            return
        
        # Normalizar vocación si se proporciona
        if vocacion:
            vocacion = vocacion.lower()
            valid_vocations = ["knight", "paladin", "sorcerer", "druid", "ek", "rp", "ms", "ed"]
            if vocacion not in valid_vocations:
                await interaction.response.send_message(
                    f"❌ Vocación inválida. Usa: knight, paladin, sorcerer, druid",
                    ephemeral=True
                )
                return
        
        # Base de datos de hunting spots por nivel
        hunting_spots = [
            {"min": 1, "max": 20, "name": "Rookgaard Rats & Trolls", "exp": "100-500/h", "profit": "Bajo"},
            {"min": 8, "max": 30, "name": "Edron Trolls & Goblins", "exp": "5k-15k/h", "profit": "Bajo"},
            {"min": 20, "max": 40, "name": "Mistrock Cyclops", "exp": "20k-40k/h", "profit": "Medio"},
            {"min": 30, "max": 60, "name": "Venore Amazons", "exp": "30k-60k/h", "profit": "Medio"},
            {"min": 40, "max": 80, "name": "Port Hope Tarantulas", "exp": "50k-100k/h", "profit": "Medio"},
            {"min": 50, "max": 100, "name": "Yalahar Mutated Humans", "exp": "100k-200k/h", "profit": "Alto"},
            {"min": 60, "max": 100, "name": "Edron Vampires", "exp": "100k-150k/h", "profit": "Bajo"},
            {"min": 80, "max": 130, "name": "Krailos Nightmares", "exp": "200k-400k/h", "profit": "Medio"},
            {"min": 100, "max": 150, "name": "Oramond Minos", "exp": "400k-600k/h", "profit": "Alto"},
            {"min": 120, "max": 180, "name": "Asura Palace", "exp": "600k-1kk/h", "profit": "Muy Alto"},
            {"min": 150, "max": 250, "name": "Carnivors Rock", "exp": "800k-1.5kk/h", "profit": "Alto"},
            {"min": 180, "max": 300, "name": "Roshamuul West", "exp": "1kk-2kk/h", "profit": "Medio"},
            {"min": 200, "max": 350, "name": "Summer Court", "exp": "1.5kk-3kk/h", "profit": "Alto"},
            {"min": 250, "max": 400, "name": "Winter Court", "exp": "2kk-4kk/h", "profit": "Alto"},
            {"min": 300, "max": 500, "name": "Flimsies (Issavi)", "exp": "3kk-5kk/h", "profit": "Muy Alto"},
            {"min": 350, "max": 600, "name": "Cobras (Nimmersatt)", "exp": "4kk-7kk/h", "profit": "Muy Alto"},
            {"min": 400, "max": 700, "name": "Falcon Bastion", "exp": "5kk-8kk/h", "profit": "Medio"},
            {"min": 500, "max": 1000, "name": "Soul War", "exp": "7kk-12kk/h", "profit": "Alto"},
            {"min": 600, "max": 1500, "name": "Library (Asuras/Grims)", "exp": "10kk-15kk/h", "profit": "Muy Alto"}
        ]
        
        # Filtrar spots apropiados para el nivel
        suitable_spots = [
            spot for spot in hunting_spots 
            if spot["min"] <= nivel <= spot["max"]
        ]
        
        # Si no hay spots exactos, buscar los más cercanos
        if not suitable_spots:
            # Buscar spots ligeramente por encima o por debajo
            for tolerance in [50, 100, 150, 200]:
                suitable_spots = [
                    spot for spot in hunting_spots 
                    if spot["min"] - tolerance <= nivel <= spot["max"] + tolerance
                ]
                if suitable_spots:
                    break
        
        if not suitable_spots:
            suitable_spots = hunting_spots[-3:]  # Mostrar los de nivel más alto
        
        # Limitar a 5 sugerencias
        suitable_spots = suitable_spots[:5]
        
        embed = discord.Embed(
            title="🗺️ Hunting Spots Recomendados",
            description=f"Sugerencias para nivel **{nivel}**" + (f" ({vocacion})" if vocacion else ""),
            color=TIBIA_GREEN
        )
        
        for i, spot in enumerate(suitable_spots, 1):
            profit_emoji = {
                "Bajo": "💰",
                "Medio": "💰💰",
                "Alto": "💰💰💰",
                "Muy Alto": "💰💰💰💰"
            }.get(spot["profit"], "💰")
            
            embed.add_field(
                name=f"{i}. {spot['name']}",
                value=f"**Nivel:** {spot['min']}-{spot['max']}\n"
                      f"**XP/h:** {spot['exp']}\n"
                      f"**Profit:** {profit_emoji} {spot['profit']}",
                inline=True
            )
        
        embed.add_field(
            name="💡 Consejos",
            value="• Usa la criatura boosted del día cuando sea posible\n"
                  "• Caza en party para mejor XP y profit\n"
                  "• Mantén stamina verde (40h+) para bonus\n"
                  "• Considera usar preys para mejor eficiencia",
            inline=False
        )
        
        embed.set_footer(text="Las tasas de XP y profit pueden variar según equipo y skills")
        
        await interaction.response.send_message(embed=embed)
    
    # ===== MÓDULO 8: NOTICIAS DE TIBIA =====
    
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
    
    # ===== MÓDULO 9: EVENTOS DEL JUEGO =====
    
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
