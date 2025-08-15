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
    print("Starting backend API...")
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
                print(f"Error: Could not import backend/main.py: {e}")
                return
            try:
                backend_main.run_server(reload=False)
            except Exception as e:
                print(f"Error running server: {e}")
            return

        # Modo desarrollo (no congelado): garantizar uv y usarlo como runtime embebido
        uv_path = _ensure_uv()
        if uv_path:
            # Instalar deps si faltan y ejecutar en la raíz del proyecto (donde está pyproject.toml)
            try:
                print("Syncing dependencies with uv...")
                subprocess.run([uv_path, "sync"], cwd=base_dir, env=env, check=True)
            except Exception as e:
                print(f"Warning: uv sync failed: {e}")
            # Ejecutar backend usando el runtime gestionado por uv
            try:
                subprocess.run([uv_path, "run", "python", "-m", "backend.main"], cwd=base_dir, env=env, check=False)
            except Exception as e:
                print(f"Error running backend with uv run: {e}")
                print("➡️ Intentando fallback a Python del sistema...")
                subprocess.run([sys.executable, "-m", "backend.main"], cwd=base_dir, env=env, check=False)
        else:
            print("Warning: Could not ensure uv. Using system Python as fallback.")
            subprocess.run([sys.executable, "-m", "backend.main"], cwd=base_dir, env=env, check=False)
        
    except KeyboardInterrupt:
        print("\n⏹️ Backend detenido por usuario")
    except Exception as e:
        print(f"Error starting backend: {e}")
        print("Tip: Make sure UV is installed and in PATH")
        if platform.system() == "Windows":
            print("Tip: On Windows, install UV from: https://docs.astral.sh/uv/getting-started/installation/")
    finally:
        # Restaurar directorio original
        try:
            os.chdir(original_dir)
        except Exception:
            pass

def start_frontend_server():
    """Iniciar servidor para la interfaz frontend."""
    print("Starting frontend server...")
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
            print("Frontend available at: http://localhost:3000")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n⏹️ Frontend detenido por usuario")
    except Exception as e:
        print(f"Error starting frontend: {e}")


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
        print(f"Warning: Could not download uv: {e}")
        return None

def main():
    """Función principal."""
    current_platform = platform.system()
    tauri_mode = os.getenv("TAURI", "").strip()
    print("Audio Transcribe - Starting complete application...")
    print("=" * 60)
    print(f"Platform detected: {current_platform}")
    
    # Verificar que estamos en el directorio correcto
    base_dir = _resolve_base_dir()
    if not (base_dir / "backend" / "main.py").exists():
        print("Error: backend/main.py file not found")
        print("   Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
        sys.exit(1)
    
    print("Components to start:")
    print("   - Backend API (FastAPI) on port 8000")
    print("   - Frontend Web on port 3000")
    print("   - Real-time transcription with Whisper")
    
    # Información específica de plataforma
    if current_platform == "Windows":
        print("   - Audio capture: PyAudioWPatch (WASAPI)")
        print("   - Make sure PyAudioWPatch is installed")
    elif current_platform == "Linux":
        print("   - Audio capture: sounddevice (ALSA/PulseAudio)")
    elif current_platform == "Darwin":  # macOS
        print("   - Audio capture: sounddevice (CoreAudio)")
    
    print()
    
    try:
        if not tauri_mode:
            # Iniciar frontend en un hilo separado cuando NO es Tauri
            frontend_thread = threading.Thread(target=start_frontend_server, daemon=True)
            frontend_thread.start()
            # Esperar un poco para que inicie el frontend
            time.sleep(2)
            print("Servers started successfully!")
            print()
            print("Access the application at: http://localhost:3000")
        else:
            print("Tauri mode: starting backend only (no port 3000 server)")
            print()
        print("API documentation at: http://localhost:8000/docs")
        print()
        print("Instructions:")
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
        if not tauri_mode:
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
        print(f"\nUnexpected error: {e}")
        print(f"Platform: {current_platform}")
        sys.exit(1)

if __name__ == "__main__":
    main()