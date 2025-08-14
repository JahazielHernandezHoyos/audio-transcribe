#!/usr/bin/env python3
"""
Script para iniciar la aplicación completa de Audio Transcribe.
Inicia el backend API y sirve la interfaz frontend.
"""

import subprocess
import sys
import time
import webbrowser
import threading
import http.server
import socketserver
import os
import platform
from pathlib import Path


def _resolve_base_dir() -> Path:
    """Return base directory for resources, supporting PyInstaller frozen mode."""
    if getattr(sys, "frozen", False):  # PyInstaller onefile/onedir
        base = getattr(sys, "_MEIPASS", None)
        if base:
            return Path(base)
    return Path(__file__).parent

def start_backend():
    """Iniciar el servidor backend FastAPI."""
    print("🚀 Iniciando backend API...")
    base_dir = _resolve_base_dir()
    backend_dir = base_dir / "backend"
    
    try:
        # Cambiar al directorio backend
        original_dir = Path.cwd()
        os.chdir(backend_dir)
        
        # Configurar entorno multiplataforma
        env = os.environ.copy()
        # Force CPU to avoid CUDA initialization crashes (can be overridden)
        env.setdefault("CUDA_VISIBLE_DEVICES", "")
        env.setdefault("FORCE_DEVICE", "cpu")
        env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        
        # Si estamos empaquetados, arrancar uvicorn en el mismo proceso
        if getattr(sys, "frozen", False):
            # Importar el backend añadiendo su carpeta al sys.path
            sys.path.insert(0, str(backend_dir))
            try:
                import main as backend_main  # type: ignore
            except Exception as e:
                print(f"❌ No se pudo importar backend/main.py: {e}")
                return
            try:
                backend_main.run_server(reload=False)
            except Exception as e:
                print(f"❌ Error ejecutando servidor: {e}")
            return

        # Modo desarrollo (no congelado): usar uv si está disponible, si no, python directo
        try:
            if platform.system() == "Windows":
                cmd = ["uv.exe", "run", "python", "main.py"]
                subprocess.run(cmd, cwd=backend_dir, env=env, check=False)
            else:
                subprocess.run(["uv", "run", "python", "main.py"], cwd=backend_dir, env=env, check=False)
        except FileNotFoundError:
            # Fallback sin uv
            subprocess.run([sys.executable, "main.py"], cwd=backend_dir, env=env, check=False)
        
    except KeyboardInterrupt:
        print("\n⏹️ Backend detenido por usuario")
    except Exception as e:
        print(f"❌ Error iniciando backend: {e}")
        print("💡 Asegúrate de que UV está instalado y en el PATH")
        if platform.system() == "Windows":
            print("💡 En Windows, instala UV desde: https://docs.astral.sh/uv/getting-started/installation/")
    finally:
        # Restaurar directorio original
        try:
            os.chdir(original_dir)
        except Exception:
            pass

def start_frontend_server():
    """Iniciar servidor para la interfaz frontend."""
    print("🌐 Iniciando servidor frontend...")
    base_dir = _resolve_base_dir()
    frontend_dir = base_dir / "frontend"
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(frontend_dir), **kwargs)
        
        def log_message(self, format, *args):
            # Silenciar logs del servidor HTTP
            pass
    
    try:
        with socketserver.TCPServer(("", 3000), Handler) as httpd:
            print("📱 Frontend disponible en: http://localhost:3000")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n⏹️ Frontend detenido por usuario")
    except Exception as e:
        print(f"❌ Error iniciando frontend: {e}")

def main():
    """Función principal."""
    current_platform = platform.system()
    print("🎵 Audio Transcribe - Iniciando aplicación completa...")
    print("=" * 60)
    print(f"🖥️ Plataforma detectada: {current_platform}")
    
    # Verificar que estamos en el directorio correcto
    base_dir = _resolve_base_dir()
    if not (base_dir / "backend" / "main.py").exists():
        print("❌ Error: No se encuentra el archivo backend/main.py")
        print("   Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
        sys.exit(1)
    
    print("📋 Componentes a iniciar:")
    print("   • Backend API (FastAPI) en puerto 8000")
    print("   • Frontend Web en puerto 3000")
    print("   • Transcripción en tiempo real con Whisper")
    
    # Información específica de plataforma
    if current_platform == "Windows":
        print("   • Captura de audio: PyAudioWPatch (WASAPI)")
        print("   • Asegúrate de que PyAudioWPatch esté instalado")
    elif current_platform == "Linux":
        print("   • Captura de audio: sounddevice (ALSA/PulseAudio)")
    elif current_platform == "Darwin":  # macOS
        print("   • Captura de audio: sounddevice (CoreAudio)")
    
    print()
    
    try:
        # Iniciar frontend en un hilo separado
        frontend_thread = threading.Thread(target=start_frontend_server, daemon=True)
        frontend_thread.start()
        
        # Esperar un poco para que inicie el frontend
        time.sleep(2)
        
        print("✅ Servidores iniciados exitosamente!")
        print()
        print("🌍 Accede a la aplicación en: http://localhost:3000")
        print("🔧 API documentación en: http://localhost:8000/docs")
        print()
        print("💡 Instrucciones:")
        print("   1. Abre http://localhost:3000 en tu navegador")
        print("   2. Presiona 'Iniciar Captura' para comenzar")
        print("   3. Habla o reproduce audio para ver la transcripción")
        if current_platform == "Windows":
            print("   4. En Windows, permite el acceso al micrófono si se solicita")
            print("   5. Presiona Ctrl+C para detener")
        else:
            print("   4. Presiona Ctrl+C para detener")
        print()
        
        # Intentar abrir automáticamente en el navegador
        try:
            webbrowser.open('http://localhost:3000')
        except Exception:
            pass
        
        # Iniciar backend (esto bloquea)
        start_backend()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Aplicación detenida por usuario")
        print("👋 ¡Hasta luego!")
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print(f"💡 Plataforma: {current_platform}")
        sys.exit(1)

if __name__ == "__main__":
    main()