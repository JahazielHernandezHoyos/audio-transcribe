@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Determine script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Ensure runtime folder
if not exist runtime mkdir runtime

REM Download uv.exe if missing
if not exist runtime\uv.exe (
  echo Downloading uv runtime...
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue'; ^
     $u='https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.exe'; ^
     $d='runtime/uv.exe'; ^
     Invoke-WebRequest -Uri $u -OutFile $d"
)

echo Starting Audio Transcribe with uv runtime...
"%SCRIPT_DIR%runtime\uv.exe" run python start_app.py

endlocal

