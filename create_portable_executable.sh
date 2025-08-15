#!/bin/bash
# Audio Transcribe - Crear ejecutable portable

set -e

echo "📦 Creando ejecutable portable de Audio Transcribe..."
echo "=================================================="

# Crear directorio de distribución
DIST_DIR="dist"
PORTABLE_DIR="$DIST_DIR/AudioTranscribe-Portable"
rm -rf "$PORTABLE_DIR"
mkdir -p "$PORTABLE_DIR"

echo "📁 Copiando archivos del proyecto..."

# Copiar archivos esenciales
cp -r backend/ "$PORTABLE_DIR/"
cp -r frontend/ "$PORTABLE_DIR/"
cp pyproject.toml "$PORTABLE_DIR/"
cp README.md "$PORTABLE_DIR/"
cp CLAUDE.md "$PORTABLE_DIR/"
cp start_app.py "$PORTABLE_DIR/"
cp unix_installer.sh "$PORTABLE_DIR/"

# Crear script ejecutable principal
echo "🔧 Creando script ejecutable..."
cat > "$PORTABLE_DIR/audio-transcribe" << 'MAIN_SCRIPT'
#!/bin/bash
# Audio Transcribe - Script ejecutable principal

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎵 Audio Transcribe v1.0.0"
echo "=========================="

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SYSTEM="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    SYSTEM="macOS"
else
    echo "❌ Sistema operativo no soportado: $OSTYPE"
    exit 1
fi

echo "🖥️ Sistema detectado: $SYSTEM"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado"
    echo ""
    echo "Por favor instala Python 3.8+ primero:"
    if [ "$SYSTEM" = "Linux" ]; then
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "  Arch: sudo pacman -S python python-pip"
    else
        echo "  macOS: brew install python"
        echo "  O descarga desde: https://python.org/downloads/"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION encontrado"

# Verificar/instalar UV
if ! command -v uv &> /dev/null; then
    echo "📦 Instalando UV (gestor de paquetes Python)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.local/bin/env 2>/dev/null || source ~/.cargo/env 2>/dev/null || true
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv &> /dev/null; then
    echo "❌ Error instalando UV"
    echo "Por favor instala manualmente: https://docs.astral.sh/uv/"
    exit 1
fi

echo "✅ UV encontrado: $(uv --version)"

# Instalar dependencias
echo "📦 Instalando dependencias..."
uv sync

# Verificar dependencias del sistema
echo "🔧 Verificando dependencias del sistema..."
if [ "$SYSTEM" = "Linux" ]; then
    # Verificar si existen las librerías necesarias
    if ! ldconfig -p | grep -q libportaudio; then
        echo "⚠️ PortAudio no encontrado. Instalando..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y portaudio19-dev
        elif command -v yum &> /dev/null; then
            sudo yum install -y portaudio-devel
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm portaudio
        else
            echo "❌ No se pudo instalar PortAudio automáticamente"
            echo "Por favor instala portaudio manualmente"
        fi
    fi
elif [ "$SYSTEM" = "macOS" ]; then
    if ! brew list portaudio &> /dev/null; then
        if command -v brew &> /dev/null; then
            echo "📦 Instalando PortAudio con Homebrew..."
            brew install portaudio
        else
            echo "⚠️ Homebrew no encontrado. Instala PortAudio manualmente"
        fi
    fi
fi

echo ""
echo "🚀 Iniciando Audio Transcribe..."
echo "================================"
echo ""
echo "📱 Interfaz web: http://localhost:3000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "⚠️ NO CIERRES esta terminal mientras uses la aplicación"
echo "📝 Presiona Ctrl+C para detener"
echo ""

# Función para abrir navegador
open_browser() {
    sleep 3
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:3000" &
    elif command -v open &> /dev/null; then
        open "http://localhost:3000" &
    fi
}

# Abrir navegador en segundo plano
open_browser &

# Ejecutar la aplicación
python3 start_app.py
MAIN_SCRIPT

chmod +x "$PORTABLE_DIR/audio-transcribe"

