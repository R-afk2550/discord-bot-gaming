# 🎮 Bot de Discord para Servidor Gaming Multi-Juego

Bot profesional de Discord desarrollado en Python usando discord.py, diseñado específicamente para servidores gaming con soporte para múltiples juegos.

## 📋 Características Principales

- **Sistema de Roles por Juego**: Asignación automática de roles mediante panel interactivo
- **Búsqueda de Partidas (LFG)**: Sistema completo para encontrar compañeros de juego
- **Bienvenida Automática**: Mensajes personalizados para nuevos miembros
- **Moderación Completa**: Kick, ban, warn, mute, y gestión de mensajes
- **Sistema de Eventos**: Creación y recordatorios automáticos de eventos
- **Comandos de Utilidad**: Información del servidor, usuarios, y más

## 🎯 Juegos Soportados

- 🎮 **League of Legends** (LOL) - Con roles y rangos
- ⚔️ **World of Warcraft** (WoW) - Raids, Mythic+, PvP
- ⛏️ **Minecraft** - Survival, Creative, Modded
- 🗡️ **Tibia** - Hunt, Quest, Boss
- ⚡ **PokéXGames** - PvP, Hunt, Clan Wars

## 📁 Estructura del Proyecto

```
discord-bot-gaming/
├── bot.py                 # Archivo principal del bot
├── cogs/
│   ├── roles.py          # Sistema de roles
│   ├── lfg.py            # Búsqueda de partidas
│   ├── moderation.py     # Comandos de moderación
│   ├── welcome.py        # Sistema de bienvenida
│   ├── utility.py        # Comandos de utilidad
│   └── events.py         # Sistema de eventos
├── config/
│   └── settings.py       # Configuraciones del bot
├── database/
│   └── db_manager.py     # Gestión de SQLite
├── utils/
│   ├── embeds.py         # Templates de embeds
│   └── helpers.py        # Funciones auxiliares
├── .env.example          # Ejemplo de variables de entorno
├── requirements.txt      # Dependencias
├── setup.py             # Script de instalación
└── README.md            # Este archivo
```

## ⚙️ Requisitos Previos

- **Python 3.8 o superior**
- **Cuenta de Discord Developer** (para obtener el token del bot)
- **Pip** (gestor de paquetes de Python)

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/R-afk2550/discord-bot-gaming.git
cd discord-bot-gaming
```

### 2. Ejecutar Script de Instalación

**Opción Automática:**
```bash
python setup.py
```

**Opción Manual:**
```bash
# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de ejemplo
cp .env.example .env
```

### 3. Crear Aplicación en Discord Developer Portal

1. Ve a [Discord Developer Portal](https://discord.com/developers/applications)
2. Haz clic en "New Application"
3. Dale un nombre a tu aplicación
4. Ve a la sección **"Bot"** en el menú lateral
5. Haz clic en **"Add Bot"**
6. En la sección "Token", haz clic en **"Reset Token"**
7. **Copia el token** (lo necesitarás en el siguiente paso)

⚠️ **IMPORTANTE**: Nunca compartas tu token. Mantenlo seguro.

### 4. Configurar Variables de Entorno

Edita el archivo `.env` y añade tu token:

```env
DISCORD_TOKEN=tu_token_aqui
GUILD_ID=                    # Opcional: ID de tu servidor
WELCOME_CHANNEL_ID=          # Opcional: ID del canal de bienvenida
LOG_CHANNEL_ID=              # Opcional: ID del canal de logs
PREFIX=/                      # Opcional: Default /

