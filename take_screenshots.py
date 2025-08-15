#!/usr/bin/env python3
"""
Script para tomar screenshots de Audio Transcribe usando Playwright
"""

import asyncio
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright


class ScreenshotTaker:
    def __init__(self):
        self.screenshots_dir = Path("docs/images")
        self.screenshots_dir.mkdir(exist_ok=True)
        
    async def wait_for_app_ready(self, page):
        """Espera a que la aplicación esté lista"""
        try:
            # Esperar a que aparezca el título
            await page.wait_for_selector("h1", timeout=10000)
            # Esperar un poco más para que todo cargue
            await page.wait_for_timeout(2000)
            return True
        except Exception as e:
            print(f"Warning: App not ready: {e}")
            return False
    
    async def take_main_interface_screenshot(self, page):
        """Toma screenshot de la interfaz principal"""
        print("Taking screenshot of main interface...")
        
        # Configurar el viewport para una captura consistente
        await page.set_viewport_size({"width": 1200, "height": 800})
        
        # Ir a la página principal
        await page.goto("http://localhost:3000")
        
        if not await self.wait_for_app_ready(page):
            print("Error: Could not load application")
            return False
            
        # Tomar screenshot de la página completa
        screenshot_path = self.screenshots_dir / "main-interface.png"
        await page.screenshot(
            path=screenshot_path,
            full_page=True,
            type="png"
        )
        print(f"Screenshot saved: {screenshot_path}")
        return True
    
    async def take_api_docs_screenshot(self, page):
        """Toma screenshot de la documentación de la API"""
        print("Taking screenshot of API documentation...")
        
        await page.goto("http://localhost:8000/docs")
        
        # Esperar a que cargue la documentación
        try:
            await page.wait_for_selector(".swagger-ui", timeout=5000)
            await page.wait_for_timeout(2000)
        except:
            print("Warning: API documentation not available")
            return False
            
        screenshot_path = self.screenshots_dir / "api-docs.png"
        await page.screenshot(
            path=screenshot_path,
            full_page=True,
            type="png"
        )
        print(f"Screenshot saved: {screenshot_path}")
        return True
    
    async def take_status_screenshot(self, page):
        """Toma screenshot del endpoint de status"""
        print("Taking screenshot of status...")
        
        await page.goto("http://localhost:8000/status")
        
        # Esperar a que cargue el JSON
        await page.wait_for_timeout(1000)
        
        screenshot_path = self.screenshots_dir / "api-status.png"
        await page.screenshot(
            path=screenshot_path,
            full_page=True,
            type="png"
        )
        print(f"Screenshot saved: {screenshot_path}")
        return True
    
    async def take_websocket_debug_screenshot(self, page):
        """Toma screenshot de la página de debug WebSocket"""
        print("Taking screenshot of WebSocket debug...")
        
        debug_html_path = Path("debug_websocket.html")
        if debug_html_path.exists():
            await page.goto(f"file://{debug_html_path.absolute()}")
            await page.wait_for_timeout(2000)
            
            screenshot_path = self.screenshots_dir / "websocket-debug.png"
            await page.screenshot(
                path=screenshot_path,
                full_page=True,
                type="png"
            )
            print(f"Screenshot saved: {screenshot_path}")
            return True
        else:
            print("Warning: debug_websocket.html not found")
            return False
    
    async def create_composite_screenshot(self, page):
        """Crea un screenshot compuesto mostrando múltiples vistas"""
        print("Creating composite screenshot...")
        
        # Configurar viewport más grande
        await page.set_viewport_size({"width": 1600, "height": 1200})
        
        # Crear una página HTML con múltiples iframes
        composite_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Audio Transcribe - Multiple Views</title>
            <style>
                body { margin: 0; font-family: Arial, sans-serif; background: #f5f5f5; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
                .container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 20px; }
                .panel { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .panel h3 { margin: 0; padding: 15px; background: #f8f9fa; border-bottom: 1px solid #e9ecef; }
                iframe { width: 100%; height: 400px; border: none; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎵 Audio Transcribe</h1>
                <p>Real-time AI-powered transcription</p>
            </div>
            <div class="container">
                <div class="panel">
                    <h3>🌐 Web Interface</h3>
                    <iframe src="http://localhost:3000"></iframe>
                </div>
                <div class="panel">
                    <h3>📚 API Documentation</h3>
                    <iframe src="http://localhost:8000/docs"></iframe>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear archivo temporal
        temp_file = Path("temp_composite.html")
        temp_file.write_text(composite_html)
        
        try:
            await page.goto(f"file://{temp_file.absolute()}")
            await page.wait_for_timeout(5000)  # Esperar a que carguen los iframes
            
            screenshot_path = self.screenshots_dir / "composite-view.png"
            await page.screenshot(
                path=screenshot_path,
                full_page=True,
                type="png"
            )
            print(f"Composite screenshot saved: {screenshot_path}")
            return True
        finally:
            # Limpiar archivo temporal
            if temp_file.exists():
                temp_file.unlink()
    
    async def run(self):
        """Ejecuta la toma de screenshots"""
        print("Audio Transcribe - Screenshot Taker")
        print("====================================")
        
        async with async_playwright() as p:
            # Usar Chromium para mejores screenshots
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Configurar user agent
            await page.set_extra_http_headers({
                "User-Agent": "Audio-Transcribe-Screenshot-Bot/1.0"
            })
            
            screenshots_taken = 0
            
            try:
                # Tomar screenshot de la interfaz principal
                if await self.take_main_interface_screenshot(page):
                    screenshots_taken += 1
                
                # Tomar screenshot de la documentación API
                if await self.take_api_docs_screenshot(page):
                    screenshots_taken += 1
                
                # Tomar screenshot del status
                if await self.take_status_screenshot(page):
                    screenshots_taken += 1
                
                # Tomar screenshot de WebSocket debug si existe
                if await self.take_websocket_debug_screenshot(page):
                    screenshots_taken += 1
                
                # Crear screenshot compuesto
                if await self.create_composite_screenshot(page):
                    screenshots_taken += 1
                
            except Exception as e:
                print(f"Error taking screenshots: {e}")
            
            finally:
                await browser.close()
            
            print(f"\nProcess completed. Screenshots taken: {screenshots_taken}")
            print(f"Saved to: {self.screenshots_dir}")
            
            # Listar archivos creados
            if screenshots_taken > 0:
                print("\nScreenshots created:")
                for img_file in sorted(self.screenshots_dir.glob("*.png")):
                    size = img_file.stat().st_size / 1024
                    print(f"   • {img_file.name} ({size:.1f} KB)")


async def main():
    """Función principal"""
    # Verificar que la aplicación esté ejecutándose
    import requests
    
    try:
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code == 200:
            print("Application detected at http://localhost:8000")
        else:
            print("Warning: Application responds but with unexpected status")
    except requests.exceptions.RequestException:
        print("Error: Application is not running")
        print("Tip: Run first: python start_app.py")
        print("   Then run this script in another terminal")
        return
    
    # Ejecutar toma de screenshots
    screenshot_taker = ScreenshotTaker()
    await screenshot_taker.run()


if __name__ == "__main__":
    asyncio.run(main())