#!/bin/bash
# Audio Transcribe - Unix Installer
# Simple installer for Linux and macOS

set -e

echo "🎵 Audio Transcribe - Unix Installer"
echo "===================================="

# Detect system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SYSTEM="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    SYSTEM="macOS"
else
    echo "❌ Unsupported system: $OSTYPE"
    echo "This installer supports Linux and macOS only"
    exit 1
fi

echo "🖥️ System detected: $SYSTEM"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    echo ""
    echo "Please install Python 3.8+ first:"
    if [ "$SYSTEM" = "Linux" ]; then
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "  Arch: sudo pacman -S python python-pip"
    else
        echo "  macOS: brew install python"
        echo "  Or download from: https://python.org/downloads/"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Create installation directory
INSTALL_DIR="$HOME/.local/share/audio-transcribe"
echo "📁 Installation directory: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️ Existing installation found. Updating..."
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download source code
echo "📥 Downloading Audio Transcribe from GitHub..."
curl -L "https://github.com/JahazielHernandezHoyos/audio-transcribe/archive/refs/heads/master.zip" -o audio-transcribe.zip

if [ ! -f "audio-transcribe.zip" ]; then
    echo "❌ Error downloading files"
    exit 1
fi

# Extract files
echo "📦 Extracting files..."
if command -v unzip &> /dev/null; then
    unzip -q audio-transcribe.zip
elif command -v python3 &> /dev/null; then
    python3 -c "
import zipfile
with zipfile.ZipFile('audio-transcribe.zip', 'r') as zip_ref:
    zip_ref.extractall('.')
"
else
    echo "❌ No unzip or python found for extraction"
    exit 1
fi

# Move files from subdirectory
if [ -d "audio-transcribe-master" ]; then
    mv audio-transcribe-master/* .
    rmdir audio-transcribe-master
fi
rm audio-transcribe.zip

# Verify files
if [ ! -f "start_app.py" ]; then
    echo "❌ Error: Application files not found"
    exit 1
fi

# Install UV if needed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.local/bin/env 2>/dev/null || source ~/.cargo/env 2>/dev/null || true
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv &> /dev/null; then
    echo "❌ Error installing UV"
    echo "Please install manually: https://docs.astral.sh/uv/"
    exit 1
fi

echo "✅ UV found: $(uv --version)"

# Install system dependencies
echo "🔧 Installing system dependencies..."
if [ "$SYSTEM" = "Linux" ]; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y portaudio19-dev || echo "⚠️ Please install portaudio19-dev manually"
    elif command -v yum &> /dev/null; then
        sudo yum install -y portaudio-devel || echo "⚠️ Please install portaudio-devel manually"
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm portaudio || echo "⚠️ Please install portaudio manually"
    fi
elif [ "$SYSTEM" = "macOS" ]; then
    if command -v brew &> /dev/null; then
        brew install portaudio || echo "⚠️ Please install portaudio manually"
    fi
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv sync

if [ $? -ne 0 ]; then
    echo "❌ Error installing dependencies"
    exit 1
fi

# Create executable command
echo "🔗 Creating system command..."
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/audio-transcribe" << 'EXEC_SCRIPT'
#!/bin/bash
# Audio Transcribe launcher

INSTALL_DIR="$HOME/.local/share/audio-transcribe"
cd "$INSTALL_DIR"

echo "🎵 Audio Transcribe v1.0.0"
echo "=========================="
echo ""
echo "🚀 Starting application..."
echo "📱 Web interface: http://localhost:3000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "⚠️ DO NOT CLOSE this terminal while using the app"
echo "📝 Press Ctrl+C to stop"
echo ""

# Open browser after 3 seconds
(
    sleep 3
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:3000" &
    elif command -v open &> /dev/null; then
        open "http://localhost:3000" &
    fi
) &

# Run the application
python3 start_app.py
EXEC_SCRIPT

chmod +x "$BIN_DIR/audio-transcribe"

# Add to PATH if needed
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo "📝 Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
fi

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🚀 To run Audio Transcribe:"
echo "   audio-transcribe"
echo ""
echo "🌐 The application will open at:"
echo "   http://localhost:3000"
echo ""
echo "💡 If 'audio-transcribe' command doesn't work:"
echo "   1. Restart your terminal, or"
echo "   2. Run: source ~/.bashrc"
echo "   3. Or use: ~/.local/bin/audio-transcribe"
echo ""
echo "🗑️ To uninstall:"
echo "   rm -rf ~/.local/share/audio-transcribe"
echo "   rm ~/.local/bin/audio-transcribe"
echo ""
echo "📞 Support: https://github.com/JahazielHernandezHoyos/audio-transcribe/issues"
echo ""