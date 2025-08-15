#!/usr/bin/env python3
"""
Script para crear instalador ejecutable de Windows
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Ejecuta un comando y maneja errores"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return None

def create_windows_installer():
    """Crea el instalador ejecutable para Windows"""
    print("📦 Creando instalador ejecutable para Windows...")
    
    # Verificar que UV está disponible
    if not shutil.which("uv"):
        print("❌ UV no encontrado. Instalando...")
        run_command("curl -LsSf https://astral.sh/uv/install.sh | sh", "Instalando UV")
    
    # Crear directorio de distribución
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Instalar PyInstaller si no está disponible
    run_command("uv add pyinstaller", "Instalando PyInstaller")
    
    # Crear archivo main ejecutable
    main_content = '''
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    print("🎵 Audio Transcribe - Iniciando aplicación...")
    print("=" * 50)
    
    # Obtener directorio base
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent
    
    print(f"📁 Directorio base: {base_dir}")
    
    # Cambiar al directorio de la aplicación
    os.chdir(base_dir)
    
    try:
        # Verificar si UV está disponible
        if not shutil.which("uv"):
            print("❌ UV no encontrado. Por favor instala UV primero:")
            print("   https://docs.astral.sh/uv/getting-started/installation/")
            input("Presiona Enter para salir...")
            return
        
        print("🔧 Sincronizando dependencias...")
        subprocess.run(["uv", "sync"], check=True)
        
        print("🚀 Iniciando Audio Transcribe...")
        print("📍 La aplicación se abrirá en tu navegador en unos segundos...")
        
        # Iniciar el servidor en segundo plano
        import threading
        
        def start_server():
            subprocess.run([sys.executable, "start_app.py"])
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Esperar un poco y abrir navegador
        time.sleep(3)
        webbrowser.open("http://localhost:3000")
        
        print("\\n🌐 Audio Transcribe está ejecutándose!")
        print("📱 Interfaz web: http://localhost:3000")
        print("📚 API docs: http://localhost:8000/docs")
        print("\\n⚠️ NO CIERRES esta ventana mientras uses la aplicación")
        print("\\n📝 Presiona Ctrl+C para detener la aplicación")
        
        # Mantener la aplicación viva
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\n🛑 Deteniendo Audio Transcribe...")
            print("👋 ¡Gracias por usar Audio Transcribe!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\\n💡 Soluciones posibles:")
        print("1. Verifica que tienes Python 3.8+ instalado")
        print("2. Instala UV: https://docs.astral.sh/uv/")
        print("3. Ejecuta como administrador si es necesario")
        input("\\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
'''
    
    # Escribir archivo main
    with open("audio_transcribe_main.py", "w", encoding="utf-8") as f:
        f.write(main_content)
    
    # Crear ejecutable con PyInstaller
    pyinstaller_cmd = [
        "uv", "run", "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=AudioTranscribe-Installer",
        "--icon=src-tauri/icons/icon.ico" if Path("src-tauri/icons/icon.ico").exists() else "",
        "--add-data=backend;backend",
        "--add-data=frontend;frontend", 
        "--add-data=pyproject.toml;.",
        "--add-data=README.md;.",
        "--add-data=unix_installer.sh;.",
        "audio_transcribe_main.py"
    ]
    
    # Remover el argumento icon si no existe
    if not Path("src-tauri/icons/icon.ico").exists():
        pyinstaller_cmd = [arg for arg in pyinstaller_cmd if not arg.startswith("--icon")]
    
    if run_command(" ".join(pyinstaller_cmd), "Creando ejecutable con PyInstaller"):
        exe_path = Path("dist/AudioTranscribe-Installer.exe")
        if exe_path.exists():
            print(f"✅ Instalador creado: {exe_path}")
            print(f"📏 Tamaño: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
            return exe_path
        else:
            print("❌ No se pudo encontrar el ejecutable generado")
    
    return None

def create_simple_installer():
    """Crea un instalador simple y directo"""
    print("📦 Creando instalador simple...")
    
    installer_content = '''
@echo off
title Audio Transcribe - Instalador para Windows
echo.
echo     ╔══════════════════════════════════════╗
echo     ║        Audio Transcribe v1.0         ║  
echo     ║     Instalador para Windows          ║
echo     ╚══════════════════════════════════════╝
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado
    echo.
    echo Por favor instala Python 3.8+ desde:
    echo https://python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

:: Crear directorio de instalación
set INSTALL_DIR=%USERPROFILE%\\AppData\\Local\\AudioTranscribe
echo 📁 Creando directorio: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

:: Descargar archivos
echo 📥 Descargando archivos de Audio Transcribe...
cd /d "%INSTALL_DIR%"

:: Descargar repositorio
echo Descargando desde GitHub...
curl -L "https://github.com/JahazielHernandezHoyos/audio-transcribe/archive/refs/heads/master.zip" -o audio-transcribe.zip

:: Extraer archivos
echo 📦 Extrayendo archivos...
powershell -command "Expand-Archive -Path 'audio-transcribe.zip' -DestinationPath '.' -Force"
move audio-transcribe-master\\* .
rmdir /s /q audio-transcribe-master
del audio-transcribe.zip

:: Instalar UV
echo 🔧 Instalando UV (gestor de paquetes)...
curl -LsSf https://astral.sh/uv/install.sh | sh

:: Instalar dependencias
echo 📦 Instalando dependencias...
"%USERPROFILE%\\.local\\bin\\uv.exe" sync

:: Crear acceso directo en el escritorio
echo 🔗 Creando acceso directo...
set SHORTCUT_PATH=%USERPROFILE%\\Desktop\\Audio Transcribe.lnk
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = '%INSTALL_DIR%\\start_app.py'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo.
echo ✅ ¡Instalación completada!
echo.
echo 🚀 Para ejecutar Audio Transcribe:
echo    1. Usa el acceso directo del escritorio
echo    2. O navega a: %INSTALL_DIR%
echo    3. Y ejecuta: python start_app.py
echo.
echo 🌐 La aplicación se abrirá en: http://localhost:3000
echo.
pause
'''
    
    # Crear instalador .bat
    installer_path = Path("dist/AudioTranscribe-Windows-Installer.bat")
    with open(installer_path, "w", encoding="utf-8") as f:
        f.write(installer_content)
    
    print(f"✅ Instalador .bat creado: {installer_path}")
    return installer_path

if __name__ == "__main__":
    print("Audio Transcribe - Constructor de Instalador Windows")
    print("=" * 55)
    
    # Crear directorio dist
    Path("dist").mkdir(exist_ok=True)
    
    # Intentar crear ejecutable con PyInstaller
    exe_path = create_windows_installer()
    
    # Crear instalador .bat como alternativa
    bat_path = create_simple_installer()
    
    print("\\n📋 Archivos creados:")
    if exe_path and exe_path.exists():
        print(f"   • {exe_path} (Ejecutable)")
    if bat_path and bat_path.exists():
        print(f"   • {bat_path} (Instalador batch)")
    
    print("\\n🚀 Listos para subir al release de GitHub!")