# Frontend - Tauri Desktop Application

## Propósito
Interfaz de escritorio multiplataforma usando Tauri para controlar la transcripción de audio.

## Tecnologías
- **Tauri 2.x**: Framework para apps de escritorio
- **HTML/CSS/JS**: Frontend web embebido
- **Rust**: Backend nativo de Tauri
- **WebSocket**: Comunicación en tiempo real con API Python

## Componentes de UI

### 1. Interfaz Principal
- **Botón Start/Stop**: Control de captura de audio
- **Área de texto**: Mostrar transcripción en tiempo real
- **Indicador de estado**: Conectado/Desconectado/Transcribiendo
- **Configuraciones básicas**: Idioma, sensibilidad

### 2. Comunicación con Backend
- **HTTP REST**: Para control (start/stop/status)
- **WebSocket**: Para stream de transcripción en tiempo real
- **Manejo de errores**: Reconexión automática, timeouts

### 3. Configuración Tauri
```json
{
  "identifier": "com.audio-transcribe.app",
  "productName": "Audio Transcribe",
  "version": "0.1.0",
  "bundle": {
    "targets": ["deb", "msi", "app", "dmg"]
  }
}
```

## Estructura de Archivos
```
frontend/
├── src-tauri/
│   ├── Cargo.toml       # Dependencias Rust
│   ├── tauri.conf.json  # Configuración Tauri
│   └── src/
│       └── main.rs      # Punto de entrada Rust
├── src/
│   ├── index.html       # UI principal
│   ├── style.css        # Estilos
│   ├── script.js        # Lógica de frontend
│   └── websocket.js     # Comunicación WebSocket
└── icons/               # Iconos de la aplicación
```

## Estado Actual
- ⏳ Instalación de Tauri CLI pendiente
- ⏳ Inicialización del proyecto Tauri pendiente
- ⏳ Diseño de UI pendiente
- ⏳ Implementación de comunicación con backend pendiente

## Comandos de Desarrollo
```bash
# Instalar Tauri CLI (requiere Rust)
cargo install tauri-cli --version "^2.0"

# Inicializar proyecto Tauri
cargo tauri init

# Desarrollo con hot reload
cargo tauri dev

# Build para producción
cargo tauri build
```

## Distribución Final
- **Windows**: .msi installer (~5-10MB)
- **Linux**: .deb package (~5-10MB)
- **Ejecutables portables** sin instalación
- **Bundle del modelo Whisper** incluido