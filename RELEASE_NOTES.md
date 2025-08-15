# :audio-transcribe v1.0.0

## 🎉 First Official Release

Real-time audio transcription powered by OpenAI Whisper, now available for all platforms! 

Built with a beautiful Vim-inspired interface for developers and power users.

### ✨ Features

- **Real-time transcription** with <3 second latency
- **Cross-platform support** (Windows, Linux, macOS)
- **Vim-inspired interface** with terminal-style design
- **AI-powered accuracy** using OpenAI Whisper "tiny" model
- **Privacy-focused** - all processing happens locally
- **Easy installation** with one-click installers
- **Modern web interface** with WebSocket real-time updates

### 📥 Installation Options

#### Windows
- **Recommended**: Download the Windows installer (coming soon)
- **Alternative**: Use the Unix installer via WSL

#### Linux/macOS
- **One-click install**: 
  ```bash
  curl -sSL https://raw.githubusercontent.com/JahazielHernandezHoyos/audio-transcribe/main/unix_installer.sh | bash
  ```
- **Portable**: Download `audio-transcribe-portable.tar.gz`

#### From Source
- Download `audio-transcribe-source-v1.0.0.tar.gz`
- See README.md for build instructions

### 🔧 System Requirements

- **Windows**: Windows 10+ with microphone access
- **Linux**: Ubuntu 18.04+, CentOS 7+, or equivalent with ALSA/PulseAudio
- **macOS**: macOS 10.15+ with microphone permissions
- **All platforms**: Python 3.8+, ~100MB disk space

### 🌐 Web Interface

After installation, access the application at:
- **Main interface**: http://localhost:3000
- **API documentation**: http://localhost:8000/docs

### 🎨 Design

Features a beautiful Vim-inspired dark theme with:
- Terminal-style green and yellow color scheme
- Monospace fonts throughout
- Command-line aesthetic
- Glowing borders and text effects

### 🛟 Support

- **Documentation**: See README.md and docs/
- **Issues**: [GitHub Issues](https://github.com/JahazielHernandezHoyos/audio-transcribe/issues)
- **Developer**: [Jahaziel Hernández](https://www.linkedin.com/in/jahaziel-anthony-h-6586b5139/)

### 🔒 Security

All files are provided with checksums in `checksums.sha256`.

---

**Made with ❤️ by [Jahaziel Hernández](https://github.com/JahazielHernandezHoyos)**

**Full Changelog**: https://github.com/JahazielHernandezHoyos/audio-transcribe/commits/v1.0.0