# 🪟 Audio Transcribe - Configuración para Windows

## Instalación Rápida

### 1. Requisitos Previos
- **Python 3.12+** desde [python.org](https://python.org/downloads/)
  - ⚠️ **Importante**: Marca "Add Python to PATH" durante la instalación

### 2. Instalación Automática
```cmd
# Ejecutar el instalador automático
install_windows.bat
```

El script instalará automáticamente:
- UV (gestor de dependencias)
- PyAudioWPatch (captura de audio WASAPI)
- Todas las dependencias Python necesarias

### 3. Ejecutar la Aplicación
```cmd
python start_app.py
```

## Configuración Manual (Avanzada)

Si prefieres instalar manualmente:

### 1. Instalar UV
```powershell
# En PowerShell como Administrador
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. Instalar Dependencias
```cmd
cd audio-transcribe
uv sync
uv add "PyAudioWPatch>=0.2.12.5"
```

### 3. Ejecutar
```cmd
python start_app.py
```

## Captura de Audio en Windows

### Micrófono (Predeterminado)
- La aplicación capturará del micrófono por defecto
- Windows puede solicitar permisos, permitir acceso

### Audio del Sistema (Avanzado)
Para capturar audio que se reproduce en el sistema:

1. **Habilitar Stereo Mix**:
   - Panel de Control → Sonido → Grabación
   - Clic derecho → "Mostrar dispositivos desconectados"
   - Habilitar "Stereo Mix" o "Mezcla estéreo"

2. **Usar VB-Audio Cable** (Recomendado):
   - Descargar [VB-Audio Cable](https://vb-audio.com/Cable/)
   - Configurar como dispositivo de salida predeterminado
   - La aplicación lo detectará automáticamente

## Solución de Problemas

### Error: "PyAudioWPatch no está instalado"
```cmd
# Solución:
uv add PyAudioWPatch
# o
pip install PyAudioWPatch
```

### Error: "uv no se reconoce como comando"
```cmd
# Solución 1: Reiniciar terminal/PowerShell
# Solución 2: Instalar UV manualmente
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

### Crash de PyTorch/CUDA
- ✅ **Ya resuelto**: La aplicación fuerza modo CPU automáticamente
- Si quieres usar GPU: `set ENABLE_CUDA=1` antes de ejecutar

### Audio no se detecta
1. Verificar que el micrófono funciona en otras aplicaciones
2. Verificar permisos de micrófono en Windows 11:
   - Configuración → Privacidad → Micrófono
   - Permitir aplicaciones de escritorio
3. Probar con diferentes dispositivos de audio

### Puerto ocupado
```cmd
# Si el puerto 8000 está ocupado:
netstat -ano | findstr :8000
# Matar proceso:
taskkill /PID <PID> /F
```

## Características Específicas de Windows

### ✅ Soporte WASAPI
- Captura de alta calidad con baja latencia
- Detección automática de dispositivos loopback
- Compatible con Windows 10/11

### ✅ Detección Automática
- Búsqueda inteligente de dispositivos de audio
- Fallback graceful al micrófono por defecto
- Logs detallados para debugging

### ✅ Manejo de Errores Robusto
- Mensajes de error específicos para Windows
- Instrucciones de instalación automáticas
- Recuperación de errores de configuración

## Acceso a la Aplicación

Una vez ejecutada la aplicación:
- 🌐 **Interfaz Web**: http://localhost:3000
- 🔧 **API**: http://localhost:8000/docs
- 📱 **Se abre automáticamente** en el navegador

## Rendimiento en Windows

### CPU vs GPU
- **CPU (predeterminado)**: Funciona en cualquier PC, modelo Whisper-tiny
- **GPU**: Para habilitar `set ENABLE_CUDA=1` (requiere NVIDIA GPU + CUDA)

### Optimizaciones
- Modelo Whisper-tiny: ~40MB, rápido para tiempo real
- Chunks de 3 segundos con overlap de 0.5s
- Detección de actividad de voz para evitar transcripciones falsas

## Integración con Windows

### Scripts Batch
- `install_windows.bat`: Instalación completa automática
- `start_app.py`: Inicio con detección de plataforma

### Rutas Windows
- Soporte para rutas con espacios
- Manejo correcto de `uv.exe` vs `uv`
- Restauración de directorio de trabajo

¿Problemas? Abre un issue con detalles de tu configuración de Windows.
