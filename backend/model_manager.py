"""
Gestor de modelos Whisper con descarga automática y selección de usuario.
Permite cambiar entre diferentes tamaños de modelos según necesidades.
"""

import os

# CRITICAL: Set CUDA environment variables BEFORE any torch imports
# This prevents PyTorch from loading CUDA libraries that cause crashes
if not os.getenv("CUDA_VISIBLE_DEVICES"):
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
if not os.getenv("FORCE_DEVICE"):
    os.environ["FORCE_DEVICE"] = "cpu"

import json
import logging
import time
from pathlib import Path

import torch
from transformers import pipeline

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    """Gestor de modelos Whisper con descarga automática."""

    # Configuración de modelos disponibles
    AVAILABLE_MODELS = {
        "tiny": {
            "name": "openai/whisper-tiny",
            "size_mb": 39,
            "description": "Más rápido, menor precisión",
            "languages": ["español", "inglés", "auto"],
            "speed": "⚡⚡⚡",
            "accuracy": "⭐⭐",
            "recommended_for": "Tiempo real, recursos limitados"
        },
        "base": {
            "name": "openai/whisper-base",
            "size_mb": 74,
            "description": "Balance velocidad/precisión",
            "languages": ["español", "inglés", "auto"],
            "speed": "⚡⚡",
            "accuracy": "⭐⭐⭐",
            "recommended_for": "Uso general, buena calidad"
        },
        "small": {
            "name": "openai/whisper-small",
            "size_mb": 244,
            "description": "Buena precisión, velocidad moderada",
            "languages": ["español", "inglés", "auto"],
            "speed": "⚡",
            "accuracy": "⭐⭐⭐⭐",
            "recommended_for": "Transcripción de calidad"
        },
        "medium": {
            "name": "openai/whisper-medium",
            "size_mb": 769,
            "description": "Alta precisión, más lento",
            "languages": ["español", "inglés", "auto"],
            "speed": "⚡",
            "accuracy": "⭐⭐⭐⭐⭐",
            "recommended_for": "Máxima calidad, audio complejo"
        },
        "large": {
            "name": "openai/whisper-large-v3",
            "size_mb": 1550,
            "description": "Máxima precisión, requiere recursos",
            "languages": ["español", "inglés", "auto", "99+ idiomas"],
            "speed": "🐌",
            "accuracy": "⭐⭐⭐⭐⭐",
            "recommended_for": "Transcripción profesional"
        }
    }

    def __init__(self, models_dir: str = "models"):
        """
        Inicializar gestor de modelos.

        Args:
            models_dir: Directorio para guardar modelos descargados
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        self.config_file = self.models_dir / "model_config.json"
        self.current_model = None
        self.current_pipeline = None
        self.device = self._get_device()

        # Cargar configuración guardada
        self.config = self._load_config()

        logger.info(f"📁 Directorio de modelos: {self.models_dir}")
        logger.info(f"🖥️ Dispositivo: {self.device}")

    def _get_device(self) -> str:
        """Detect optimal device, defaulting to CPU to avoid CUDA issues."""
        # Respect explicit override
        force_device = os.getenv("FORCE_DEVICE", "").lower().strip()
        if force_device in {"cpu", "cuda", "mps"}:
            if force_device == "cuda":
                try:
                    return "cuda" if torch.cuda.is_available() else "cpu"
                except Exception:
                    return "cpu"
            if force_device == "mps":
                try:
                    return "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu"
                except Exception:
                    return "cpu"
            return "cpu"

        # Honor common disabling flags
        if os.getenv("DISABLE_CUDA") or os.getenv("CUDA_VISIBLE_DEVICES", None) == "":
            return "cpu"

        # Default to CPU to prevent crashes from CUDA initialization in some environments
        try:
            if os.getenv("ENABLE_CUDA") and torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass

        try:
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except Exception:
            pass

        return "cpu"

    def _load_config(self) -> dict:
        """Cargar configuración de modelos."""
        if self.config_file.exists():
            try:
                with self.config_file.open() as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando config: {e}")

        # Configuración por defecto
        return {
            "current_model": "tiny",
            "downloaded_models": [],
            "last_updated": None
        }

    def _save_config(self):
        """Guardar configuración de modelos."""
        try:
            with self.config_file.open("w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando config: {e}")

    def get_available_models(self) -> dict:
        """Obtener lista de modelos disponibles con información."""
        models_info = {}

        for model_id, info in self.AVAILABLE_MODELS.items():
            model_info = info.copy()

            # Verificar si está descargado
            model_info["downloaded"] = model_id in self.config.get("downloaded_models", [])
            model_info["is_current"] = model_id == self.config.get("current_model")

            # Estimar tiempo de descarga (aproximado)
            size_mb = model_info["size_mb"]
            estimated_download_min = max(1, size_mb // 50)  # ~50MB/min promedio
            model_info["estimated_download_time"] = f"~{estimated_download_min} min"

            models_info[model_id] = model_info

        return models_info

    def download_model(self, model_id: str, progress_callback=None) -> bool:
        """
        Descargar un modelo específico.

        Args:
            model_id: ID del modelo a descargar
            progress_callback: Función para reportar progreso

        Returns:
            True si la descarga fue exitosa
        """
        if model_id not in self.AVAILABLE_MODELS:
            logger.error(f"Modelo desconocido: {model_id}")
            return False

        model_info = self.AVAILABLE_MODELS[model_id]
        model_name = model_info["name"]

        try:
            logger.info(f"📥 Descargando modelo {model_id} ({model_info['size_mb']}MB)...")

            if progress_callback:
                progress_callback("Iniciando descarga...", 0)

            start_time = time.time()

            # Descargar usando transformers (que maneja caché automáticamente)
            pipeline(
                "automatic-speech-recognition",
                model=model_name,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )

            download_time = time.time() - start_time

            if progress_callback:
                progress_callback("Descarga completada", 100)

            # Actualizar configuración
            if model_id not in self.config.get("downloaded_models", []):
                self.config.setdefault("downloaded_models", []).append(model_id)
                self._save_config()

            logger.info(f"✅ Modelo {model_id} descargado en {download_time:.1f}s")
            return True

        except Exception as e:
            logger.error(f"❌ Error descargando modelo {model_id}: {e}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}", -1)
            return False

    def load_model(self, model_id: str, language: str = "spanish") -> bool:
        """
        Cargar un modelo específico.

        Args:
            model_id: ID del modelo a cargar
            language: Idioma de transcripción

        Returns:
            True si la carga fue exitosa
        """
        if model_id not in self.AVAILABLE_MODELS:
            logger.error(f"Modelo desconocido: {model_id}")
            return False

        model_info = self.AVAILABLE_MODELS[model_id]
        model_name = model_info["name"]

        try:
            logger.info(f"🔄 Cargando modelo {model_id}...")
            start_time = time.time()

            # Liberar modelo anterior
            if self.current_pipeline:
                del self.current_pipeline
                if self.device == "cuda":
                    try:
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                    except Exception:
                        pass

            # Cargar nuevo modelo
            self.current_pipeline = pipeline(
                "automatic-speech-recognition",
                model=model_name,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                model_kwargs={"attn_implementation": "eager"}
            )

            # Configurar idioma
            self.language_kwargs = {}
            if language != "auto":
                lang_map = {
                    "spanish": "es",
                    "english": "en"
                }
                lang_code = lang_map.get(language, "es")
                self.language_kwargs = {"language": lang_code}

            # Warmup
            self._warmup_model()

            load_time = time.time() - start_time

            # Actualizar estado
            self.current_model = model_id
            self.config["current_model"] = model_id
            self._save_config()

            logger.info(f"✅ Modelo {model_id} cargado en {load_time:.1f}s")
            return True

        except Exception as e:
            logger.error(f"❌ Error cargando modelo {model_id}: {e}")
            return False

    def _warmup_model(self):
        """Calentar modelo con audio sintético."""
        if not self.current_pipeline:
            return

        try:
            import numpy as np
            synthetic_audio = np.random.randn(8000).astype(np.float32)  # 0.5s
            _ = self.current_pipeline(
                {"array": synthetic_audio, "sampling_rate": 16000},
                generate_kwargs={"max_new_tokens": 10, **self.language_kwargs}
            )
            logger.debug("🔥 Modelo calentado")
        except Exception as e:
            logger.warning(f"Error en warmup: {e}")

    def transcribe(self, audio_data, sample_rate: int = 16000) -> dict:
        """
        Transcribir audio con el modelo actual.

        Args:
            audio_data: Datos de audio
            sample_rate: Frecuencia de muestreo

        Returns:
            Resultado de transcripción
        """
        if not self.current_pipeline:
            raise ValueError("Ningún modelo cargado")

        try:
            start_time = time.time()

            # Configurar opciones según el modelo
            model_size = self.current_model
            if model_size in ["tiny", "base"]:
                max_tokens = 128
                num_beams = 1
            elif model_size == "small":
                max_tokens = 256
                num_beams = 1
            elif model_size == "medium":
                max_tokens = 300  # Reducido para evitar límite de 448
                num_beams = 1
            else:  # large
                max_tokens = 400
                num_beams = 1  # Solo beam search para velocidad

            generate_kwargs = {
                "max_new_tokens": max_tokens,
                "num_beams": num_beams,
                "do_sample": False,
                **self.language_kwargs
            }

            result = self.current_pipeline(
                {"array": audio_data, "sampling_rate": sample_rate},
                generate_kwargs=generate_kwargs,
                return_timestamps=False
            )

            processing_time = time.time() - start_time
            text = result.get("text", "").strip()

            return {
                "text": text,
                "processing_time": processing_time,
                "model": self.current_model,
                "model_size": self.AVAILABLE_MODELS[self.current_model]["size_mb"]
            }

        except Exception as e:
            logger.error(f"Error en transcripción: {e}")
            return {
                "text": "",
                "processing_time": 0.0,
                "error": str(e)
            }

    def get_current_model_info(self) -> dict:
        """Obtener información del modelo actual."""
        if not self.current_model:
            return {"error": "Ningún modelo cargado"}

        model_info = self.AVAILABLE_MODELS[self.current_model].copy()
        model_info["model_id"] = self.current_model
        model_info["device"] = self.device
        model_info["loaded"] = self.current_pipeline is not None

        return model_info

    def delete_model(self, model_id: str) -> bool:
        """
        Eliminar un modelo descargado (liberar espacio).

        Args:
            model_id: ID del modelo a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        try:
            if model_id == self.current_model:
                logger.warning(f"No se puede eliminar el modelo actual: {model_id}")
                return False

            # Eliminar de la lista de descargados
            if model_id in self.config.get("downloaded_models", []):
                self.config["downloaded_models"].remove(model_id)
                self._save_config()

            # Nota: Los modelos de transformers se guardan en caché de huggingface
            # Para liberar espacio realmente, el usuario debería limpiar ~/.cache/huggingface

            logger.info(f"🗑️ Modelo {model_id} marcado para eliminación")
            return True

        except Exception as e:
            logger.error(f"Error eliminando modelo {model_id}: {e}")
            return False


def test_model_manager():
    """Test del gestor de modelos."""
    print("🧪 Probando Model Manager...")

    manager = ModelManager()

    # Mostrar modelos disponibles
    print("\n📋 Modelos disponibles:")
    models = manager.get_available_models()
    for model_id, info in models.items():
        status = "✅ Descargado" if info["downloaded"] else "📥 No descargado"
        current = " (ACTUAL)" if info["is_current"] else ""
        print(f"  {model_id}: {info['description']} - {info['size_mb']}MB {status}{current}")

    # Cargar modelo tiny (más rápido para testing)
    print("\n🔄 Cargando modelo tiny...")
    success = manager.load_model("tiny", "spanish")
    if success:
        print("✅ Modelo cargado exitosamente")

        # Probar transcripción
        import numpy as np
        test_audio = np.random.randn(16000).astype(np.float32)
        result = manager.transcribe(test_audio)
        print(f"📝 Test transcripción: {result}")
    else:
        print("❌ Error cargando modelo")

    print("✅ Test completado")


if __name__ == "__main__":
    test_model_manager()
