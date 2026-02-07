"""
Generador de imágenes para banners de bienvenida
"""
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import discord


async def create_welcome_banner(member: discord.Member, member_count: int) -> discord.File:
    """
    Crea un banner de bienvenida personalizado
    
    Args:
        member: Miembro que se unió
        member_count: Número total de miembros
    
    Returns:
        discord.File: Imagen del banner
    """
    # Dimensiones del banner
    WIDTH = 1024
    HEIGHT = 500
    
    # Colores (tema Zero Hour - Minimalista Elegante)
    BG_COLOR_START = (20, 20, 30)      # Negro azulado
    BG_COLOR_END = (40, 40, 50)        # Gris oscuro
    ACCENT_COLOR = (220, 38, 38)       # Rojo neón
    TEXT_COLOR = (255, 255, 255)       # Blanco
    SUBTEXT_COLOR = (180, 180, 190)    # Gris claro
    
    # Crear imagen base
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR_START)
    draw = ImageDraw.Draw(img)
    
    # Crear degradado de fondo
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_COLOR_START[0] + (BG_COLOR_END[0] - BG_COLOR_START[0]) * ratio)
        g = int(BG_COLOR_START[1] + (BG_COLOR_END[1] - BG_COLOR_START[1]) * ratio)
        b = int(BG_COLOR_START[2] + (BG_COLOR_END[2] - BG_COLOR_START[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # Descargar avatar del usuario
    avatar_size = 200
    async with aiohttp.ClientSession() as session:
        async with session.get(str(member.display_avatar.url)) as resp:
            if resp.status == 200:
                avatar_data = await resp.read()
                avatar = Image.open(io.BytesIO(avatar_data))
            else:
                # Avatar por defecto si falla
                avatar = Image.new('RGB', (avatar_size, avatar_size), (100, 100, 100))
    
    # Redimensionar avatar
    avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
    
    # Crear máscara circular para el avatar
    mask = Image.new('L', (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
    
    # Aplicar máscara al avatar
    circular_avatar = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
    circular_avatar.paste(avatar, (0, 0))
    circular_avatar.putalpha(mask)
    
    # Crear borde brillante alrededor del avatar
    border_size = 6
    border_avatar = Image.new('RGBA', (avatar_size + border_size * 2, avatar_size + border_size * 2), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_avatar)
    border_draw.ellipse((0, 0, avatar_size + border_size * 2, avatar_size + border_size * 2), fill=ACCENT_COLOR)
    
    # Posicionar avatar en el centro superior
    avatar_x = (WIDTH - avatar_size) // 2
    avatar_y = 60
    
    # Pegar borde y avatar
    img.paste(border_avatar, (avatar_x - border_size, avatar_y - border_size), border_avatar)
    img.paste(circular_avatar, (avatar_x, avatar_y), circular_avatar)
    
    # Línea decorativa roja debajo del avatar
    line_y = avatar_y + avatar_size + 30
    line_width = 300
    line_x = (WIDTH - line_width) // 2
    draw.rectangle([line_x, line_y, line_x + line_width, line_y + 3], fill=ACCENT_COLOR)
    
    # Intentar cargar fuentes, si no usa la por defecto
    try:
        # Fuente para el nombre de usuario (grande)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        # Fuente para texto secundario
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        # Fuente para contador de miembros
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Texto: Nombre de usuario
    username = f"{member.name}"
    text_bbox = draw.textbbox((0, 0), username, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (WIDTH - text_width) // 2
    text_y = line_y + 40
    
    # Sombra del texto (efecto profundidad)
    shadow_offset = 3
    draw.text((text_x + shadow_offset, text_y + shadow_offset), username, font=font_large, fill=(0, 0, 0, 128))
    draw.text((text_x, text_y), username, font=font_large, fill=TEXT_COLOR)
    
    # Texto: "SE UNIÓ A ZERO HOUR ⏰"
    welcome_text = "SE UNIÓ A ZERO HOUR ⏰"
    welcome_bbox = draw.textbbox((0, 0), welcome_text, font=font_medium)
    welcome_width = welcome_bbox[2] - welcome_bbox[0]
    welcome_x = (WIDTH - welcome_width) // 2
    welcome_y = text_y + 60
    draw.text((welcome_x, welcome_y), welcome_text, font=font_medium, fill=SUBTEXT_COLOR)
    
    # Texto: "MIEMBRO #XX"
    member_text = f"MIEMBRO #{member_count}"
    member_bbox = draw.textbbox((0, 0), member_text, font=font_small)
    member_width = member_bbox[2] - member_bbox[0]
    member_x = (WIDTH - member_width) // 2
    member_y = welcome_y + 50
    draw.text((member_x, member_y), member_text, font=font_small, fill=ACCENT_COLOR)
    
    # Guardar en buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return discord.File(fp=buffer, filename='welcome_banner.png')
