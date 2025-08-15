# 🎵 Audio Transcribe

> **Real-time audio transcription powered by OpenAI Whisper**

[![Platform](https://img.shields.io/badge/platform-Windows%20|%20Linux%20|%20macOS-blue)](#installation)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Tauri](https://img.shields.io/badge/tauri-2.0-orange.svg)](https://tauri.app)

A cross-platform desktop application that provides real-time audio transcription using OpenAI's Whisper model. Capture audio from your microphone or system and see instant, accurate transcriptions in a beautiful, modern interface.

## ✨ Features

- 🎙️ **Real-time transcription** - Live audio to text conversion with <3 second latency
- 🖥️ **Cross-platform** - Native desktop apps for Windows, Linux, and macOS
- 🧠 **AI-powered** - Uses OpenAI's Whisper "tiny" model (~39MB) for optimal speed/accuracy
- 🔊 **Flexible audio input** - Microphone, system audio, or loopback capture
- 🌐 **Modern web interface** - Clean, responsive UI with real-time updates
- ⚡ **High performance** - Optimized for real-time processing with minimal resource usage
- 🎯 **Voice Activity Detection** - Intelligent filtering of silence and noise
- 🌍 **Multi-language support** - Supports multiple languages including English and Spanish
- 🔌 **WebSocket real-time** - Instant transcription updates via WebSocket connection
- 📱 **Progressive Web App** - Works as both desktop and web application

## 🚀 Quick Start

### One-Click Installation

#### Windows
```cmd
# Download and run the installer
curl -O https://github.com/JahazielHernandezHoyos/audio-transcribe/releases/latest/download/audio-transcribe-windows.exe
audio-transcribe-windows.exe
```

#### Linux/macOS (One Command)
```bash
curl -sSL https://raw.githubusercontent.com/JahazielHernandezHoyos/audio-transcribe/main/unix_installer.sh | bash
```

#### Alternative: Portable Version
```bash
# Download portable version
wget https://github.com/JahazielHernandezHoyos/audio-transcribe/releases/latest/download/audio-transcribe-portable.tar.gz
tar -xzf audio-transcribe-portable.tar.gz
cd audio-transcribe-portable
./quick_install.sh && ./run_portable.sh
```

## 🏗️ Architecture

Audio Transcribe combines multiple technologies for optimal performance:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │   ML Model      │
│                 │    │                  │    │                 │
│ HTML/CSS/JS     │◄──►│ Python FastAPI   │◄──►│ Whisper Tiny    │
│ WebSocket       │    │ WebSocket        │    │ (~39MB)         │
│ Real-time UI    │    │ Audio Capture    │    │ Local Inference │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │   Audio System   │
                       │                  │
                       │ PyAudioWPatch    │
                       │ sounddevice      │
                       │ Platform APIs    │
                       └──────────────────┘
```

### Key Components

- **Frontend**: HTML5/CSS3/JavaScript web interface with WebSocket real-time communication
- **Backend**: Python FastAPI server with WebSocket support for real-time transcription
- **Desktop Wrapper**: Tauri (Rust + HTML) for native desktop distribution
- **ML Engine**: OpenAI Whisper "tiny" model for fast, accurate transcription
- **Audio Capture**: Platform-specific audio APIs (WASAPI/ALSA/CoreAudio)

## 📱 Screenshots

### Main Interface
![Main Interface](docs/images/main-interface.png)
*Clean, modern interface with real-time transcription display*

### Settings & Configuration
![Settings](docs/images/settings.png)
*Easy device selection and model configuration*

### Real-time Transcription
![Real-time](docs/images/realtime-demo.gif)
*Live transcription in action*

## 🛠️ Development

### Manual Installation

<details>
<summary>Click to expand manual installation instructions</summary>

#### Prerequisites
- Python 3.8+ 
- Node.js 18+ (for Tauri builds)
- Rust (for Tauri builds)
- Audio system (ALSA/PulseAudio on Linux, CoreAudio on macOS, WASAPI on Windows)

#### From Source
```bash
# Clone the repository
git clone https://github.com/JahazielHernandezHoyos/audio-transcribe.git
cd audio-transcribe

# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the application
python start_app.py
```

#### Build Desktop App
```bash
# Install Node dependencies
npm install

# Build for your platform
npm run tauri:build

# Run in development
npm run tauri:dev
```

</details>

### Project Structure

```
audio-transcribe/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Main API server
│   ├── audio_capture.py    # Cross-platform audio capture
│   ├── transcription.py    # Whisper integration
│   └── model_manager.py    # Model loading and management
├── frontend/               # Web interface
│   └── index.html         # Single-page application
├── src-tauri/             # Tauri desktop wrapper
│   ├── src/
│   │   └── main.rs        # Rust application entry point
│   ├── Cargo.toml         # Rust dependencies
│   └── tauri.conf.json    # Tauri configuration
├── dist/                  # Distribution files
├── scripts/               # Build and deployment scripts
└── docs/                  # Documentation and assets
```

### Development Commands

```bash
# Backend development
uv run python backend/main.py --reload

# Frontend development (auto-served by backend)
python start_app.py

# Desktop app development
npm run tauri:dev

# Build for production
npm run tauri:build

# Run tests
python test_mvp.py
python test_websocket.py
```

## 🎯 Technical Details

### Audio Processing
- **Sample Rate**: 16000 Hz (Whisper requirement)
- **Chunk Duration**: 3 seconds with 0.5s overlap
- **Voice Activity Detection**: Filters silence automatically
- **Platform Support**: Windows (WASAPI), Linux (ALSA/PulseAudio), macOS (CoreAudio)

### Machine Learning
- **Model**: OpenAI Whisper "tiny" (39MB)
- **Inference**: CPU-optimized for real-time performance
- **Languages**: Multi-language support (English, Spanish, and more)
- **Accuracy**: Balanced for real-time use cases

### Performance
- **Latency**: <3 seconds end-to-end
- **Memory Usage**: ~300MB with model loaded
- **CPU Usage**: Moderate (optimized for real-time)
- **Throughput**: ~10x real-time processing speed

## 🌐 API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and status |
| `/status` | GET | System status and statistics |
| `/start_capture` | POST | Start audio capture |
| `/stop_capture` | POST | Stop audio capture |
| `/audio/devices` | GET | List available audio devices |
| `/models` | GET | Available Whisper models |
| `/models/{model_id}/load` | POST | Load specific model |

### WebSocket API

Connect to `ws://localhost:8000/ws` for real-time transcription updates.

**Message Format:**
```json
{
  "type": "transcription",
  "data": {
    "text": "Transcribed text",
    "confidence": 0.95,
    "processing_time": 0.3,
    "timestamp": 1234567890
  }
}
```

## 🛟 Troubleshooting

### Common Issues

**Audio not detected:**
```bash
# Check audio devices
curl http://localhost:8000/audio/devices

# Linux: Check PulseAudio
pulseaudio --check -v

# macOS: Check permissions
# System Preferences → Security & Privacy → Microphone
```

**Model loading fails:**
```bash
# Check internet connection and disk space
# Models are downloaded to ./models/ directory
# Ensure ~100MB free space
```

### Platform-Specific

#### Windows
- Enable microphone permissions in Windows Settings
- For system audio: Enable "Stereo Mix" or use VB-Audio Cable
- Install Visual C++ Redistributable if needed

#### Linux
- Install: `sudo apt install python3-dev portaudio19-dev pulseaudio`
- For system audio: Configure PulseAudio monitor
- Check ALSA devices: `arecord -l`

#### macOS
- Grant microphone permissions in System Preferences
- Install via Homebrew: `brew install python portaudio`
- For system audio: Use Aggregate Audio Device

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Amazing speech recognition model
- [Tauri](https://tauri.app) - Modern desktop application framework
- [FastAPI](https://fastapi.tiangolo.com) - High-performance Python web framework
- [UV](https://docs.astral.sh/uv/) - Ultra-fast Python package manager

---

<div align="center">

**Made with ❤️ by [Jahaziel Hernández](https://github.com/JahazielHernandezHoyos)**

[⭐ Star this project](https://github.com/JahazielHernandezHoyos/audio-transcribe) • [📥 Download](https://github.com/JahazielHernandezHoyos/audio-transcribe/releases) • [📖 Docs](https://JahazielHernandezHoyos.github.io/audio-transcribe)

</div>