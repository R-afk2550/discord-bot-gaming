#!/usr/bin/env python3
"""
Script de instalación inicial para el bot de Discord Gaming
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verifica que la versión de Python sea 3.8 o superior"""
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Tu versión: Python {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")


def install_dependencies():
    """Instala las dependencias del requirements.txt"""
    print("\n📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error al instalar dependencias")
        return False


def create_env_file():
    """Crea el archivo .env si no existe"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("\n⚠️  El archivo .env ya existe")
        response = input("¿Deseas sobrescribirlo? (s/N): ").lower()
        if response != 's':
            print("   Manteniendo el archivo .env existente")
            return
    
    if env_example.exists():
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n✅ Archivo .env creado desde .env.example")
        print("   ⚠️  IMPORTANTE: Edita el archivo .env y añade tu DISCORD_TOKEN")
    else:
        print("\n❌ No se encontró .env.example")


def print_next_steps():
    """Imprime los siguientes pasos para el usuario"""
    print("\n" + "="*60)
    print("🎮 INSTALACIÓN COMPLETADA")
    print("="*60)
    print("\n📋 Próximos pasos:")
    print("\n1. Obtén tu token de Discord:")
    print("   • Ve a https://discord.com/developers/applications")
    print("   • Crea una nueva aplicación")
    print("   • Ve a la sección 'Bot'")
    print("   • Haz clic en 'Reset Token' y copia el token")
    print("\n2. Configura el archivo .env:")
    print("   • Abre el archivo .env con un editor de texto")
    print("   • Pega tu token en DISCORD_TOKEN=tu_token_aqui")
    print("   • (Opcional) Configura otros valores")
    print("\n3. Invita el bot a tu servidor:")
    print("   • En el Developer Portal, ve a 'OAuth2' > 'URL Generator'")
    print("   • Selecciona los scopes: 'bot' y 'applications.commands'")
    print("   • Permisos recomendados:")
    print("     - Manage Roles")
    print("     - Kick Members")
    print("     - Ban Members")
    print("     - Manage Messages")
    print("     - Send Messages")
    print("     - Embed Links")
    print("     - Read Message History")
    print("     - Moderate Members")
    print("   • Copia la URL generada y ábrela en tu navegador")
    print("\n4. Ejecuta el bot:")
    print("   python bot.py")
    print("\n5. ¡Disfruta!")
    print("   Usa /ayuda en Discord para ver todos los comandos")
    print("\n" + "="*60)


def main():
    """Función principal del script de instalación"""
    print("="*60)
    print("🎮 INSTALACIÓN DEL BOT DE DISCORD GAMING")
    print("="*60)
    
    # Verificar versión de Python
    check_python_version()
    
    # Instalar dependencias
    if not install_dependencies():
        print("\n❌ La instalación falló")
        sys.exit(1)
    
    # Crear archivo .env
    create_env_file()
    
    # Imprimir próximos pasos
    print_next_steps()


if __name__ == "__main__":
    main()
