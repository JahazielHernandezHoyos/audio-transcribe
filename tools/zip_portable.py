"""
Create a portable UV-based runtime ZIP for Audio Transcribe.

This bundles the app source files plus launcher scripts that fetch a
standalone 'uv' binary on first run and start the app via `uv run`.
"""

from __future__ import annotations

import sys
from pathlib import Path
import zipfile


def add_path_to_zip(zipf: zipfile.ZipFile, base_dir: Path, path: Path) -> None:
    """Add a file or directory to zip preserving relative paths."""
    if path.is_dir():
        for p in path.rglob("*"):
            if p.is_file():
                arcname = p.relative_to(base_dir)
                zipf.write(p, arcname)
    elif path.is_file():
        arcname = path.relative_to(base_dir)
        zipf.write(path, arcname)


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent
    dist_dir = base_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    target_zip = dist_dir / "AudioTranscribe-portable-uv.zip"

    includes = [
        base_dir / "start_app.py",
        base_dir / "frontend",
        base_dir / "backend",
        base_dir / "models",
        base_dir / "run_with_uv.bat",
        base_dir / "run_with_uv.sh",
        base_dir / "pyproject.toml",
        base_dir / "uv.lock",
        base_dir / "README.md",
    ]

    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in includes:
            if item.exists():
                add_path_to_zip(zf, base_dir, item)

    print(f"✅ Created: {target_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


