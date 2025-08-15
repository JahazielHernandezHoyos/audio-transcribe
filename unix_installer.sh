#!/bin/bash
# Audio Transcribe - Unix One-Click Installer & Runner
# This script installs and runs Audio Transcribe on Unix systems

set -e

INSTALL_DIR="$HOME/.local/share/audio-transcribe"
CONFIG_DIR="$HOME/.config/audio-transcribe"

echo "🎵 Audio Transcribe - Unix Installer"
echo "=================================="

# Detect system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SYSTEM="linux"
    echo "🐧 Detected: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    SYSTEM="macos"
    echo "🍎 Detected: macOS"
else
    echo "❌ Unsupported system: $OSTYPE"
    echo "This installer supports Linux and macOS only"
    exit 1
fi

# Check if already installed
if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/run.sh" ]; then
    echo "✅ Audio Transcribe is already installed"
    echo "🚀 Running existing installation..."
    cd "$INSTALL_DIR"
    exec ./run.sh
fi

echo "📦 Installing Audio Transcribe..."

# Check dependencies
echo "🔍 Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    echo ""
    echo "Please install Python 3.12+ first:"
    if [ "$SYSTEM" = "linux" ]; then
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

# Install system dependencies
echo "🔧 Installing system dependencies..."
if [ "$SYSTEM" = "linux" ]; then
    if command -v apt-get &> /dev/null; then
        echo "📦 Installing Ubuntu/Debian dependencies..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-dev portaudio19-dev pulseaudio-utils curl
    elif command -v yum &> /dev/null; then
        echo "📦 Installing CentOS/RHEL dependencies..."
        sudo yum install -y python3-devel portaudio-devel pulseaudio-utils curl
    elif command -v pacman &> /dev/null; then
        echo "📦 Installing Arch dependencies..."
        sudo pacman -S --noconfirm python portaudio pulseaudio curl
    else
        echo "⚠️ Unknown Linux distribution"
        echo "Please install manually: python3-dev, portaudio-dev, pulseaudio"
    fi
elif [ "$SYSTEM" = "macos" ]; then
    if command -v brew &> /dev/null; then
        echo "📦 Installing macOS dependencies..."
        brew install portaudio
    else
        echo "⚠️ Homebrew not found"
        echo "Please install Homebrew: https://brew.sh"
        echo "Then run: brew install portaudio"
    fi
fi

# Install UV
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.local/bin/env 2>/dev/null || source ~/.cargo/env 2>/dev/null || true
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv &> /dev/null; then
    echo "❌ Failed to install UV"
    echo "Please install manually: https://docs.astral.sh/uv/"
    exit 1
fi

echo "✅ UV found: $(uv --version)"

# Create installation directory
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"

# Download source code
echo "📥 Downloading Audio Transcribe..."
cd "$INSTALL_DIR"

# If we have the portable distribution locally, use it
if [ -f "$(dirname "$0")/dist/audio-transcribe-portable-*.tar.gz" ]; then
    echo "📦 Using local portable distribution..."
    tar -xzf "$(dirname "$0")/dist/audio-transcribe-portable-"*.tar.gz --strip-components=1
else
    # Create minimal source structure
    echo "📝 Creating source structure..."
    mkdir -p backend frontend
    
    # Create backend files (simplified versions)
    cat > backend/main.py << 'PYTHON_MAIN'
"""
Audio Transcribe - Simplified Backend
"""
import asyncio
import logging
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import threading
import queue
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Audio Transcribe", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
app_state = {
    "is_capturing": False,
    "connected_clients": set(),
    "transcription_queue": queue.Queue(),
}

@app.get("/")
async def root():
    return {"message": "Audio Transcribe API", "version": "1.0.0"}