# Configuración de GitHub (Opcional, para comandos de estado)
GITHUB_TOKEN=                # Opcional: Token de GitHub para comandos /github_*
GITHUB_REPO_OWNER=R-afk2550  # Opcional: Owner del repositorio
GITHUB_REPO_NAME=discord-bot-gaming  # Opcional: Nombre del repositorio
```

**¿Cómo obtener IDs?**
1. Activa el "Modo Desarrollador" en Discord (Configuración > Avanzado > Modo Desarrollador)
2. Haz clic derecho en servidor/canal > "Copiar ID"

**¿Cómo obtener un token de GitHub? (Opcional)**
1. Ve a [GitHub Settings](https://github.com/settings/tokens)
2. Clic en "Generate new token" > "Generate new token (classic)"
3. Dale un nombre descriptivo (ej: "Discord Bot")
4. Selecciona el scope `repo` (o solo `public_repo` si el repositorio es público)
5. Genera y copia el token en `GITHUB_TOKEN`

### 5. Configurar Permisos e Invitar el Bot

En el [Developer Portal](https://discord.com/developers/applications):

1. Ve a **OAuth2** > **URL Generator**
2. Selecciona los **scopes**:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Selecciona los **permisos**:
   - ✅ Manage Roles
   - ✅ Kick Members
   - ✅ Ban Members
   - ✅ Moderate Members
   - ✅ Manage Messages
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Read Message History
   - ✅ Add Reactions
   - ✅ Use Slash Commands
4. Copia la **URL generada** en la parte inferior
5. Pega la URL en tu navegador y selecciona tu servidor

### 6. Ejecutar el Bot

```bash
python bot.py
```

Si todo está configurado correctamente, verás:
```
Bot conectado como TuBot#1234 (ID: 123456789)
Discord.py versión: 2.3.2
Servidores: 1
Bot listo para usar!
```

## 🎮 Configuración Inicial en Discord

### Canales Recomendados

Crea estos canales en tu servidor para mejor experiencia:

- 📝 `#bienvenida` - Para mensajes de bienvenida
- 📋 `#roles` - Para que los usuarios elijan sus roles
- 🔍 `#buscar-grupo` - Para comandos LFG
- 📅 `#eventos` - Para anuncios de eventos
- 🛡️ `#logs` - Para logs de moderación (solo staff)

### Primer Uso

1. Usa `/crear_roles` en Discord (requiere permisos de administrador)
2. Esto creará todos los roles de juegos automáticamente
3. Los usuarios pueden usar `/roles` para auto-asignarse roles

## 📖 Lista Completa de Comandos

### 🎮 Roles de Juegos

| Comando | Descripción | Permisos |
|---------|-------------|----------|
| `/roles` | Panel interactivo para seleccionar juegos | Todos |
| `/crear_roles` | Crear todos los roles de juegos | Administrador |

### 🔍 Búsqueda de Grupo (LFG)

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/lfg <juego> [descripción]` | Buscar compañeros para cualquier juego | `/lfg LOL Rankeadas en la noche` |
| `/lfg_lol <rol> [rango]` | Buscar grupo para LoL | `/lfg_lol Mid Diamond` |
| `/lfg_wow <tipo> <rol>` | Buscar grupo para WoW | `/lfg_wow Mythic+ DPS` |

### 🛡️ Moderación

| Comando | Descripción | Permisos |
|---------|-------------|----------|
| `/kick <usuario> [razón]` | Expulsar usuario | Kick Members |
| `/ban <usuario> [razón]` | Banear usuario | Ban Members |
| `/warn <usuario> <razón>` | Advertir usuario | Moderate Members |
| `/warnings <usuario>` | Ver advertencias de usuario | Moderate Members |
| `/clear <cantidad>` | Borrar mensajes (1-100) | Manage Messages |
| `/mute <usuario> [tiempo]` | Silenciar usuario temporalmente | Moderate Members |

### 📅 Eventos

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/evento <título> <fecha> <descripción>` | Crear evento | `/evento Torneo 25/12/2024 20:00 Torneo de LoL` |
| `/eventos` | Ver próximos eventos | `/eventos` |

### 🔧 Utilidad

| Comando | Descripción |
|---------|-------------|
| `/ping` | Ver latencia del bot |
| `/serverinfo` | Información del servidor |
| `/userinfo [@usuario]` | Información de usuario |
| `/perfil` | Ver tu perfil de gaming |
| `/ayuda` | Lista de todos los comandos |

