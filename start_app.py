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
import shutil
from pathlib import Path
from urllib.request import urlretrieve


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

        # Modo desarrollo (no congelado): garantizar uv y usarlo como runtime embebido
        uv_path = _ensure_uv()
        if uv_path:
            # Instalar deps si faltan y ejecutar en la raíz del proyecto (donde está pyproject.toml)
            try:
                print("📦 Sincronizando dependencias con uv...")
                subprocess.run([uv_path, "sync"], cwd=base_dir, env=env, check=True)
            except Exception as e:
                print(f"⚠️ uv sync falló: {e}")
            # Ejecutar backend usando el runtime gestionado por uv
            try:
                subprocess.run([uv_path, "run", "python", "-m", "backend.main"], cwd=base_dir, env=env, check=False)
            except Exception as e:
                print(f"❌ Error ejecutando backend con uv run: {e}")
                print("➡️ Intentando fallback a Python del sistema...")
                subprocess.run([sys.executable, "-m", "backend.main"], cwd=base_dir, env=env, check=False)
        else:
            print("⚠️ No se pudo asegurar uv. Usando Python del sistema como fallback.")
            subprocess.run([sys.executable, "-m", "backend.main"], cwd=base_dir, env=env, check=False)
        
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


def _ensure_uv() -> str | None:
    """Ensure 'uv' is available. If not, download a portable binary for the platform.

    Returns absolute path to uv executable or None.
    """
    # 1) PATH
    exe_name = "uv.exe" if platform.system() == "Windows" else "uv"
    path_uv = shutil.which("uv") or shutil.which(exe_name)
    if path_uv:
        return path_uv

    # 2) Try download latest release binary
    try:
        arch = platform.machine().lower()
        sysname = platform.system().lower()
        if sysname == "windows":
            tag = "x86_64-pc-windows-msvc" if "64" in arch or arch == "amd64" else "i686-pc-windows-msvc"
            filename = f"uv-{tag}.exe"
        elif sysname == "linux":
            tag = "x86_64-unknown-linux-gnu" if arch in {"x86_64", "amd64"} else "aarch64-unknown-linux-gnu"
            filename = f"uv-{tag}"
        elif sysname == "darwin":
            tag = "aarch64-apple-darwin" if arch in {"arm64", "aarch64"} else "x86_64-apple-darwin"
            filename = f"uv-{tag}"
        else:
            return None

        url = f"https://github.com/astral-sh/uv/releases/latest/download/{filename}"
        base_dir = _resolve_base_dir()
        runtime_dir = base_dir / "runtime"
        runtime_dir.mkdir(exist_ok=True)
        dest = runtime_dir / ("uv.exe" if filename.endswith(".exe") else "uv")
        print(f"⬇️ Descargando uv desde {url} ...")
        urlretrieve(url, dest)
        try:
            os.chmod(dest, 0o755)
        except Exception:
            pass
        return str(dest)
    except Exception as e:
        print(f"⚠️ No se pudo descargar uv: {e}")
        return None

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