@app.get("/status")
async def get_status():
    return {
        "is_capturing": app_state["is_capturing"],
        "connected_clients": len(app_state["connected_clients"]),
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app_state["connected_clients"].add(websocket)
    logger.info(f"Client connected. Total: {len(app_state['connected_clients'])}")
    
    try:
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received: {message}")
            await websocket.send_text('{"type": "status", "message": "Connected"}')
    except WebSocketDisconnect:
        app_state["connected_clients"].discard(websocket)
        logger.info(f"Client disconnected. Total: {len(app_state['connected_clients'])}")

# Serve frontend
@app.get("/app")
async def serve_frontend():
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"error": "Frontend not found"}

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    run_server()
PYTHON_MAIN

    # Create frontend
    cat > frontend/index.html << 'HTML_FRONTEND'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Transcribe - Unix</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 { text-align: center; margin-bottom: 30px; }
        .status { 
            text-align: center; 
            margin: 20px 0;
            font-size: 18px;
        }
        .button {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            color: white;
            font-size: 16px;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s;
        }
        .button:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        .info {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Audio Transcribe</h1>
        <div class="status" id="status">Connecting...</div>
        
        <div style="text-align: center;">
            <button class="button" onclick="connectWebSocket()">Connect</button>
            <button class="button" onclick="openAPI()">View API</button>
        </div>
        
        <div class="info">
            <h3>🚀 Getting Started</h3>
            <p>This is a simplified version of Audio Transcribe running on Unix.</p>
            <p><strong>Next steps:</strong></p>
            <ul>
                <li>The full transcription features are available in the complete version</li>
                <li>This demonstrates the basic web interface and API connectivity</li>
                <li>API documentation: <a href="http://localhost:8000/docs" target="_blank" style="color: lightblue;">http://localhost:8000/docs</a></li>
            </ul>
        </div>
        
        <div class="info">
            <h3>🔧 System Information</h3>
            <p>Platform: Unix/Linux</p>
            <p>Backend: Python FastAPI</p>
            <p>Frontend: HTML5/JavaScript</p>
        </div>
    </div>

    <script>
        let ws = null;
        
        function connectWebSocket() {
            if (ws) {
                ws.close();
            }
            
            ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.onopen = function() {
                document.getElementById('status').textContent = 'Connected to Audio Transcribe API ✅';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                console.log('Received:', data);
            };
            
            ws.onclose = function() {
                document.getElementById('status').textContent = 'Disconnected ❌';
            };
            
            ws.onerror = function() {
                document.getElementById('status').textContent = 'Connection Error ❌';
            };
        }
        
        function openAPI() {
            window.open('http://localhost:8000/docs', '_blank');
        }
        
        // Auto-connect on load
        setTimeout(connectWebSocket, 1000);
    </script>
</body>
</html>
HTML_FRONTEND

    # Create pyproject.toml
    cat > pyproject.toml << 'TOML_PROJECT'
[project]
name = "audio-transcribe"
version = "0.1.0"
description = "Real-time audio transcription"
requires-python = ">=3.8"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0",
    "websockets>=11.0",
]
TOML_PROJECT
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv sync

# Create run script
cat > run.sh << 'RUN_SCRIPT'
#!/bin/bash
# Audio Transcribe - Unix Runner

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎵 Audio Transcribe - Starting..."
echo "==============================="

# Check if UV is available
if ! command -v uv &> /dev/null; then
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Please run the installer again."
    exit 1
fi

# Start backend
echo "🚀 Starting backend server..."
echo "📍 API will be available at: http://localhost:8000"
echo "🌐 Web interface at: http://localhost:8000/app"
echo "📚 API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

# Try to open browser
if command -v xdg-open &> /dev/null; then
    sleep 2 && xdg-open "http://localhost:8000/app" &
elif command -v open &> /dev/null; then
    sleep 2 && open "http://localhost:8000/app" &
fi

# Run the application
uv run python backend/main.py
RUN_SCRIPT

chmod +x run.sh

# Create desktop shortcut for Linux
if [ "$SYSTEM" = "linux" ] && [ -d "$HOME/.local/share/applications" ]; then
    cat > "$HOME/.local/share/applications/audio-transcribe.desktop" << DESKTOP_ENTRY
[Desktop Entry]
Name=Audio Transcribe
Comment=Real-time audio transcription
Exec=$INSTALL_DIR/run.sh
Icon=applications-multimedia
Terminal=false
Type=Application
Categories=AudioVideo;Audio;
DESKTOP_ENTRY
    echo "✅ Desktop shortcut created"
fi

# Create system command
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/audio-transcribe" << SYS_COMMAND
#!/bin/bash
cd "$INSTALL_DIR"
exec ./run.sh
SYS_COMMAND
chmod +x "$HOME/.local/bin/audio-transcribe"

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🚀 To run Audio Transcribe:"
echo "   audio-transcribe"
echo ""
echo "   Or directly:"
echo "   $INSTALL_DIR/run.sh"
echo ""
echo "📁 Installed to: $INSTALL_DIR"
echo ""

# Ask to run now
read -p "🎵 Run Audio Transcribe now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting Audio Transcribe..."
    exec ./run.sh
fi

echo "👋 Done! Run 'audio-transcribe' anytime to start."