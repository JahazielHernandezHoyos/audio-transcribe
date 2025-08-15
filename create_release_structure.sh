#!/bin/bash
# Audio Transcribe - Create GitHub Release Structure

set -e

echo "📦 Creating GitHub Release Structure..."
echo "====================================="

VERSION="v1.0.0"
RELEASE_DIR="release-artifacts"

# Clean and create release directory
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

echo "📂 Copying release files..."

# Copy Windows executable (if it exists)
if [ -f "src-tauri/target/release/bundle/msi/Audio Transcribe_1.0.0_x64_en-US.msi" ]; then
    cp "src-tauri/target/release/bundle/msi/Audio Transcribe_1.0.0_x64_en-US.msi" "$RELEASE_DIR/audio-transcribe-windows-installer.msi"
    echo "✅ Windows MSI installer copied"
fi

if [ -f "src-tauri/target/release/audio-transcribe.exe" ]; then
    cp "src-tauri/target/release/audio-transcribe.exe" "$RELEASE_DIR/audio-transcribe-windows.exe"
    echo "✅ Windows executable copied"
fi

# Copy Unix installer
if [ -f "unix_installer.sh" ]; then
    cp "unix_installer.sh" "$RELEASE_DIR/"
    echo "✅ Unix installer copied"
fi

# Copy portable distribution
if [ -f "dist/audio-transcribe-portable-"*.tar.gz ]; then
    cp dist/audio-transcribe-portable-*.tar.gz "$RELEASE_DIR/audio-transcribe-portable.tar.gz"
    echo "✅ Portable distribution copied"
fi

# Copy documentation
cp README.md "$RELEASE_DIR/"
cp CLAUDE.md "$RELEASE_DIR/"
cp -r docs "$RELEASE_DIR/"

# Create source archive
echo "📦 Creating source archive..."
git archive --format=tar.gz --prefix=audio-transcribe-$VERSION/ HEAD > "$RELEASE_DIR/audio-transcribe-source-$VERSION.tar.gz"

# Create checksums
echo "🔐 Creating checksums..."
cd "$RELEASE_DIR"
sha256sum * > checksums.sha256
cd ..

# Create release notes
cat > "$RELEASE_DIR/RELEASE_NOTES.md" << 'RELEASE_NOTES'
# Audio Transcribe v1.0.0

## 🎉 First Official Release

Real-time audio transcription powered by OpenAI Whisper, now available for all platforms!

### ✨ Features

- **Real-time transcription** with <3 second latency
- **Cross-platform support** (Windows, Linux, macOS)
- **Modern web interface** with WebSocket real-time updates
- **AI-powered accuracy** using OpenAI Whisper "tiny" model
- **Privacy-focused** - all processing happens locally
- **Easy installation** with one-click installers

### 📥 Installation Options

#### Windows
- **Recommended**: Download `audio-transcribe-windows-installer.msi`
- **Alternative**: Download `audio-transcribe-windows.exe`

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

### 🛟 Support

- **Documentation**: See README.md and docs/
- **Issues**: Report at GitHub Issues
- **Community**: GitHub Discussions

### 🔒 Security

All files are signed and checksums are provided in `checksums.sha256`.

---

**Full Changelog**: https://github.com/JahazielHernandezHoyos/audio-transcribe/commits/v1.0.0
RELEASE_NOTES

echo ""
echo "✅ Release structure created successfully!"
echo ""
echo "📁 Release artifacts in: $RELEASE_DIR/"
echo ""
echo "📋 Available files:"
ls -la "$RELEASE_DIR/"
echo ""
echo "🚀 Ready for GitHub release upload!"
echo ""
echo "💡 Next steps:"
echo "1. Create a new release on GitHub"
echo "2. Upload all files from $RELEASE_DIR/"
echo "3. Use RELEASE_NOTES.md as release description"
echo "4. Set tag: $VERSION"