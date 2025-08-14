"""
Módulo para captura de audio del sistema multiplataforma.
Soporta Windows (PyAudioWPatch) y Linux (sounddevice).
"""

import logging
import platform
import queue
import threading
import time
from collections.abc import Callable

import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioCaptureError(Exception):
    """Excepción personalizada para errores de captura de audio."""


class AudioCapture:
    """
    Clase para capturar audio del sistema de forma multiplataforma.
    """

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024, preferred_device_index: Optional[int] = None):
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
        self.device_sample_rate = sample_rate  # Actual sample rate del dispositivo en Windows
        self.preferred_device_index = preferred_device_index

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
            device_info = sd.query_devices(kind="input")
            logger.info(f"Dispositivo de entrada por defecto: {device_info}")

            def audio_callback(indata, frames, time_info, status):
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
                callback=audio_callback,
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
            import pyaudiowpatch as pyaudio

            # Configurar PyAudio
            audio = pyaudio.PyAudio()

            logger.info("🔍 Buscando dispositivos de audio en Windows...")

            # Buscar dispositivo (WASAPI)
            wasapi_info = None
            devices_found = []

            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                devices_found.append(f"  {i}: {device_info['name']} ({device_info['maxInputChannels']} in)")

                # Si hay un índice preferido válido, seleccionarlo
                if (
                    self.preferred_device_index is not None
                    and i == int(self.preferred_device_index)
                    and device_info["maxInputChannels"] > 0
                ):
                    wasapi_info = device_info
                    logger.info(
                        f"✅ Usando dispositivo preferido: {device_info['name']} (index {i})"
                    )
                    break

                # Fallback heurístico: priorizar loopback, si no, cualquier WASAPI con entrada
                if not wasapi_info and device_info["maxInputChannels"] > 0:
                    if "loopback" in device_info["name"].lower():
                        wasapi_info = device_info
                    elif device_info.get("hostApi") == 3:
                        wasapi_info = device_info

            logger.info("📋 Dispositivos de audio encontrados:")
            for device in devices_found:
                logger.info(device)

            if not wasapi_info:
                logger.warning(
                    "⚠️ No se encontró dispositivo loopback, usando micrófono por defecto"
                )
                try:
                    wasapi_info = audio.get_default_input_device_info()
                except Exception as e:
                    logger.error(f"Error obteniendo dispositivo por defecto: {e}")
                    audio.terminate()
                    raise AudioCaptureError(
                        "No se pudo encontrar ningún dispositivo de entrada"
                    )

            logger.info(f"🎤 Usando dispositivo: {wasapi_info['name']}")

            # Determinar sample rate soportado por el dispositivo
            device_sample_rate = int(
                wasapi_info.get("defaultSampleRate", self.sample_rate)
            )
            preferred_rates = [device_sample_rate, 48000, 44100, 32000, 22050, 16000]
            # Deduplicar manteniendo orden
            rates_to_try = []
            for rate in preferred_rates:
                if rate not in rates_to_try and rate > 0:
                    rates_to_try.append(rate)
            logger.info(
                f"📶 Sample rates candidatos (device->target): {rates_to_try} -> {self.sample_rate}"
            )

            def audio_callback(in_data, frame_count, time_info, status):
                """Callback para procesar audio capturado."""
                if status:
                    logger.warning(f"⚠️ Audio callback status: {status}")

                try:
                    # Convertir bytes a numpy array
                    audio_data = np.frombuffer(in_data, dtype=np.float32)

                    # Re-muestrear si el dispositivo no coincide con el sample rate objetivo
                    if (
                        self.device_sample_rate != self.sample_rate
                        and self.device_sample_rate > 0
                    ):
                        audio_data = self._resample_audio(
                            audio_data, self.device_sample_rate, self.sample_rate
                        )

                    # Agregar a la cola
                    self.audio_queue.put(audio_data.copy())

                    # Llamar callback personalizado si existe
                    if callback:
                        callback(audio_data)

                except Exception as e:
                    logger.error(f"Error en audio callback: {e}")

                return (None, pyaudio.paContinue)

            # Iniciar stream intentando con distintos sample rates soportados
            stream = None
            last_error = None
            for rate in rates_to_try:
                try:
                    stream = audio.open(
                        format=pyaudio.paFloat32,
                        channels=1,
                        rate=rate,
                        input=True,
                        input_device_index=wasapi_info["index"],
                        frames_per_buffer=self.chunk_size,
                        stream_callback=audio_callback,
                    )
                    self.device_sample_rate = rate
                    logger.info(
                        f"🎚️ Stream abierto con sample rate del dispositivo: {rate} Hz"
                    )
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"⚠️ Falló abrir stream con {rate} Hz: {e}")

            try:
                if stream is None:
                    raise last_error or RuntimeError(
                        "No se pudo abrir el stream con los sample rates probados"
                    )
                stream.start_stream()
                logger.info("🎵 Captura de audio iniciada en Windows (WASAPI)")
                while self.is_capturing and stream.is_active():
                    time.sleep(0.1)
                stream.stop_stream()
                stream.close()
                logger.info("⏹️ Stream de audio cerrado")
            except Exception as e:
                logger.error(f"Error configurando stream de audio: {e}")
                raise
            finally:
                audio.terminate()

        except ImportError as e:
            error_msg = """
PyAudioWPatch no está instalado. Para Windows necesitas:

1. Instalar PyAudioWPatch:
   pip install PyAudioWPatch

2. O con UV:
   uv add PyAudioWPatch

3. Alternativamente, usa el instalador automático:
   uv sync
"""
            logger.error(error_msg)
            raise AudioCaptureError(f"PyAudioWPatch requerido para Windows: {e}")

        except Exception as e:
            logger.error(f"Error en captura Windows: {e}")
            raise AudioCaptureError(f"Error en captura Windows: {e}")

    def _resample_audio(
        self, audio_data: np.ndarray, from_rate: int, to_rate: int
    ) -> np.ndarray:
        """Resample audio using linear interpolation.

        Args:
            audio_data: Input mono float32 audio array
            from_rate: Original sample rate
            to_rate: Target sample rate

        Returns:
            Resampled mono float32 audio array
        """
        if from_rate == to_rate or len(audio_data) == 0:
            return audio_data.astype(np.float32, copy=False)
        try:
            original_indices = np.arange(audio_data.shape[0], dtype=np.float64)
            resampled_length = int(
                round(audio_data.shape[0] * float(to_rate) / float(from_rate))
            )
            if resampled_length <= 1:
                return audio_data.astype(np.float32, copy=False)
            resampled_indices = np.linspace(
                0, audio_data.shape[0] - 1, num=resampled_length, dtype=np.float64
            )
            resampled = np.interp(
                resampled_indices, original_indices, audio_data.astype(np.float64)
            )
            return resampled.astype(np.float32, copy=False)
        except Exception as e:
            logger.warning(
                f"Fallo al remuestrear audio de {from_rate} a {to_rate}: {e}"
            )
            return audio_data.astype(np.float32, copy=False)

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
            target=capture_func, args=(callback,), daemon=True
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
        volume = np.sqrt(np.mean(data ** 2))
        if volume > 0.01:  # Solo mostrar si hay sonido
            print(f"📊 Audio detectado - Volumen: {volume:.4f}")

    try:
        # Iniciar captura
        capture.start_capture(callback=audio_callback)

        print("🔴 Capturando audio... (presiona Ctrl+C para detener)")
        print("💡 Reproduce algo de audio para ver la detección")

        # Capturar por 10 segundos o hasta Ctrl+C
        for _ in range(100):
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


