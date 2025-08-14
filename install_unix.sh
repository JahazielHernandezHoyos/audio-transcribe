#!/bin/bash
# Audio Transcribe - Instalador para Linux/macOS
# Instala dependencias y configura el entorno

set -e

echo
echo "🎵 Audio Transcribe - Instalador para Linux/macOS"
echo "================================================"
echo

# Detectar OS
OS=$(uname -s)
echo "🖥️  Sistema operativo: $OS"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    echo "💡 Instala Python 3:"
    if [[ "$OS" == "Darwin" ]]; then
        echo "   brew install python3"
        echo "   O descarga desde: https://python.org/downloads/"
    else
        echo "   Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "   Fedora/RHEL: sudo dnf install python3 python3-pip" 
        echo "   Arch: sudo pacman -S python python-pip"
    fi
    exit 1
fi

echo "✅ Python detectado:"
python3 --version

# Verificar UV
if ! command -v uv &> /dev/null; then
    echo
    echo "📦 UV no está instalado, instalando..."
    echo "💡 Instalando UV (gestor de dependencias)..."
    
    # Instalar UV
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Cargar UV en PATH
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Verificar instalación
    if ! command -v uv &> /dev/null; then
        echo "❌ Error instalando UV"
        echo "💡 Instala manualmente desde: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
fi

echo "✅ UV detectado:"
uv --version

# Instalar dependencias del sistema según la plataforma
echo
echo "🔧 Verificando dependencias del sistema..."

if [[ "$OS" == "Linux" ]]; then
    echo "🐧 Linux detectado - verificando dependencias de audio..."
    
    # Verificar si sounddevice puede funcionar
    if ! python3 -c "import sounddevice" 2>/dev/null; then
        echo "⚠️  Pueden faltar dependencias de audio del sistema"
        echo "💡 Si tienes problemas, instala:"
        echo "   Ubuntu/Debian: sudo apt install portaudio19-dev python3-pyaudio"
        echo "   Fedora/RHEL: sudo dnf install portaudio-devel"
        echo "   Arch: sudo pacman -S portaudio"
    fi
    
elif [[ "$OS" == "Darwin" ]]; then
    echo "🍎 macOS detectado - verificando dependencias de audio..."
    
    # En macOS, generalmente funciona out-of-the-box
    echo "✅ macOS típicamente no requiere dependencias adicionales"
fi

echo
echo "📦 Instalando dependencias Python..."
uv sync

echo
echo "✅ Instalación completada!"
echo
echo "🚀 Para ejecutar la aplicación usa:"
echo "   python3 start_app.py"
echo "   # o"
echo "   uv run python start_app.py"
echo
echo "🌐 La aplicación estará disponible en:"
echo "   http://localhost:3000"
echo
if [[ "$OS" == "Linux" ]]; then
    echo "💡 Consejos para Linux:"
    echo "   • Para capturar audio del sistema, configura un monitor en PulseAudio"
    echo "   • Ejecuta: ./backend/setup_system_audio.py para configuración automática"
    echo "   • Si usas pipewire, asegúrate de que pipewire-pulse esté ejecutándose"
elif [[ "$OS" == "Darwin" ]]; then
    echo "💡 Consejos para macOS:"
    echo "   • Permite el acceso al micrófono en Preferencias del Sistema"
    echo "   • Para capturar audio del sistema, instala Soundflower o BlackHole"
fi
echo
