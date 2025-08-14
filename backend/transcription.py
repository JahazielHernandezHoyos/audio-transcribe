"""
Módulo para transcripción de audio usando Whisper via transformers.
Optimizado para tiempo real con el modelo tiny.
"""

import os
import sys

# CRITICAL: Set CUDA environment variables BEFORE any torch imports
# This prevents PyTorch from loading CUDA libraries that cause crashes
if not os.getenv("CUDA_VISIBLE_DEVICES"):
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
if not os.getenv("FORCE_DEVICE"):
    os.environ["FORCE_DEVICE"] = "cpu"

import numpy as np
import torch
import logging
import time
import warnings
from typing import Optional, List, Dict
from transformers import (
    WhisperProcessor, 
    WhisperForConditionalGeneration,
    pipeline
)
from model_manager import ModelManager

# Suprimir warnings verbosos
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionError(Exception):
    """Excepción personalizada para errores de transcripción."""
    pass

class WhisperTranscriber:
    """
    Transcriptor de audio usando ModelManager para múltiples modelos Whisper.
    """
    
    def __init__(self, model_id: str = "tiny", language: str = "spanish"):
        """
        Inicializar transcriptor.
        
        Args:
            model_id: ID del modelo Whisper (tiny, base, small, medium, large)
            language: Idioma para transcripción ("spanish", "english", "auto")
        """
        self.model_id = model_id
        self.language = language
        self.model_manager = ModelManager()
        
        logger.info(f"Inicializando Whisper con ModelManager: {model_id}")
        logger.info(f"Idioma: {language}")
        
        self._load_model()
    
    def _get_device(self) -> str:
        """Detectar dispositivo óptimo (CPU/GPU)."""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"GPU disponible: {torch.cuda.get_device_name()}")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"  # Apple Silicon
            logger.info("Apple MPS disponible")
        else:
            device = "cpu"
            logger.info("Usando CPU")
        
        return device
    
    def _load_model(self):
        """Cargar modelo usando ModelManager."""
        try:
            success = self.model_manager.load_model(self.model_id, self.language)
            if not success:
                raise TranscriptionError(f"Error cargando modelo {self.model_id}")
            
        except Exception as e:
            raise TranscriptionError(f"Error cargando modelo: {e}")
    
    def _warmup_model(self):
        """Calentar modelo con audio sintético."""
        try:
            logger.info("Calentando modelo...")
            
            # Audio sintético corto
            sample_rate = 16000
            duration = 1.0  # 1 segundo
            synthetic_audio = np.random.randn(int(sample_rate * duration)).astype(np.float32)
            
            # Transcripción de prueba
            start_time = time.time()
            _ = self.transcribe_chunk(synthetic_audio, sample_rate)
            warmup_time = time.time() - start_time
            
            logger.info(f"Modelo calentado en {warmup_time:.2f}s")
            
        except Exception as e:
            logger.warning(f"Error en warmup: {e}")
    
    def transcribe_chunk(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, any]:
        """
        Transcribir chunk de audio.
        
        Args:
            audio_data: Array numpy con datos de audio
            sample_rate: Frecuencia de muestreo
            
        Returns:
            Dict con resultado de transcripción
        """
        if len(audio_data) == 0:
            return {"text": "", "confidence": 0.0, "processing_time": 0.0}
        
        try:
            start_time = time.time()
            
            # Normalizar audio
            audio_data = audio_data.astype(np.float32)
            
            # Whisper espera audio en rango [-1, 1]
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Detectar silencio usando múltiples métricas
            rms_volume = np.sqrt(np.mean(audio_data**2))
            max_amplitude = np.max(np.abs(audio_data))
            
            # Umbrales para detección de voz
            rms_threshold = 0.01      # Umbral RMS mínimo
            amplitude_threshold = 0.02 # Umbral de amplitud máxima
            
            # Detección simple de actividad de voz
            has_voice_activity = (rms_volume > rms_threshold and 
                                max_amplitude > amplitude_threshold)
            
            if not has_voice_activity:
                logger.debug(f"Sin actividad de voz (RMS: {rms_volume:.4f}, Max: {max_amplitude:.4f})")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "processing_time": time.time() - start_time,
                    "language": self.language,
                    "volume": rms_volume,
                    "max_amplitude": max_amplitude,
                    "skipped": "no_voice_activity"
                }
            
            # Usar ModelManager para transcribir
            result = self.model_manager.transcribe(audio_data, sample_rate)
            
            # Agregar métricas de audio
            result.update({
                "confidence": min(1.0, len(result.get("text", "")) / 50.0),
                "language": self.language,
                "volume": rms_volume,
                "max_amplitude": max_amplitude,
                "audio_length": len(audio_data) / sample_rate
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error en transcripción: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "processing_time": 0.0,
                "error": str(e)
            }
    
    def transcribe_file(self, audio_file_path: str) -> Dict[str, any]:
        """
        Transcribir archivo de audio completo.
        
        Args:
            audio_file_path: Ruta al archivo de audio
            
        Returns:
            Dict con resultado de transcripción
        """
        if self.pipe is None:
            raise TranscriptionError("Modelo no cargado")
        
        try:
            logger.info(f"Transcribiendo archivo: {audio_file_path}")
            start_time = time.time()
            
            result = self.pipe(audio_file_path)
            processing_time = time.time() - start_time
            
            text = result.get("text", "").strip()
            
            return {
                "text": text,
                "confidence": 1.0,  # Pipeline no proporciona confianza
                "processing_time": processing_time,
                "language": self.language,
                "file": audio_file_path
            }
            
        except Exception as e:
            logger.error(f"Error transcribiendo archivo: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "processing_time": 0.0,
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, any]:
        """Obtener información del modelo."""
        model_info = self.model_manager.get_current_model_info()
        model_info.update({
            "language": self.language,
            "model_id": self.model_id
        })
        return model_info
    
    def change_model(self, model_id: str, language: str = None) -> bool:
        """
        Cambiar a un modelo diferente.
        
        Args:
            model_id: ID del nuevo modelo
            language: Nuevo idioma (opcional)
            
        Returns:
            True si el cambio fue exitoso
        """
        try:
            if language:
                self.language = language
            
            success = self.model_manager.load_model(model_id, self.language)
            if success:
                self.model_id = model_id
                logger.info(f"✅ Cambiado a modelo {model_id}")
                return True
            else:
                logger.error(f"❌ Error cambiando a modelo {model_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error cambiando modelo: {e}")
            return False
    
    def get_available_models(self) -> Dict:
        """Obtener modelos disponibles."""
        return self.model_manager.get_available_models()


class RealTimeTranscriber:
    """
    Transcriptor optimizado para tiempo real con buffer de chunks.
    """
    
    def __init__(self, chunk_duration: float = 3.0, overlap_duration: float = 0.5):
        """
        Inicializar transcriptor en tiempo real.
        
        Args:
            chunk_duration: Duración del chunk en segundos
            overlap_duration: Solapamiento entre chunks en segundos
        """
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.sample_rate = 16000
        
        self.chunk_size = int(chunk_duration * self.sample_rate)
        self.overlap_size = int(overlap_duration * self.sample_rate)
        
        self.audio_buffer = np.array([], dtype=np.float32)
        self.transcriber = WhisperTranscriber()
        
        logger.info(f"Transcriptor tiempo real: chunks {chunk_duration}s, overlap {overlap_duration}s")
    
    def add_audio(self, audio_data: np.ndarray) -> Optional[Dict[str, any]]:
        """
        Agregar audio al buffer y transcribir si hay suficiente datos.
        
        Args:
            audio_data: Nuevos datos de audio
            
        Returns:
            Resultado de transcripción si hay chunk completo, None si no
        """
        # Agregar al buffer
        self.audio_buffer = np.concatenate([self.audio_buffer, audio_data])
        
        # Verificar si tenemos chunk completo
        if len(self.audio_buffer) >= self.chunk_size:
            # Extraer chunk
            chunk = self.audio_buffer[:self.chunk_size]
            
            # Mantener overlap para continuidad
            self.audio_buffer = self.audio_buffer[self.chunk_size - self.overlap_size:]
            
            # Transcribir chunk
            return self.transcriber.transcribe_chunk(chunk, self.sample_rate)
        
        return None
    
    def flush(self) -> Optional[Dict[str, any]]:
        """
        Transcribir cualquier audio restante en el buffer.
        
        Returns:
            Resultado de transcripción del audio restante
        """
        if len(self.audio_buffer) > 0:
            chunk = self.audio_buffer.copy()
            self.audio_buffer = np.array([], dtype=np.float32)
            return self.transcriber.transcribe_chunk(chunk, self.sample_rate)
        
        return None


def test_transcription():
    """Test de transcripción con audio sintético."""
    logger.info("🧪 Iniciando test de transcripción...")
    
    # Crear transcriptor
    transcriber = WhisperTranscriber(language="spanish")
    
    # Test con silencio
    logger.info("Test 1: Silencio")
    silence = np.zeros(16000, dtype=np.float32)  # 1 segundo de silencio
    result = transcriber.transcribe_chunk(silence)
    logger.info(f"Resultado: {result}")
    
    # Test con ruido
    logger.info("Test 2: Ruido blanco")
    noise = np.random.randn(16000).astype(np.float32) * 0.1
    result = transcriber.transcribe_chunk(noise)
    logger.info(f"Resultado: {result}")
    
    # Test tiempo real
    logger.info("Test 3: Transcriptor tiempo real")
    rt_transcriber = RealTimeTranscriber(chunk_duration=2.0)
    
    # Simular chunks de audio
    for i in range(5):
        chunk = np.random.randn(1024).astype(np.float32) * 0.1
        result = rt_transcriber.add_audio(chunk)
        if result:
            logger.info(f"Chunk {i}: {result}")
    
    # Flush final
    final_result = rt_transcriber.flush()
    if final_result:
        logger.info(f"Final: {final_result}")
    
    logger.info("✅ Test de transcripción completado")


if __name__ == "__main__":
    test_transcription()