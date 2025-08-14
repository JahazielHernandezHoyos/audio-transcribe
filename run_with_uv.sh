#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p runtime

if [[ ! -f runtime/uv ]]; then
  echo "Downloading uv runtime..."
  ARCH=$(uname -m)
  OS=$(uname -s | tr '[:upper:]' '[:lower:]')
  if [[ "$OS" == "darwin" ]]; then
    if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
      FILE="uv-aarch64-apple-darwin"
    else
      FILE="uv-x86_64-apple-darwin"
    fi
  else
    if [[ "$ARCH" == "x86_64" || "$ARCH" == "amd64" ]]; then
      FILE="uv-x86_64-unknown-linux-gnu"
    else
      FILE="uv-aarch64-unknown-linux-gnu"
    fi
  fi
  curl -fsSL -o runtime/uv "https://github.com/astral-sh/uv/releases/latest/download/${FILE}"
  chmod +x runtime/uv
fi

echo "Starting Audio Transcribe with uv runtime..."
"$SCRIPT_DIR/runtime/uv" run python start_app.py