# Crear instalador rápido
echo "📦 Creando instalador rápido..."
cat > "$PORTABLE_DIR/install.sh" << 'INSTALL_SCRIPT'
#!/bin/bash
# Audio Transcribe - Instalador rápido

echo "🎵 Audio Transcribe - Instalador rápido"
echo "======================================"

INSTALL_DIR="$HOME/.local/share/audio-transcribe"
BIN_DIR="$HOME/.local/bin"

echo "📁 Creando directorios de instalación..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

echo "📦 Copiando archivos..."
cp -r * "$INSTALL_DIR/"

echo "🔗 Creando enlace ejecutable..."
ln -sf "$INSTALL_DIR/audio-transcribe" "$BIN_DIR/audio-transcribe"

# Asegurar que ~/.local/bin está en PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo "📝 Agregando ~/.local/bin al PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
fi

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "🚀 Para ejecutar Audio Transcribe:"
echo "   audio-transcribe"
echo ""
echo "💡 Si el comando no funciona, reinicia tu terminal o ejecuta:"
echo "   source ~/.bashrc"
echo ""
INSTALL_SCRIPT

chmod +x "$PORTABLE_DIR/install.sh"

# Crear README para el portable
cat > "$PORTABLE_DIR/README-PORTABLE.md" << 'PORTABLE_README'
# Audio Transcribe - Versión Portable

## 🚀 Ejecución Rápida

### Opción 1: Ejecución Directa
```bash
./audio-transcribe
```

### Opción 2: Instalación en el Sistema
```bash
./install.sh
```
Después ejecuta desde cualquier lugar:
```bash
audio-transcribe
```

## 📋 Requisitos del Sistema

- **Linux**: Ubuntu 18.04+, CentOS 7+, o equivalente
- **macOS**: macOS 10.15+
- **Python**: 3.8 o superior
- **Espacio**: ~100MB

## 🔧 Dependencias

El script instalará automáticamente:
- UV (gestor de paquetes Python)
- PortAudio (biblioteca de audio)
- Dependencias Python necesarias

## 🌐 Acceso

Después de ejecutar:
- **Interfaz principal**: http://localhost:3000
- **Documentación API**: http://localhost:8000/docs

## 🛟 Solución de Problemas

### Error de permisos:
```bash
chmod +x audio-transcribe install.sh
```

### Python no encontrado:
- **Ubuntu/Debian**: `sudo apt install python3`
- **macOS**: `brew install python` o descargar de python.org

### Error de audio en Linux:
```bash
sudo apt install portaudio19-dev pulseaudio-utils
```

## 📞 Soporte

Para problemas o preguntas:
- **Issues**: https://github.com/JahazielHernandezHoyos/audio-transcribe/issues
- **Documentación**: README.md en este directorio
PORTABLE_README

# Crear archivo de información
cat > "$PORTABLE_DIR/VERSION.txt" << VERSION_INFO
Audio Transcribe v1.0.0
Versión Portable para Linux/macOS

Fecha de compilación: $(date)
Arquitectura: Multiplataforma (Python)
Sistema: Linux/macOS

Incluye:
- Código fuente completo
- Script ejecutable principal
- Instalador automático
- Documentación
VERSION_INFO

echo "📦 Creando archivo comprimido..."
cd "$DIST_DIR"
tar -czf "AudioTranscribe-Portable-$(date +%Y%m%d).tar.gz" "AudioTranscribe-Portable"
cd ..

echo ""
echo "✅ Ejecutable portable creado exitosamente!"
echo ""
echo "📁 Archivos generados:"
echo "   • $PORTABLE_DIR/ (directorio portable)"
echo "   • $DIST_DIR/AudioTranscribe-Portable-$(date +%Y%m%d).tar.gz (archivo comprimido)"
echo ""
echo "🚀 Para usar el portable:"
echo "   1. Extrae el archivo .tar.gz"
echo "   2. Ejecuta: ./audio-transcribe"
echo "   3. O instala: ./install.sh"
echo ""
echo "📋 Listo para subir al release de GitHub!"