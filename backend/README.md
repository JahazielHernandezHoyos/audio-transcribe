# Backend - Python Audio Transcription API

## Propósito
API en Python usando FastAPI para capturar audio del sistema y transcribirlo usando Whisper.

## Componentes a Implementar

### 1. Captura de Audio
- **Linux**: sounddevice + PulseAudio/ALSA loopback
- **Windows**: PyAudioWPatch para WASAPI loopback
- **Buffer circular** para audio continuo
- **Detección automática** de plataforma

### 2. Transcripción
- **Whisper modelo "tiny"** (~39MB) para balance velocidad/precisión
- **Chunks de 3-5 segundos** para tiempo real
- **Soporte** español/inglés
- **Auto-detección** CPU/GPU

### 3. API FastAPI
- `GET /status` - Estado del sistema
- `POST /start_capture` - Iniciar captura
- `POST /stop_capture` - Detener captura
- `GET /get_transcription` - Obtener texto transcrito
- `WebSocket /ws` - Stream en tiempo real

### 4. Estructura de Archivos
```
backend/
├── main.py              # FastAPI app principal
├── audio_capture.py     # Captura de audio multiplataforma
├── transcription.py     # Integración con Whisper
├── api/
│   ├── __init__.py
│   ├── routes.py        # Rutas de la API
│   └── websocket.py     # WebSocket para tiempo real
└── config.py            # Configuración de la app
```

## Dependencias Requeridas
- fastapi>=0.116.1
- uvicorn>=0.35.0
- websockets>=15.0.1
- sounddevice>=0.5.2 (Linux)
- PyAudioWPatch (Windows) - agregar condicionalmente
- transformers>=4.55.2 (para Whisper)
- torch>=2.8.0
- numpy>=2.3.2

## Estado Actual
- ✅ Dependencias básicas instaladas con UV
- ⏳ Estructura de archivos pendiente
- ⏳ Implementación de captura de audio pendiente
- ⏳ Integración Whisper pendiente
- ⏳ API endpoints pendientes

## Comandos de Desarrollo
```bash
# Desde raíz del proyecto
uv run python backend/main.py

# Para testing de componentes específicos
uv run python backend/audio_capture.py
uv run python backend/transcription.py
```