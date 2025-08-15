@echo off
title Audio Transcribe - Instalador para Windows
chcp 65001 >nul
cls
echo.
echo     ╔══════════════════════════════════════╗
echo     ║        Audio Transcribe v1.0         ║  
echo     ║     Instalador para Windows          ║
echo     ╚══════════════════════════════════════╝
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado
    echo.
    echo Por favor instala Python 3.8+ desde:
    echo https://python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

:: Crear directorio de instalación
set INSTALL_DIR=%USERPROFILE%\AppData\Local\AudioTranscribe
echo 📁 Creando directorio: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Cambiar al directorio de instalación
cd /d "%INSTALL_DIR%"

:: Descargar archivos
echo 📥 Descargando Audio Transcribe desde GitHub...
curl -L "https://github.com/JahazielHernandezHoyos/audio-transcribe/archive/refs/heads/master.zip" -o audio-transcribe.zip

if not exist audio-transcribe.zip (
    echo ❌ Error descargando archivos
    pause
    exit /b 1
)

:: Extraer archivos usando PowerShell
echo 📦 Extrayendo archivos...
powershell -command "Expand-Archive -Path 'audio-transcribe.zip' -DestinationPath '.' -Force"

:: Mover archivos del subdirectorio
if exist audio-transcribe-master (
    move audio-transcribe-master\* . >nul 2>&1
    rmdir /s /q audio-transcribe-master
)
del audio-transcribe.zip

:: Verificar si los archivos se extrajeron correctamente
if not exist start_app.py (
    echo ❌ Error: No se encontraron los archivos de la aplicación
    pause
    exit /b 1
)

:: Instalar UV si no existe
echo 🔧 Verificando UV (gestor de paquetes)...
where uv >nul 2>&1
if errorlevel 1 (
    echo Instalando UV...
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if errorlevel 1 (
        echo ❌ Error instalando UV
        pause
        exit /b 1
    )
    :: Agregar UV al PATH de la sesión actual
    set PATH=%USERPROFILE%\.local\bin;%PATH%
)

:: Instalar dependencias
echo 📦 Instalando dependencias de Python...
uv sync
if errorlevel 1 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)

:: Crear script de ejecución
echo 🔗 Creando launcher...
(
echo @echo off
echo title Audio Transcribe
echo cd /d "%INSTALL_DIR%"
echo echo Iniciando Audio Transcribe...
echo python start_app.py
echo pause
) > "%INSTALL_DIR%\AudioTranscribe.bat"

:: Crear acceso directo en el escritorio
echo 🖥️ Creando acceso directo en el escritorio...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Audio Transcribe.lnk
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%INSTALL_DIR%\AudioTranscribe.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = 'shell32.dll,21'; $Shortcut.Save()"

:: Crear entrada en el menú de inicio
echo 📋 Creando entrada en el menú de inicio...
set START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%"
copy "%SHORTCUT_PATH%" "%START_MENU_DIR%\Audio Transcribe.lnk" >nul

echo.
echo ✅ ¡Instalación completada exitosamente!
echo.
echo 🚀 Para ejecutar Audio Transcribe:
echo    • Usa el acceso directo del escritorio
echo    • O búscalo en el menú de inicio
echo    • O ejecuta: %INSTALL_DIR%\AudioTranscribe.bat
echo.
echo 🌐 La aplicación se abrirá en: http://localhost:3000
echo 📚 Documentación API: http://localhost:8000/docs
echo.
echo 💡 Consejo: Marca estos enlaces como favoritos en tu navegador
echo.
pause