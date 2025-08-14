"""
Script para configurar captura de audio del sistema en Linux.
Configura PulseAudio para capturar el audio que sale por las bocinas.
"""

import subprocess
import sys
import os
import platform
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_pulseaudio():
    """Verificar si PulseAudio está disponible."""
    try:
        result = subprocess.run(['pulseaudio', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"PulseAudio encontrado: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    logger.error("PulseAudio no está disponible")
    return False

def list_audio_sources():
    """Listar todas las fuentes de audio disponibles."""
    try:
        # Listar sources (input devices)
        result = subprocess.run(['pactl', 'list', 'sources'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Fuentes de audio disponibles:")
            print(result.stdout)
        
        # Listar sinks (output devices)  
        result = subprocess.run(['pactl', 'list', 'sinks'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Dispositivos de salida disponibles:")
            print(result.stdout)
            
    except FileNotFoundError:
        logger.error("pactl no está disponible. Instala pulseaudio-utils")

def create_loopback_module():
    """Crear módulo loopback para capturar audio del sistema."""
    try:
        # Crear loopback: conecta el monitor del sink principal como source
        cmd = [
            'pactl', 'load-module', 'module-loopback',
            'source=@DEFAULT_SINK@.monitor',
            'sink=@DEFAULT_SINK@',
            'latency_msec=20'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            module_id = result.stdout.strip()
            logger.info(f"Módulo loopback creado con ID: {module_id}")
            return module_id
        else:
            logger.error(f"Error creando loopback: {result.stderr}")
            return None
            
    except FileNotFoundError:
        logger.error("pactl no está disponible")
        return None

def remove_loopback_module(module_id):
    """Remover módulo loopback."""
    try:
        cmd = ['pactl', 'unload-module', str(module_id)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Módulo {module_id} removido")
        else:
            logger.error(f"Error removiendo módulo: {result.stderr}")
            
    except FileNotFoundError:
        logger.error("pactl no está disponible")

def get_system_audio_device():
    """
    Obtener el dispositivo para capturar audio del sistema.
    Retorna el nombre del dispositivo monitor del sink principal.
    """
    try:
        # Obtener el sink por defecto
        result = subprocess.run(['pactl', 'get-default-sink'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            default_sink = result.stdout.strip()
            monitor_device = f"{default_sink}.monitor"
            logger.info(f"Dispositivo de captura del sistema: {monitor_device}")
            return monitor_device
        else:
            logger.error("No se pudo obtener el sink por defecto")
            return None
            
    except FileNotFoundError:
        logger.error("pactl no está disponible")
        return None

def test_system_audio_capture():
    """Test para verificar captura de audio del sistema."""
    import sounddevice as sd
    import numpy as np
    import time
    
    # Buscar dispositivo monitor
    devices = sd.query_devices()
    monitor_device = None
    
    for i, device in enumerate(devices):
        if 'monitor' in device['name'].lower() or '.monitor' in device['name'].lower():
            monitor_device = i
            logger.info(f"Dispositivo monitor encontrado: {device['name']}")
            break
    
    if monitor_device is None:
        logger.error("No se encontró dispositivo monitor")
        logger.info("Dispositivos disponibles:")
        print(sd.query_devices())
        return False
    
    # Test de captura
    logger.info("Iniciando test de captura del sistema...")
    logger.info("Reproduce música o video para probar")
    
    def callback(indata, frames, time, status):
        if status:
            print(f"Status: {status}")
        
        # Calcular volumen
        volume = np.sqrt(np.mean(indata**2))
        if volume > 0.001:
            print(f"🔊 Audio del sistema detectado - Volumen: {volume:.4f}")
    
    try:
        with sd.InputStream(
            device=monitor_device,
            samplerate=16000,
            channels=1,
            callback=callback
        ):
            logger.info("Capturando audio del sistema... (Ctrl+C para detener)")
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Test detenido por usuario")
    except Exception as e:
        logger.error(f"Error en test: {e}")
        return False
    
    return True

def setup_system_audio():
    """Configuración completa para captura de audio del sistema."""
    logger.info("🔧 Configurando captura de audio del sistema...")
    
    # Verificar sistema operativo
    if platform.system().lower() != 'linux':
        logger.error("Este script es solo para Linux")
        return False
    
    # Verificar PulseAudio
    if not check_pulseaudio():
        logger.error("PulseAudio es requerido para captura del sistema")
        print("\n💡 Para instalar PulseAudio:")
        print("Ubuntu/Debian: sudo apt install pulseaudio pulseaudio-utils")
        print("Fedora/RHEL: sudo dnf install pulseaudio pulseaudio-utils")
        print("Arch: sudo pacman -S pulseaudio pulseaudio-alsa")
        return False
    
    # Mostrar dispositivos disponibles
    logger.info("\n📋 Listando dispositivos de audio...")
    list_audio_sources()
    
    # Obtener dispositivo del sistema
    system_device = get_system_audio_device()
    if not system_device:
        logger.error("No se pudo configurar dispositivo del sistema")
        return False
    
    print(f"\n✅ Configuración completada")
    print(f"📱 Dispositivo para captura del sistema: {system_device}")
    print("\n🧪 ¿Quieres probar la captura del sistema? (y/n)")
    
    response = input().lower().strip()
    if response == 'y':
        return test_system_audio_capture()
    
    return True

if __name__ == "__main__":
    setup_system_audio()