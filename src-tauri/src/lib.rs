use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;
use sysinfo::System;
use tauri::{Emitter, Manager};
use tokio::sync::Mutex;

static FORCE_CONNECT: AtomicBool = AtomicBool::new(false);

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameStatus {
    pub game_running: bool,
    pub connected: bool,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub id: u64,
    pub msg: String,
    pub sender: String,
    #[serde(default)]
    pub enemy: bool,
    #[serde(default)]
    pub mode: String,
    #[serde(default)]
    pub time: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranslatedChatMessage {
    pub id: u64,
    pub sender: String,
    pub original: String,
    pub translated: String,
    pub enemy: bool,
    pub mode: String,
    pub time: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryPayload {
    pub state: serde_json::Value,
    pub indicators: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HudMsgPayload {
    pub id: u64,
    pub msg: String,
    pub category: String,
}

pub struct AppState {
    pub chat_history: Arc<Mutex<Vec<TranslatedChatMessage>>>,
}

fn translate_chat_message(text: &str, lang: &str) -> String {
    let trimmed = text.trim();
    if trimmed.contains("Внимание на карту!") {
        let replacement = match lang {
            "DE" => "Achtung auf die Karte!",
            "ES" => "¡Atención al mapa!",
            "FR" => "Attention à la carte!",
            "PL" => "Uwaga na mapę!",
            "PT" => "Atenção ao mapa!",
            "ZH" => "注意地图！",
            _ => "Attention to the map!",
        };
        return text.replace("Внимание на карту!", replacement);
    }
    if trimmed.contains("Атакуйте точку") {
        let replacement = match lang {
            "DE" => "Greift den Punkt an",
            "ES" => "Atacad el punto",
            "FR" => "Attaquez le point",
            "PL" => "Atakować punkt",
            "PT" => "Ataquem o ponto",
            "ZH" => "攻击目标点",
            _ => "Attack point",
        };
        return text.replace("Атакуйте точку", replacement);
    }
    if trimmed.contains("Защищайте точку") {
        let replacement = match lang {
            "DE" => "Verteidigt den Punkt",
            "ES" => "Defended el punto",
            "FR" => "Défendez le point",
            "PL" => "Bronić punktu",
            "PT" => "Defendam o ponto",
            "ZH" => "防守目标点",
            _ => "Defend point",
        };
        return text.replace("Защищайте точку", replacement);
    }
    if trimmed.contains("Спасибо!") {
        let replacement = match lang {
            "DE" => "Danke!",
            "ES" => "¡Gracias!",
            "FR" => "Merci!",
            "PL" => "Dziękuję!",
            "PT" => "Obrigado!",
            "ZH" => "谢谢！",
            _ => "Thank you!",
        };
        return text.replace("Спасибо!", replacement);
    }

    let has_non_ascii = text.chars().any(|c| c as u32 > 127);
    if has_non_ascii {
        format!("[{} Translation]: {}", lang, text)
    } else {
        text.to_string()
    }
}

#[tauri::command]
fn toggle_click_through(window: tauri::Window, ignore: bool) -> Result<(), String> {
    window.set_ignore_cursor_events(ignore).map_err(|e| e.to_string())
}

#[tauri::command]
fn force_connect() {
    FORCE_CONNECT.store(true, Ordering::SeqCst);
}

#[tauri::command]
fn get_system_status() -> GameStatus {
    let mut sys = System::new_all();
    sys.refresh_processes(sysinfo::ProcessesToUpdate::All, true);
    let running = sys.processes().values().any(|p| {
        let p_name = p.name().to_string_lossy().to_lowercase();
        p_name.contains("aces") || p_name.contains("warthunder") || p_name.contains("win64")
    }) || FORCE_CONNECT.load(Ordering::SeqCst);

    GameStatus {
        game_running: running,
        connected: false,
        message: if running {
            "aces.exe detected. Polling telemetry...".into()
        } else {
            "Waiting for War Thunder (aces.exe)...".into()
        },
    }
}

#[tauri::command]
fn start_drag(window: tauri::Window) -> Result<(), String> {
    window.start_dragging().map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_chat_history(state: tauri::State<'_, AppState>) -> Result<Vec<TranslatedChatMessage>, String> {
    let history = state.chat_history.lock().await;
    Ok(history.clone())
}

pub fn run() {
    let chat_history = Arc::new(Mutex::new(Vec::<TranslatedChatMessage>::new()));
    let chat_history_bg = chat_history.clone();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(AppState {
            chat_history,
        })
        .invoke_handler(tauri::generate_handler![
            toggle_click_through,
            get_system_status,
            start_drag,
            get_chat_history,
            force_connect
        ])
        .setup(move |app| {
            let app_handle = app.handle().clone();

            // Ensure window is in interactive mode on launch
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_ignore_cursor_events(false);
            }

            // Background Tokio loop for Game Detection & Telemetry Polling
            tauri::async_runtime::spawn(async move {
                let client = reqwest::Client::builder()
                    .timeout(Duration::from_secs(2))
                    .build()
                    .unwrap_or_default();

                let mut sys = System::new_all();
                let seen_chats: Arc<Mutex<HashSet<u64>>> = Arc::new(Mutex::new(HashSet::new()));
                let seen_hudmsgs: Arc<Mutex<HashSet<String>>> = Arc::new(Mutex::new(HashSet::new()));
                let mut last_chat_id: u64 = 0;
                let mut last_evt_id: u64 = 0;
                let mut last_dmg_id: u64 = 0;

                loop {
                    // Step 1: Game Detection (Process Check + Direct HTTP Probe Fallback)
                    sys.refresh_processes(sysinfo::ProcessesToUpdate::All, true);
                    let proc_running = sys.processes().values().any(|p| {
                        let p_name = p.name().to_string_lossy().to_lowercase();
                        p_name.contains("aces") || p_name.contains("warthunder") || p_name.contains("win64")
                    });

                    // Quick probe check if 8111 web server is alive (any response means it's WT)
                    let http_active = client
                        .get("http://127.0.0.1:8111/")
                        .send()
                        .await
                        .is_ok();

                    let forced = FORCE_CONNECT.load(Ordering::SeqCst);
                    let game_running = proc_running || http_active || forced;

                    if !game_running {
                        let _ = app_handle.emit(
                            "wt-status",
                            GameStatus {
                                game_running: false,
                                connected: false,
                                message: "War Thunder (aces.exe) is not running.".into(),
                            },
                        );
                        tokio::time::sleep(Duration::from_secs(2)).await;
                        continue;
                    }

                    // Step 2: Poll Telemetry (State & Indicators)
                    let state_res = client.get("http://127.0.0.1:8111/state").send().await;
                    let indicators_res = client.get("http://127.0.0.1:8111/indicators").send().await;

                    match (state_res, indicators_res) {
                        (Ok(state_resp), Ok(ind_resp)) if state_resp.status().is_success() && ind_resp.status().is_success() => {
                            if let (Ok(state_json), Ok(ind_json)) = (
                                state_resp.json::<serde_json::Value>().await,
                                ind_resp.json::<serde_json::Value>().await,
                            ) {
                                let _ = app_handle.emit(
                                    "wt-status",
                                    GameStatus {
                                        game_running: true,
                                        connected: true,
                                        message: "Connected to 127.0.0.1:8111".into(),
                                    },
                                );

                                let _ = app_handle.emit(
                                    "wt-telemetry",
                                    TelemetryPayload {
                                        state: state_json,
                                        indicators: ind_json,
                                    },
                                );

                                // Step 3: Poll Gamechat with ?lastId= parameter
                                let chat_url = format!("http://127.0.0.1:8111/gamechat?lastId={}", last_chat_id);
                                if let Ok(chat_resp) = client.get(&chat_url).send().await {
                                    if chat_resp.status().is_success() {
                                        if let Ok(json_items) = chat_resp.json::<Vec<serde_json::Value>>().await {
                                            let mut history = chat_history_bg.lock().await;
                                            let mut seen = seen_chats.lock().await;

                                            // Detect new match restart (IDs reset)
                                            if let Some(first_item) = json_items.first() {
                                                let first_id = first_item.get("id").and_then(|v| v.as_u64()).unwrap_or(0);
                                                if first_id > 0 && first_id < last_chat_id {
                                                    seen.clear();
                                                    history.clear();
                                                    last_chat_id = 0;
                                                    last_evt_id = 0;
                                                    last_dmg_id = 0;
                                                }
                                            }

                                            for item in json_items {
                                                let id = item.get("id").and_then(|v| v.as_u64()).unwrap_or(0);
                                                let msg = item.get("msg").and_then(|v| v.as_str()).unwrap_or("").to_string();
                                                let sender = item.get("sender").and_then(|v| v.as_str()).unwrap_or("System").to_string();
                                                let enemy = item.get("enemy").and_then(|v| v.as_bool()).unwrap_or(false);
                                                let mode = item.get("mode").and_then(|v| v.as_str()).unwrap_or("all").to_string();
                                                let time = item.get("time").and_then(|v| v.as_u64()).unwrap_or(0);

                                                if id > last_chat_id {
                                                    last_chat_id = id;
                                                }

                                                if !seen.contains(&id) {
                                                    seen.insert(id);
                                                    let translated = translate_chat_message(&msg, "EN");
                                                    let payload = TranslatedChatMessage {
                                                        id,
                                                        sender,
                                                        original: msg,
                                                        translated,
                                                        enemy,
                                                        mode,
                                                        time,
                                                    };
                                                    history.push(payload.clone());
                                                    let _ = app_handle.emit("wt-chat", payload);
                                                }
                                            }
                                        }
                                    }
                                }

                                // Step 4: Poll /hudmsg?lastEvt={last_evt_id}&lastDmg={last_dmg_id}
                                let hud_url = format!("http://127.0.0.1:8111/hudmsg?lastEvt={}&lastDmg={}", last_evt_id, last_dmg_id);
                                if let Ok(hud_resp) = client.get(&hud_url).send().await {
                                    if hud_resp.status().is_success() {
                                        if let Ok(hud_json) = hud_resp.json::<serde_json::Value>().await {
                                            let mut seen_hud = seen_hudmsgs.lock().await;

                                            // Process 'events' array (kills, team events)
                                            if let Some(events) = hud_json.get("events").and_then(|v| v.as_array()) {
                                                for evt in events {
                                                    let id = evt.get("id").and_then(|v| v.as_u64()).unwrap_or(0);
                                                    let msg = evt.get("msg").and_then(|v| v.as_str()).unwrap_or("").to_string();
                                                    if id > last_evt_id {
                                                        last_evt_id = id;
                                                    }
                                                    let key = format!("evt:{}:{}", id, msg);
                                                    if !seen_hud.contains(&key) && !msg.is_empty() {
                                                        seen_hud.insert(key);
                                                        let payload = HudMsgPayload {
                                                            id,
                                                            msg,
                                                            category: "evt".into(),
                                                        };
                                                        let _ = app_handle.emit("wt-hudmsg", payload);
                                                    }
                                                }
                                            }

                                            // Process 'damage' array (hits, damage logs)
                                            if let Some(damage) = hud_json.get("damage").and_then(|v| v.as_array()) {
                                                for dmg in damage {
                                                    let id = dmg.get("id").and_then(|v| v.as_u64()).unwrap_or(0);
                                                    let msg = dmg.get("msg").and_then(|v| v.as_str()).unwrap_or("").to_string();
                                                    if id > last_dmg_id {
                                                        last_dmg_id = id;
                                                    }
                                                    let key = format!("dmg:{}:{}", id, msg);
                                                    if !seen_hud.contains(&key) && !msg.is_empty() {
                                                        seen_hud.insert(key);
                                                        let payload = HudMsgPayload {
                                                            id,
                                                            msg,
                                                            category: "dmg".into(),
                                                        };
                                                        let _ = app_handle.emit("wt-hudmsg", payload);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                                tokio::time::sleep(Duration::from_millis(300)).await;
                            } else {
                                let _ = app_handle.emit(
                                    "wt-status",
                                    GameStatus {
                                        game_running: true,
                                        connected: false,
                                        message: "In hangar or waiting for match data...".into(),
                                    },
                                );
                                tokio::time::sleep(Duration::from_secs(3)).await;
                            }
                        }
                        _ => {
                            let _ = app_handle.emit(
                                "wt-status",
                                GameStatus {
                                    game_running: true,
                                    connected: false,
                                    message: "Game running, but 127.0.0.1:8111 is offline (in hangar). Retrying in 3s...".into(),
                                },
                            );
                            tokio::time::sleep(Duration::from_secs(3)).await;
                        }
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
