@echo off
REM Audio Transcribe - Instalador para Windows
REM Instala dependencias y configura el entorno

echo.
echo 🎵 Audio Transcribe - Instalador para Windows
echo ============================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado
    echo 💡 Instala Python desde: https://python.org/downloads/
    echo    Asegúrate de marcar "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python detectado:
python --version

REM Verificar si UV está instalado
uv --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo 📦 UV no está instalado, instalando...
    echo 💡 Instalando UV (gestor de dependencias)...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    
    REM Agregar UV al PATH para esta sesión
    set PATH=%USERPROFILE%\.cargo\bin;%PATH%
    
    REM Verificar instalación
    uv --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Error instalando UV
        echo 💡 Instala manualmente desde: https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
)

echo ✅ UV detectado:
uv --version

echo.
echo 📦 Instalando dependencias Python...
uv sync

echo.
echo 🎤 Verificando PyAudioWPatch para Windows...
uv add "PyAudioWPatch>=0.2.12.5"

echo.
echo ✅ Instalación completada!
echo.
echo 🚀 Para ejecutar la aplicación usa:
echo    python start_app.py
echo.
echo 🌐 La aplicación estará disponible en:
echo    http://localhost:3000
echo.
echo 💡 Consejos para Windows:
echo    • Permite el acceso al micrófono cuando se solicite
echo    • Para capturar audio del sistema, habilita "Stereo Mix" en configuración de audio
echo    • Si tienes problemas con PyTorch/CUDA, la app forzará modo CPU automáticamente
echo.
pause
