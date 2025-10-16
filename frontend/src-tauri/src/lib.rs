use serde_json::json;

// Tauri command to send chat message to FastAPI backend
#[tauri::command]
async fn send_chat_message(message: String, session_id: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .post("http://localhost:8000/api/chat")
        .json(&json!({
            "message": message,
            "session_id": session_id
        }))
        .send()
        .await
        .map_err(|e| format!("Failed to send request: {}", e))?;
    
    let result = response
        .text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))?;
    
    Ok(result)
}

// Tauri command to get chat history
#[tauri::command]
async fn get_chat_history(session_id: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get(format!("http://localhost:8000/api/chat/{}", session_id))
        .send()
        .await
        .map_err(|e| format!("Failed to get history: {}", e))?;
    
    let result = response
        .text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))?;
    
    Ok(result)
}

// Tauri command to check API health
#[tauri::command]
async fn check_api_health() -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get("http://localhost:8000/api/health")
        .send()
        .await
        .map_err(|e| format!("Failed to check health: {}", e))?;
    
    let result = response
        .text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))?;
    
    Ok(result)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            send_chat_message,
            get_chat_history,
            check_api_health
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