### 📊 Estado de GitHub

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/github_prs [limit]` | Ver pull requests abiertos en el repositorio | `/github_prs 5` |
| `/github_deployments [limit]` | Ver deployments/workflows recientes | `/github_deployments 5` |

## 🔐 Permisos Necesarios del Bot

El bot necesita los siguientes permisos para funcionar correctamente:

- **Manage Roles**: Para crear y asignar roles de juegos
- **Kick Members**: Para el comando /kick
- **Ban Members**: Para el comando /ban
- **Moderate Members**: Para el comando /mute
- **Manage Messages**: Para el comando /clear
- **Send Messages**: Para enviar mensajes en canales
- **Embed Links**: Para enviar embeds visuales
- **Read Message History**: Para comandos de moderación
- **Add Reactions**: Para futuros features con reacciones

## 🐛 Troubleshooting (Solución de Problemas)

### El bot no se conecta

```
❌ Error: Token de Discord inválido
```
**Solución**: Verifica que hayas copiado correctamente el token en `.env`

### Los comandos no aparecen

**Solución**: 
1. Asegúrate de haber invitado el bot con el scope `applications.commands`
2. Espera unos minutos (Discord puede tardar en sincronizar)
3. Reinicia Discord (Ctrl+R)

### El bot no puede crear roles

```
Error: No tengo permisos para crear roles
```
**Solución**: 
1. Ve a Configuración del Servidor > Roles
2. Arrastra el rol del bot por encima de otros roles
3. Verifica que tenga el permiso "Manage Roles"

### Los mensajes de bienvenida no se envían

**Solución**:
1. Verifica que el bot tenga permisos para escribir en el canal
2. Configura `WELCOME_CHANNEL_ID` en `.env`
3. O crea un canal llamado `#bienvenida`

### Error al instalar dependencias

```
ERROR: Could not install packages
```
**Solución**:
```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias una por una
pip install discord.py
pip install python-dotenv
pip install aiosqlite
pip install pytz
```

## 🎨 Personalización

### Añadir Más Juegos

Edita `config/settings.py`:

```python
GAMES = {
    'TuJuego': {
        'name': 'Nombre Completo',
        'emoji': '🎮',
        'roles': ['Rol1', 'Rol2'],  # Opcional
        'types': ['Tipo1', 'Tipo2']  # Opcional
    }
}
```

### Cambiar Colores de Embeds

Edita `config/settings.py`:

```python
COLORS = {
    'info': 0x3498db,      # Azul
    'success': 0x2ecc71,   # Verde
    'error': 0xe74c3c,     # Rojo
    'warning': 0xe67e22,   # Naranja
    'event': 0x9b59b6      # Morado
}
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Si quieres mejorar el bot:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías para Contribuir

- Escribe código limpio y comentado en español
- Sigue la estructura de carpetas existente
- Usa los embeds de `utils/embeds.py` para consistencia visual
- Añade logging apropiado
- Actualiza la documentación si es necesario

## 📝 Base de Datos

El bot usa SQLite para almacenar:

- **warnings**: Advertencias de usuarios
- **user_profiles**: Perfiles de gaming (juegos favoritos)
- **events**: Eventos programados

La base de datos se crea automáticamente en `gaming_bot.db`

## 🔒 Seguridad

- ✅ Nunca incluyas tu token en el código
- ✅ Usa `.env` para secretos
- ✅ `.gitignore` está configurado para evitar subir `.env`
- ✅ Validación de permisos antes de ejecutar comandos
- ✅ Manejo de errores robusto

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 👨‍💻 Autor

**R-afk2550**

## 🙏 Agradecimientos

- [discord.py](https://github.com/Rapptz/discord.py) - Librería principal
- Comunidad de Discord por el soporte
- Todos los contribuidores del proyecto

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisa la sección de [Troubleshooting](#-troubleshooting-solución-de-problemas)
2. Abre un [Issue](https://github.com/R-afk2550/discord-bot-gaming/issues)
3. Únete a nuestro servidor de Discord (próximamente)

---

⭐ Si te gusta el proyecto, ¡dale una estrella en GitHub!

🎮 ¡Disfruta tu servidor gaming!
