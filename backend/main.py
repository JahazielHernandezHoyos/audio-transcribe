"""
API principal de Audio Transcribe usando FastAPI.
Proporciona endpoints REST y WebSocket para controlar transcripción en tiempo real.
"""

import asyncio
import json
import logging
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Optional
import threading
import queue
import numpy as np

from audio_capture import AudioCapture, AudioCaptureError
from transcription import RealTimeTranscriber

# Configurar logging
import os
log_level = logging.DEBUG if os.getenv("DEBUG") else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Estado global de la aplicación
app_state = {
    "is_capturing": False,
    "audio_capture": None,
    "transcriber": None,
    "transcription_queue": queue.Queue(),
    "connected_clients": set(),
    "selected_device_index": None,  # Índice de dispositivo de entrada seleccionado
    "selected_output_index": None,  # Índice de dispositivo de salida seleccionado (Windows)
}

async def transcription_broadcaster():
    """Task para enviar transcripciones via WebSocket."""
    logger.info("🔄 Iniciando broadcaster de transcripciones")
    while True:
        try:
            # Verificar si hay transcripciones pendientes
            if not app_state["transcription_queue"].empty():
                transcription = app_state["transcription_queue"].get_nowait()
                logger.info(f"📡 Broadcasting transcripción: {transcription.get('text', '')[:50]}...")
                
                # Convert numpy types to native Python types for JSON serialization
                serializable_transcription = {}
                for key, value in transcription.items():
                    if hasattr(value, 'item'):  # numpy scalar
                        serializable_transcription[key] = value.item()
                    else:
                        serializable_transcription[key] = value
                
                message = {
                    "type": "transcription",
                    "data": serializable_transcription,
                    "timestamp": float(transcription.get("processing_time", 0))
                }
                
                await broadcast_to_clients(message)
            
            await asyncio.sleep(0.1)  # Verificar cada 100ms
            
        except Exception as e:
            logger.error(f"Error en broadcaster: {e}")
            await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación."""
    logger.info("🚀 Iniciando Audio Transcribe API...")
    
    # Inicializar transcriptor
    try:
        app_state["transcriber"] = RealTimeTranscriber(
            chunk_duration=3.0,
            overlap_duration=0.5
        )
        logger.info("✅ Transcriptor inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando transcriptor: {e}")
    
    # Iniciar broadcaster
    broadcaster_task = asyncio.create_task(transcription_broadcaster())
    logger.info("📡 Broadcaster iniciado")
    
    yield
    
    # Limpieza al cerrar
    logger.info("🛑 Cerrando Audio Transcribe API...")
    broadcaster_task.cancel()
    if app_state["is_capturing"]:
        stop_audio_capture()

# Crear aplicación FastAPI
app = FastAPI(
    title="Audio Transcribe API",
    description="API para captura y transcripción de audio en tiempo real",
    version="0.1.0",
    lifespan=lifespan
)

# Configurar CORS para permitir conexiones desde Tauri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def audio_callback(audio_data: np.ndarray):
    """
    Callback para procesar audio capturado en tiempo real.
    
    Args:
        audio_data: Chunk de audio capturado
    """
    if app_state["transcriber"]:
        # Calcular volumen del chunk para debug
        rms_volume = np.sqrt(np.mean(audio_data**2))
        
        # Solo procesar si hay suficiente audio
        if rms_volume > 0.001:  # Umbral más bajo para testing
            result = app_state["transcriber"].add_audio(audio_data)
            
            if result:
                # Verificar si se saltó por bajo volumen
                if result.get("skipped"):
                    logger.debug(f"🔇 Audio saltado: {result.get('skipped')} (vol: {result.get('volume', 0):.4f})")
                elif result.get("text", "").strip():
                    # Solo mostrar transcripciones reales
                    confidence = result.get("confidence", 0)
                    processing_time = result.get("processing_time", 0)
                    logger.info(f"📝 Transcripción: \"{result['text']}\" (conf: {confidence:.2f}, tiempo: {processing_time:.2f}s)")
                    
                    # Agregar a cola para WebSocket
                    app_state["transcription_queue"].put(result)
        else:
            logger.debug(f"🔇 Chunk muy silencioso (vol: {rms_volume:.4f}), ignorando")

def _list_audio_devices() -> Dict[str, any]:
    """Listar dispositivos de audio disponibles por plataforma."""
    import platform as _platform
    devices = []
    input_devices = []
    output_devices = []
    loopback_devices = []

    try:
        if _platform.system().lower() == "windows":
            try:
                import pyaudiowpatch as pyaudio
                pa = pyaudio.PyAudio()
                for i in range(pa.get_device_count()):
                    info = pa.get_device_info_by_index(i)
                    device = {
                        "index": i,
                        "name": info.get("name"),
                        "max_input_channels": info.get("maxInputChannels"),
                        "default_sample_rate": info.get("defaultSampleRate"),
                        "host_api": info.get("hostApi"),
                        "is_loopback": "loopback" in str(info.get("name", "")).lower(),
                        "is_input": (info.get("maxInputChannels", 0) or 0) > 0,
                    }
                    devices.append(device)
                    if device["is_input"]:
                        input_devices.append(device)
                        if device["is_loopback"]:
                            loopback_devices.append(device)
                    else:
                        output_devices.append(device)
                pa.terminate()
            except Exception as e:
                logger.error(f"Error listando dispositivos Windows: {e}")
        else:
            try:
                import sounddevice as sd
                sd_devs = sd.query_devices()
                for i, info in enumerate(sd_devs):
                    device = {
                        "index": i,
                        "name": info.get("name"),
                        "max_input_channels": info.get("max_input_channels", info.get("max_input_channels", 0)),
                        "max_output_channels": info.get("max_output_channels", info.get("max_output_channels", 0)),
                        "default_samplerate": info.get("default_samplerate"),
                        "is_input": (info.get("max_input_channels", 0) or 0) > 0,
                    }
                    devices.append(device)
                    if device["is_input"]:
                        input_devices.append(device)
                    else:
                        output_devices.append(device)
            except Exception as e:
                logger.error(f"Error listando dispositivos Linux/macOS: {e}")

    except Exception as e:
        logger.error(f"Error listando dispositivos: {e}")

    return {
        "platform": _platform.system().lower(),
        "devices": devices,
        "input_devices": input_devices,
        "output_devices": output_devices,
        "loopback_devices": loopback_devices,
    }


def _resolve_device_index(
    selected_device_index: Optional[int] = None,
    selected_output_index: Optional[int] = None,
) -> Optional[int]:
    """Resolver índice final de dispositivo de entrada a usar.

    - En Windows, si se da un índice de salida, busca el input loopback correspondiente por nombre.
    - Si se da un índice de entrada válido, úsalo.
    - Si nada válido, retorna None para usar el fallback automático.
    """
    import platform as _platform
    final_index = None
    try:
        if _platform.system().lower() == "windows":
            import pyaudiowpatch as pyaudio
            pa = pyaudio.PyAudio()
            device_count = pa.get_device_count()

            # Si se indicó dispositivo de entrada explícito y es válido
            if selected_device_index is not None:
                try:
                    info = pa.get_device_info_by_index(int(selected_device_index))
                    if (info.get("maxInputChannels", 0) or 0) > 0:
                        final_index = int(selected_device_index)
                        pa.terminate()
                        return final_index
                except Exception:
                    pass

            # Si se indicó un dispositivo de salida, buscar su loopback
            if selected_output_index is not None:
                try:
                    out_info = pa.get_device_info_by_index(int(selected_output_index))
                    out_name = str(out_info.get("name", ""))
                    loopback_candidate = None
                    for i in range(device_count):
                        info = pa.get_device_info_by_index(i)
                        name = str(info.get("name", ""))
                        if (
                            (info.get("maxInputChannels", 0) or 0) > 0
                            and "loopback" in name.lower()
                            and out_name.split(" (")[0].lower() in name.lower()
                        ):
                            loopback_candidate = i
                            break
                    if loopback_candidate is not None:
                        final_index = loopback_candidate
                        pa.terminate()
                        return final_index
                except Exception:
                    pass

            pa.terminate()
        else:
            # En Linux/macOS solo se usa el índice de entrada
            if selected_device_index is not None:
                final_index = int(selected_device_index)
                return final_index
    except Exception as e:
        logger.error(f"Error resolviendo índice de dispositivo: {e}")

    return final_index


def start_audio_capture(
    selected_device_index: Optional[int] = None,
    selected_output_index: Optional[int] = None,
) -> Dict[str, any]:
    """Iniciar captura de audio."""
    if app_state["is_capturing"]:
        return {"success": False, "message": "Captura ya activa"}
    
    try:
        # Resolver dispositivo preferido
        resolved_index = _resolve_device_index(
            selected_device_index, selected_output_index
        )

        # Guardar selección
        app_state["selected_device_index"] = resolved_index
        app_state["selected_output_index"] = (
            int(selected_output_index) if selected_output_index is not None else None
        )

        # Crear capturador de audio
        app_state["audio_capture"] = AudioCapture(
            sample_rate=16000,
            chunk_size=1024,
            preferred_device_index=resolved_index,
        )
        
        # Iniciar captura con callback
        app_state["audio_capture"].start_capture(callback=audio_callback)
        app_state["is_capturing"] = True
        
        logger.info("🎵 Captura de audio iniciada")
        return {
            "success": True,
            "message": "Captura iniciada",
            "device_index": resolved_index,
        }
        
    except AudioCaptureError as e:
        logger.error(f"❌ Error iniciando captura: {e}")
        return {"success": False, "message": str(e)}
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return {"success": False, "message": f"Error interno: {e}"}

def stop_audio_capture() -> Dict[str, any]:
    """Detener captura de audio."""
    if not app_state["is_capturing"]:
        return {"success": False, "message": "Captura no activa"}
    
    try:
        if app_state["audio_capture"]:
            app_state["audio_capture"].stop_capture()
            app_state["audio_capture"] = None
        
        # Procesar audio restante
        if app_state["transcriber"]:
            final_result = app_state["transcriber"].flush()
            if final_result and final_result.get("text", "").strip():
                app_state["transcription_queue"].put(final_result)
        
        app_state["is_capturing"] = False
        logger.info("⏹️ Captura de audio detenida")
        return {"success": True, "message": "Captura detenida"}
        
    except Exception as e:
        logger.error(f"❌ Error deteniendo captura: {e}")
        return {"success": False, "message": f"Error deteniendo: {e}"}

# Endpoints REST

@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "name": "Audio Transcribe API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "status": "/status",
            "start": "/start_capture",
            "stop": "/stop_capture",
            "transcription": "/get_transcription",
            "websocket": "/ws"
        }
    }

@app.get("/status")
async def get_status():
    """Obtener estado actual del sistema."""
    transcriber_info = {}
    if app_state["transcriber"]:
        transcriber_info = app_state["transcriber"].transcriber.get_model_info()
    
    return {
        "is_capturing": app_state["is_capturing"],
        "connected_clients": len(app_state["connected_clients"]),
        "transcription_queue_size": app_state["transcription_queue"].qsize(),
        "transcriber": transcriber_info
    }


@app.get("/audio/devices")
async def get_audio_devices():
    """Obtener lista de dispositivos de audio disponibles."""
    return _list_audio_devices()

@app.post("/start_capture")
async def start_capture():
    """Iniciar captura de audio."""
    result = start_audio_capture()
    
    if result["success"]:
        return JSONResponse(content=result, status_code=200)
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@app.post("/stop_capture")
async def stop_capture():
    """Detener captura de audio."""
    result = stop_audio_capture()
    
    if result["success"]:
        return JSONResponse(content=result, status_code=200)
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@app.get("/get_transcription")
async def get_transcription():
    """Obtener transcripciones pendientes."""
    transcriptions = []
    
    # Obtener todas las transcripciones disponibles
    while not app_state["transcription_queue"].empty():
        try:
            transcription = app_state["transcription_queue"].get_nowait()
            transcriptions.append(transcription)
        except queue.Empty:
            break
    
    return {
        "transcriptions": transcriptions,
        "count": len(transcriptions)
    }

@app.get("/models")
async def get_models():
    """Obtener lista de modelos disponibles."""
    if app_state["transcriber"]:
        return app_state["transcriber"].transcriber.get_available_models()
    else:
        return {"error": "Transcriptor no inicializado"}

@app.post("/models/{model_id}/load")
async def load_model(model_id: str, language: str = "spanish"):
    """Cargar un modelo específico."""
    if not app_state["transcriber"]:
        raise HTTPException(status_code=400, detail="Transcriptor no inicializado")
    
    # Detener captura si está activa
    was_capturing = app_state["is_capturing"]
    if was_capturing:
        stop_audio_capture()
    
    try:
        success = app_state["transcriber"].transcriber.change_model(model_id, language)
        
        if success:
            # Reiniciar captura si estaba activa
            if was_capturing:
                start_audio_capture()
            
            return {"success": True, "message": f"Modelo {model_id} cargado exitosamente"}
        else:
            raise HTTPException(status_code=400, detail=f"Error cargando modelo {model_id}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_id}/download")
async def download_model(model_id: str):
    """Descargar un modelo específico."""
    if not app_state["transcriber"]:
        raise HTTPException(status_code=400, detail="Transcriptor no inicializado")
    
    try:
        model_manager = app_state["transcriber"].transcriber.model_manager
        success = model_manager.download_model(model_id)
        
        if success:
            return {"success": True, "message": f"Modelo {model_id} descargado exitosamente"}
        else:
            raise HTTPException(status_code=400, detail=f"Error descargando modelo {model_id}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/add_transcription")  
async def debug_add_transcription(transcription: dict):
    """Endpoint de debug para agregar transcripción de prueba."""
    logger.info(f"🧪 Debug: Agregando transcripción de prueba: {transcription.get('text', '')}")
    app_state["transcription_queue"].put(transcription)
    return {"success": True, "message": "Transcripción agregada a la cola", "queue_size": app_state["transcription_queue"].qsize()}

# WebSocket para tiempo real

async def broadcast_to_clients(message: Dict):
    """Enviar mensaje a todos los clientes conectados."""
    if not app_state["connected_clients"]:
        logger.debug("📡 No hay clientes conectados para broadcast")
        return
    
    disconnected_clients = set()
    message_str = json.dumps(message)
    
    # Solo log para transcripciones, no para cada envío
    if message.get('type') == 'transcription':
        logger.debug(f"📡 Enviando transcripción a {len(app_state['connected_clients'])} clientes")
    else:
        logger.info(f"📡 Enviando a {len(app_state['connected_clients'])} clientes: {message.get('type', 'unknown')}")
    
    for client in app_state["connected_clients"]:
        try:
            await client.send_text(message_str)
        except Exception as e:
            logger.warning(f"❌ Error enviando a cliente: {e}")
            disconnected_clients.add(client)
    
    # Remover clientes desconectados
    if disconnected_clients:
        app_state["connected_clients"] -= disconnected_clients
        logger.info(f"🔌 Removidos {len(disconnected_clients)} clientes desconectados")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para comunicación en tiempo real."""
    await websocket.accept()
    app_state["connected_clients"].add(websocket)
    
    logger.info(f"🔌 Cliente WebSocket conectado. Total: {len(app_state['connected_clients'])}")
    
    # Enviar estado inicial
    status_message = {
        "type": "status",
        "data": {
            "is_capturing": app_state["is_capturing"],
            "message": "Conectado al servidor"
        }
    }
    await websocket.send_text(json.dumps(status_message))
    
    try:
        while True:
            # Recibir mensajes del cliente
            message = await websocket.receive_text()
            data = json.loads(message)
            
            command = data.get("command")
            response = {"type": "response", "command": command}
            
            if command == "start_capture":
                device_index = data.get("device_index")
                output_device_index = data.get("output_device_index")
                result = start_audio_capture(device_index, output_device_index)
                response["data"] = result
                
            elif command == "stop_capture":
                result = stop_audio_capture()
                response["data"] = result
                
            elif command == "get_status":
                response["data"] = {
                    "is_capturing": app_state["is_capturing"],
                    "queue_size": app_state["transcription_queue"].qsize()
                }
            
            else:
                response["data"] = {"success": False, "message": "Comando desconocido"}
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        app_state["connected_clients"].discard(websocket)
        logger.info(f"🔌 Cliente WebSocket desconectado. Total: {len(app_state['connected_clients'])}")
    
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        app_state["connected_clients"].discard(websocket)

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Ejecutar servidor de desarrollo."""
    logger.info(f"🌐 Iniciando servidor en http://{host}:{port}")
    logger.info("📋 Endpoints disponibles:")
    logger.info("   • GET  /              - Información de la API")
    logger.info("   • GET  /status        - Estado del sistema")
    logger.info("   • POST /start_capture - Iniciar captura")
    logger.info("   • POST /stop_capture  - Detener captura")
    logger.info("   • GET  /get_transcription - Obtener transcripciones")
    logger.info("   • WS   /ws            - WebSocket tiempo real")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    # Ejecutar servidor de desarrollo
    run_server(reload=True)