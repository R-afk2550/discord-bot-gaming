#!/usr/bin/env python3
"""
Script de verificación para el bot de Discord Gaming
Ejecuta este script para verificar que todo está configurado correctamente
"""
import sys
import os

def check_python_version():
    """Verifica la versión de Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requerido")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    required = ['discord', 'dotenv', 'aiosqlite', 'pytz']
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (faltante)")
            missing.append(module)
    
    return len(missing) == 0

def check_env_file():
    """Verifica que el archivo .env exista"""
    if not os.path.isfile('.env'):
        print("❌ Archivo .env no encontrado")
        print("   Ejecuta: cp .env.example .env")
        return False
    print("✅ Archivo .env encontrado")
    return True

def check_token():
    """Verifica que el token esté configurado"""
    if not os.path.isfile('.env'):
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
        if 'DISCORD_TOKEN=tu_token_aqui' in content or not any('DISCORD_TOKEN=' in line and line.split('=')[1].strip() for line in content.split('\n') if line.startswith('DISCORD_TOKEN=')):
            print("⚠️  Token de Discord no configurado")
            print("   Edita .env y añade tu token")
            return False
    print("✅ Token configurado")
    return True

def check_structure():
    """Verifica la estructura del proyecto"""
    required_dirs = ['cogs', 'config', 'database', 'utils']
    required_files = ['bot.py', 'requirements.txt', 'README.md']
    
    all_ok = True
    for d in required_dirs:
        if not os.path.isdir(d):
            print(f"❌ Directorio faltante: {d}/")
            all_ok = False
        else:
            print(f"✅ {d}/")
    
    for f in required_files:
        if not os.path.isfile(f):
            print(f"❌ Archivo faltante: {f}")
            all_ok = False
    
    return all_ok

def main():
    print("="*60)
    print("🎮 VERIFICACIÓN DEL BOT DE DISCORD GAMING")
    print("="*60)
    
    print("\n1️⃣ Verificando versión de Python...")
    py_ok = check_python_version()
    
    print("\n2️⃣ Verificando dependencias...")
    deps_ok = check_dependencies()
    
    print("\n3️⃣ Verificando estructura del proyecto...")
    struct_ok = check_structure()
    
    print("\n4️⃣ Verificando configuración...")
    env_ok = check_env_file()
    token_ok = check_token() if env_ok else False
    
    print("\n" + "="*60)
    
    if all([py_ok, deps_ok, struct_ok, env_ok, token_ok]):
        print("✅ TODO LISTO - Puedes ejecutar el bot con: python bot.py")
    elif all([py_ok, deps_ok, struct_ok, env_ok]):
        print("⚠️  CASI LISTO - Configura tu token en .env")
    else:
        print("❌ HAY PROBLEMAS - Revisa los errores arriba")
        if not deps_ok:
            print("\n💡 Instala dependencias: pip install -r requirements.txt")
        if not env_ok:
            print("\n💡 Crea archivo .env: cp .env.example .env")
    
    print("="*60)

if __name__ == "__main__":
    main()
