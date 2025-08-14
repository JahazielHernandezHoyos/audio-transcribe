# Audio Transcribe - MVP

Aplicación multiplataforma para capturar audio del sistema y transcribirlo en tiempo real usando Whisper.

## Arquitectura

- **Backend**: Python + FastAPI + UV para gestión de dependencias
- **Frontend**: Tauri (HTML/CSS/JS + Rust wrapper)
- **Transcripción**: Whisper modelo "tiny" local (~39MB)
- **Audio**: PyAudioWPatch (Windows) + sounddevice (Linux)

## Estado del Desarrollo

### ✅ Completado
- Instalación de UV
- Creación del proyecto con `uv init`
- Instalación de dependencias Python básicas: fastapi, uvicorn, websockets, sounddevice, numpy, transformers, torch
- Estructura de directorios: backend/, frontend/

### 🔄 En Progreso
- Historia 1: Configuración del entorno base
  - ✅ UV instalado y configurado
  - ✅ Dependencias Python agregadas
  - ✅ Rust instalado
  - ⏳ Instalación de Tauri CLI (pendiente herramientas de compilación)

### ⏸️ Pendiente
- Historia 2: Captura de audio Windows (PyAudioWPatch)
- Historia 3: Captura de audio Linux (sounddevice)
- Historia 4: Integración Whisper modelo tiny
- Historia 5: API FastAPI con WebSocket
- Historia 6: Frontend Tauri
- Historia 7: Empaquetado multiplataforma
- Historia 8: Testing end-to-end

## Comandos UV del Proyecto

```bash
# Activar entorno
uv sync

# Ejecutar aplicación
uv run python backend/main.py

# Agregar dependencias
uv add nombre-paquete

# Ver dependencias instaladas
uv list
```

## Dependencias Actuales

```toml
dependencies = [
    "certifi>=2025.8.3",
    "charset-normalizer>=3.4.3",
    "fastapi>=0.116.1",
    "numpy>=2.3.2",
    "sounddevice>=0.5.2",
    "torch>=2.8.0",
    "transformers>=4.55.2",
    "uvicorn>=0.35.0",
    "websockets>=15.0.1",
]
```

## 🚀 Cómo Usar la Aplicación

### Instalación Automática

#### Windows
```cmd
# Ejecutar el instalador automático
install_windows.bat
```

#### Linux/macOS
```bash
# Ejecutar el instalador automático
./install_unix.sh
```

### Inicio Rápido
```bash
# Ejecutar aplicación completa (todas las plataformas)
python start_app.py

# O manualmente:
# Terminal 1 - Backend
cd backend && uv run python main.py

# Terminal 2 - Frontend (opcional)
cd frontend && python -m http.server 3000
```

### Acceso
- **Aplicación Web**: http://localhost:3000
- **API Documentación**: http://localhost:8000/docs

### Compatibilidad por Plataforma

#### ✅ Windows
- **Audio**: PyAudioWPatch (WASAPI)
- **Instalación**: `install_windows.bat`
- **Requisitos**: Python 3.12+, UV
- **Notas**: Permite acceso al micrófono cuando se solicite

#### ✅ Linux  
- **Audio**: sounddevice (ALSA/PulseAudio)
- **Instalación**: `./install_unix.sh`
- **Setup audio**: `python backend/setup_system_audio.py`
- **Notas**: Configuración automática de audio del sistema

#### ✅ macOS
- **Audio**: sounddevice (CoreAudio)
- **Instalación**: `./install_unix.sh`
- **Notas**: Permite acceso al micrófono en Preferencias del Sistema

### Funcionalidades Implementadas ✅
- ✅ Captura de audio en tiempo real (Linux/micrófono)
- ✅ Transcripción local con Whisper modelo tiny
- ✅ **Detección de actividad de voz (VAD)** - evita transcripciones falsas
- ✅ API REST completa (FastAPI)
- ✅ WebSocket para tiempo real
- ✅ Interfaz web funcional
- ✅ Gestión de dependencias con UV
- ✅ Filtrado inteligente de silencio y ruido

### Pendiente ⏳
- Captura de audio del sistema (requiere PulseAudio)
- Soporte Windows (PyAudioWPatch)
- Empaquetado con Tauri
- Distribución como ejecutable