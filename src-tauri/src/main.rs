#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{api::process::Command, Manager};

#[tauri::command]
async fn start_backend(app: tauri::AppHandle) -> Result<u16, String> {
  let port = portpicker::pick_unused_port().unwrap_or(8000);
  // Set TAURI=1 so our Python starter doesn't spin the local 3000 server
  let mut cmd = Command::new_sidecar("AudioTranscribe")
    .map_err(|e| e.to_string())?
    .env("TAURI", "1")
    .spawn()
    .map_err(|e| e.to_string())?;
  tauri::async_runtime::spawn(async move {
    let _ = cmd.wait().await;
  });
  Ok(port)
}

fn main() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![start_backend])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}


