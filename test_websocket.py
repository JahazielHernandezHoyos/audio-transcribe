#!/usr/bin/env python3
"""
Test para verificar funcionalidad del WebSocket.
Simula transcripciones para probar el flujo completo.
"""


import requests


def test_api_endpoints():
    """Test básico de endpoints."""
    print("🧪 Probando endpoints de API...")

    try:
        # Test status
        response = requests.get("http://127.0.0.1:8000/status", timeout=5)
        print(f"Status: {response.status_code}")

        # Test models
        response = requests.get("http://127.0.0.1:8000/models", timeout=5)
        print(f"Models: {response.status_code}")

        # Agregar una transcripción de prueba directamente a la cola
        test_transcription = {
            "text": "Esta es una transcripción de prueba",
            "confidence": 0.95,
            "processing_time": 0.25,
            "model": "tiny",
            "volume": 0.5,
            "max_amplitude": 0.8
        }

        # Simular inserción en cola
        print("📝 Insertando transcripción de prueba...")
        response = requests.post("http://127.0.0.1:8000/debug/add_transcription",
                               json=test_transcription, timeout=5)

        return True

    except Exception as e:
        print(f"Error en test: {e}")
        return False

def add_debug_endpoint():
    """Agregar endpoint de debug para insertar transcripciones."""
    print("🔧 Agregando endpoint de debug...")

    # Este endpoint se debería agregar temporalmente al main.py
endpoint_code = '''
@app.post("/debug/add_transcription")
async def debug_add_transcription(transcription: dict):
    """Endpoint de debug para agregar transcripción de prueba."""
    app_state["transcription_queue"].put(transcription)
    return {"success": True, "message": "Transcripción agregada a la cola"}
'''

print("Agrega este código temporalmente a main.py:")
print(endpoint_code)

if __name__ == "__main__":
    print("🧪 Test de WebSocket - Audio Transcribe")
    print("=" * 50)

    # Instrucciones para test manual
    print("Para probar el WebSocket:")
    print("1. Inicia el servidor: uv run python start_app.py")
    print("2. Abre http://localhost:3000 en el navegador")
    print("3. Abre DevTools > Console")
    print("4. Inicia captura y habla al micrófono")
    print("5. Verifica que aparezcan logs de WebSocket")
    print()

    add_debug_endpoint()

    # Test básico de conectividad
    if test_api_endpoints():
        print("✅ API endpoints funcionando")
    else:
        print("❌ Problemas con API endpoints")
