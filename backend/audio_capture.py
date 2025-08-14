"""
Módulo para captura de audio del sistema multiplataforma.
Soporta Windows (PyAudioWPatch) y Linux (sounddevice).
"""

import platform
import numpy as np
import threading
import queue
import time
from typing import Optional, Callable
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioCaptureError(Exception):
    """Excepción personalizada para errores de captura de audio."""
    pass

class AudioCapture:
    """
    Clase para capturar audio del sistema de forma multiplataforma.
    """
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        """
        Inicializar capturador de audio.
        
        Args:
            sample_rate: Frecuencia de muestreo en Hz (16kHz es óptimo para Whisper)
            chunk_size: Tamaño del buffer en samples
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_capturing = False
        self.audio_queue = queue.Queue()
        self.capture_thread = None
        self.platform = platform.system().lower()
        
        logger.info(f"Inicializando AudioCapture para {self.platform}")
        logger.info(f"Sample rate: {sample_rate}Hz, Chunk size: {chunk_size}")
        
    def _capture_linux(self, callback: Optional[Callable] = None):
        """
        Captura de audio en Linux usando sounddevice.
        
        Args:
            callback: Función opcional para procesar chunks en tiempo real
        """
        try:
            import sounddevice as sd
            
            # Listar dispositivos disponibles para debug
            logger.info("Dispositivos de audio disponibles:")
            logger.info(sd.query_devices())
            
            # Configurar dispositivo por defecto
            device_info = sd.query_devices(kind='input')
            logger.info(f"Dispositivo de entrada por defecto: {device_info}")
            
            def audio_callback(indata, frames, time, status):
                """Callback para procesar audio capturado."""
                if status:
                    logger.warning(f"Audio callback status: {status}")
                
                # Convertir a mono si es estéreo
                if indata.shape[1] > 1:
                    audio_data = np.mean(indata, axis=1)
                else:
                    audio_data = indata[:, 0]
                
                # Agregar a la cola
                self.audio_queue.put(audio_data.copy())
                
                # Llamar callback personalizado si existe
                if callback:
                    callback(audio_data)
            
            # Iniciar captura
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,  # Mono
                dtype=np.float32,
                blocksize=self.chunk_size,
                callback=audio_callback
            ):
                logger.info("Captura de audio iniciada en Linux")
                while self.is_capturing:
                    time.sleep(0.1)
                    
        except ImportError:
            raise AudioCaptureError("sounddevice no está instalado")
        except Exception as e:
            raise AudioCaptureError(f"Error en captura Linux: {e}")
    
    def _capture_windows(self, callback: Optional[Callable] = None):
        """
        Captura de audio en Windows usando PyAudioWPatch.
        
        Args:
            callback: Función opcional para procesar chunks en tiempo real
        """
        try:
            import PyAudioWPatch as pyaudio
            
            # Configurar PyAudio
            audio = pyaudio.PyAudio()
            
            # Buscar dispositivo loopback (WASAPI)
            wasapi_info = None
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                if ("loopback" in device_info["name"].lower() or 
                    device_info["hostApi"] == 3):  # WASAPI
                    wasapi_info = device_info
                    break
            
            if not wasapi_info:
                logger.warning("No se encontró dispositivo loopback, usando micrófono")
                wasapi_info = audio.get_default_input_device_info()
            
            logger.info(f"Usando dispositivo: {wasapi_info['name']}")
            
            def audio_callback(in_data, frame_count, time_info, status):
                """Callback para procesar audio capturado."""
                if status:
                    logger.warning(f"Audio callback status: {status}")
                
                # Convertir bytes a numpy array
                audio_data = np.frombuffer(in_data, dtype=np.float32)
                
                # Agregar a la cola
                self.audio_queue.put(audio_data.copy())
                
                # Llamar callback personalizado si existe
                if callback:
                    callback(audio_data)
                
                return (None, pyaudio.paContinue)
            
            # Iniciar stream
            stream = audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=wasapi_info["index"],
                frames_per_buffer=self.chunk_size,
                stream_callback=audio_callback
            )
            
            stream.start_stream()
            logger.info("Captura de audio iniciada en Windows")
            
            while self.is_capturing and stream.is_active():
                time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
        except ImportError:
            raise AudioCaptureError("PyAudioWPatch no está instalado")
        except Exception as e:
            raise AudioCaptureError(f"Error en captura Windows: {e}")
    
    def start_capture(self, callback: Optional[Callable] = None):
        """
        Iniciar captura de audio.
        
        Args:
            callback: Función opcional para procesar chunks en tiempo real
        """
        if self.is_capturing:
            logger.warning("La captura ya está activa")
            return
        
        self.is_capturing = True
        
        # Seleccionar método según plataforma
        if self.platform == "windows":
            capture_func = self._capture_windows
        elif self.platform == "linux":
            capture_func = self._capture_linux
        else:
            raise AudioCaptureError(f"Plataforma {self.platform} no soportada")
        
        # Iniciar thread de captura
        self.capture_thread = threading.Thread(
            target=capture_func, 
            args=(callback,),
            daemon=True
        )
        self.capture_thread.start()
        
        logger.info("Captura de audio iniciada")
    
    def stop_capture(self):
        """Detener captura de audio."""
        if not self.is_capturing:
            logger.warning("La captura no está activa")
            return
        
        self.is_capturing = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        
        logger.info("Captura de audio detenida")
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Obtener chunk de audio de la cola.
        
        Args:
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Array de numpy con datos de audio o None si timeout
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_buffer_size(self) -> int:
        """Obtener tamaño actual del buffer."""
        return self.audio_queue.qsize()
    
    def clear_buffer(self):
        """Limpiar buffer de audio."""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break


def test_audio_capture():
    """Función de test para verificar captura de audio."""
    print("🎵 Iniciando test de captura de audio...")
    
    capture = AudioCapture(sample_rate=16000, chunk_size=1024)
    
    def audio_callback(data):
        """Callback para mostrar estadísticas de audio."""
        volume = np.sqrt(np.mean(data**2))
        if volume > 0.01:  # Solo mostrar si hay sonido
            print(f"📊 Audio detectado - Volumen: {volume:.4f}")
    
    try:
        # Iniciar captura
        capture.start_capture(callback=audio_callback)
        
        print("🔴 Capturando audio... (presiona Ctrl+C para detener)")
        print("💡 Reproduce algo de audio para ver la detección")
        
        # Capturar por 10 segundos o hasta Ctrl+C
        for i in range(100):
            time.sleep(0.1)
            buffer_size = capture.get_buffer_size()
            if buffer_size > 0:
                print(f"📦 Buffer: {buffer_size} chunks")
    
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo captura...")
    
    finally:
        capture.stop_capture()
        print("✅ Test completado")


if __name__ == "__main__":
    test_audio_capture()