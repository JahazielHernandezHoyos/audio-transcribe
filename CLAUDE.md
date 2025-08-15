# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Audio Transcribe is a cross-platform real-time audio transcription application that captures audio from system/microphone and transcribes it using OpenAI's Whisper model. The architecture combines:

- **Backend**: Python FastAPI server with WebSocket support for real-time transcription
- **Frontend**: HTML/CSS/JS web interface served via HTTP
- **Desktop App**: Tauri wrapper (Rust + HTML) for native distribution
- **ML Model**: Whisper "tiny" model (~39MB) for optimal speed/accuracy balance
- **Audio Capture**: Platform-specific audio capture (PyAudioWPatch for Windows, sounddevice for Linux/macOS)

## Development Commands

### Python Backend (Primary Development)
```bash
# Install and sync dependencies
uv sync

# Run backend API server
uv run python backend/main.py

# Run complete application (backend + frontend)
python start_app.py

# Run with development mode
uv run python backend/main.py --reload

# Install platform-specific audio dependencies
uv add PyAudioWPatch  # Windows only
```

### Frontend Development
```bash
# Serve frontend (auto-started by start_app.py)
cd frontend && python -m http.server 3000
```

### Tauri Desktop App
```bash
# Install Tauri CLI
npm install

# Build desktop app
npm run tauri build

# Run in development mode  
npm run tauri dev
```

### Platform-Specific Setup

#### Windows
```cmd
# Automated installation
install_windows.bat

# Manual dependency installation
uv add PyAudioWPatch
```

#### Linux/macOS
```bash
# Automated installation
./install_unix.sh

# Setup system audio (Linux)
python backend/setup_system_audio.py
```

## Code Architecture

### Backend Structure (`backend/`)
- `main.py`: FastAPI application with REST endpoints and WebSocket server
- `audio_capture.py`: Cross-platform audio capture abstraction
- `transcription.py`: Whisper model integration and real-time processing
- `model_manager.py`: Model loading and management
- `setup_system_audio.py`: Linux audio configuration helper

### Key Application Flow
1. **Audio Capture**: Platform-specific audio input → circular buffer → 3-second chunks
2. **Transcription Pipeline**: Audio chunks → Whisper model → confidence filtering → WebSocket broadcast
3. **Real-time Communication**: WebSocket connection delivers transcriptions to frontend
4. **State Management**: Global app_state tracks capture status, connected clients, transcription queue

### Tauri Integration (`src-tauri/`)
- `main.rs`: Tauri entry point with sidecar process management
- `tauri.conf.json`: Configuration for desktop app bundling
- Uses `start_app.py` as external binary sidecar
- Environment variable `TAURI=1` enables Tauri mode (no frontend server)

## Important Technical Details

### Audio Processing
- Sample rate: 16000 Hz (Whisper requirement)
- Chunk duration: 3 seconds with 0.5s overlap
- Voice Activity Detection (VAD) to filter silence
- Platform detection automatically selects audio backend

### Model Management
- Default model: "tiny" for real-time performance
- Models downloaded to `models/` directory  
- CPU-first approach (CUDA disabled by default to prevent crashes)
- Supports model switching via API endpoints

### Development Patterns
- Use `uv` for Python dependency management (80x faster than pip)
- WebSocket for real-time communication between frontend and backend
- Error handling with platform-specific fallbacks
- Logging with different levels for development vs production

### Testing and Debugging
```bash
# Test backend API
python test_mvp.py

# Test WebSocket connection
python test_websocket.py

# Debug WebSocket in browser
# Open debug_websocket.html in browser
```

## Entry Points and URLs

- **Main Application**: `python start_app.py` 
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket Endpoint**: ws://localhost:8000/ws

## Platform-Specific Notes

### Windows
- Requires PyAudioWPatch for WASAPI audio capture
- Supports both microphone and system audio (loopback)
- Automatic device detection and fallback

### Linux
- Uses sounddevice with ALSA/PulseAudio
- System audio requires PulseAudio monitor setup
- Automatic dependency installation via install script

### macOS  
- Uses sounddevice with CoreAudio
- Microphone access permissions required
- System audio capture through aggregate devices

## Common Issues and Solutions

### Audio Capture Problems
- Check device permissions (microphone access)
- Verify correct audio backend installation
- Use `/audio/devices` endpoint to list available devices
- Windows: Enable Stereo Mix or use VB-Audio Cable for system audio

### Model Loading Issues
- Ensure models directory exists and has write permissions
- Check internet connection for initial model download
- Verify sufficient disk space (~40MB per model)

### Port Conflicts
- Backend uses port 8000, frontend uses 3000
- Check for conflicts: `netstat -ano | findstr :8000` (Windows)
- Kill processes if needed: `taskkill /PID <PID> /F` (Windows)