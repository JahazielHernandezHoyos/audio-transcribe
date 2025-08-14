#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager};
use tauri_plugin_shell::ShellExt;

#[tauri::command]
async fn start_backend(app: tauri::AppHandle) -> Result<u16, String> {
  let port = portpicker::pick_unused_port().unwrap_or(8000);
  let shell = app.shell();
  let mut child = shell.sidecar("AudioTranscribe")
    .map_err(|e| e.to_string())?
    .env("TAURI", "1")
    .spawn()
    .map_err(|e| e.to_string())?;
  tauri::async_runtime::spawn(async move {
    let _ = child.wait().await;
  });
  Ok(port)
}

fn main() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .invoke_handler(tauri::generate_handler![start_backend])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}


