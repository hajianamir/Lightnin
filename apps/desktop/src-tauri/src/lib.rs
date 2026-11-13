//! AegisLPS Tauri 2 Desktop Host (`ADR-002`, Step 5.3).
//!
//! Security properties:
//! 1. Allocates a free ephemeral loopback port (`127.0.0.1:<port>`).
//! 2. Generates a 32-byte CSPRNG session bearer token (`AEGISLPS_SIDECAR_TOKEN`)
//!    and exposes `{ baseUrl, token }` to the WebView via `get_backend_config`.
//! 3. Loads or creates a `>= 32`-byte HMAC project integrity key in Windows
//!    Credential Manager (`keyring` crate, `windows-native` backend) and passes
//!    it exclusively to the sidecar process via `AEGISLPS_INTEGRITY_KEY`. Neither
//!    secret is ever logged or written to files; the integrity key is never
//!    returned to the WebView.
//! 4. Note on `.lps` portability: because the installation integrity key resides
//!    in the local Windows Credential Manager, `.lps` project checksums verify
//!    only on the installation that created them.

use std::fmt;
use std::net::TcpListener;
use std::sync::Mutex;

use serde::Serialize;
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

const CREDENTIAL_SERVICE: &str = "org.aegislps.desktop";
const CREDENTIAL_ACCOUNT: &str = "project_integrity_hmac_key";
const MIN_INTEGRITY_KEY_BYTES: usize = 32;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BackendConfig {
    pub base_url: String,
    pub token: String,
}

impl fmt::Debug for BackendConfig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("BackendConfig")
            .field("base_url", &self.base_url)
            .field("token", &"[REDACTED]")
            .finish()
    }
}

pub struct AppState {
    config: BackendConfig,
    sidecar_child: Mutex<Option<CommandChild>>,
}

impl fmt::Debug for AppState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("AppState")
            .field("config", &self.config)
            .field("sidecar_running", &self.sidecar_child.lock().map(|g| g.is_some()).unwrap_or(false))
            .finish()
    }
}

#[tauri::command]
pub fn get_backend_config(state: tauri::State<'_, AppState>) -> BackendConfig {
    state.config.clone()
}

fn generate_csprng_hex_32_bytes() -> Result<String, String> {
    let mut raw = [0u8; 32];
    getrandom::getrandom(&mut raw).map_err(|_| "OS CSPRNG entropy generation failed".to_string())?;
    let mut hex = String::with_capacity(64);
    for byte in raw {
        use std::fmt::Write as _;
        let _ = write!(&mut hex, "{byte:02x}");
    }
    Ok(hex)
}

fn pick_free_loopback_port() -> Result<u16, String> {
    let listener = TcpListener::bind(("127.0.0.1", 0))
        .map_err(|e| format!("Failed to bind ephemeral loopback port: {e}"))?;
    let port = listener
        .local_addr()
        .map_err(|e| format!("Failed to inspect loopback socket address: {e}"))?
        .port();
    drop(listener);
    Ok(port)
}

/// Retrieves or initializes the per-installation `AEGISLPS_INTEGRITY_KEY`
/// (`>= 32` UTF-8 bytes) inside Windows Credential Manager. Never logs key material.
fn load_or_create_integrity_key() -> Result<String, String> {
    let entry = keyring::Entry::new(CREDENTIAL_SERVICE, CREDENTIAL_ACCOUNT)
        .map_err(|_| "Unable to open OS credential store entry".to_string())?;

    match entry.get_password() {
        Ok(existing) if existing.len() >= MIN_INTEGRITY_KEY_BYTES => Ok(existing),
        Ok(_) | Err(keyring::Error::NoEntry) => {
            let generated = generate_csprng_hex_32_bytes()?;
            entry
                .set_password(&generated)
                .map_err(|_| "Unable to persist integrity key in OS credential store".to_string())?;
            Ok(generated)
        }
        Err(_) => Err("Unable to read integrity key from OS credential store".to_string()),
    }
}

fn terminate_sidecar(app_handle: &tauri::AppHandle) {
    if let Some(state) = app_handle.try_state::<AppState>() {
        if let Ok(mut guard) = state.sidecar_child.lock() {
            if let Some(child) = guard.take() {
                let _ = child.kill();
            }
        }
    }
}

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_http::init())
        .setup(|app| {
            let port = pick_free_loopback_port()?;
            let session_token = generate_csprng_hex_32_bytes()?;
            let integrity_key = load_or_create_integrity_key()?;
            let port_str = port.to_string();

            let sidecar_cmd = app
                .shell()
                .sidecar("binaries/aegislps-backend")
                .map_err(|e| format!("Failed to configure sidecar command: {e}"))?
                .args(["--host", "127.0.0.1", "--port", &port_str])
                .env("AEGISLPS_HOST", "127.0.0.1")
                .env("AEGISLPS_PORT", &port_str)
                .env("AEGISLPS_SIDECAR_TOKEN", &session_token)
                .env("AEGISLPS_INTEGRITY_KEY", &integrity_key);

            // Drop local copy of integrity_key immediately after spawning sidecar.
            let (_rx, child) = sidecar_cmd
                .spawn()
                .map_err(|e| format!("Failed to launch sidecar process: {e}"))?;
            drop(integrity_key);

            let config = BackendConfig {
                base_url: format!("http://127.0.0.1:{port}"),
                token: session_token,
            };

            app.manage(AppState {
                config,
                sidecar_child: Mutex::new(Some(child)),
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_backend_config])
        .build(tauri::generate_context!())
        .expect("error while building AegisLPS desktop application");

    app.run(|app_handle, event| match event {
        RunEvent::ExitRequested { .. } | RunEvent::Exit => {
            terminate_sidecar(app_handle);
        }
        _ => {}
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn csprng_hex_is_64_chars_and_unique() {
        let a = generate_csprng_hex_32_bytes().expect("csprng a");
        let b = generate_csprng_hex_32_bytes().expect("csprng b");
        assert_eq!(a.len(), 64);
        assert_eq!(b.len(), 64);
        assert_ne!(a, b);
    }

    #[test]
    fn free_loopback_port_is_nonzero() {
        let port = pick_free_loopback_port().expect("loopback port");
        assert!(port > 0);
    }

    #[test]
    fn backend_config_debug_redacts_token() {
        let secret = generate_csprng_hex_32_bytes().expect("token");
        let cfg = BackendConfig {
            base_url: "http://127.0.0.1:9999".to_string(),
            token: secret.clone(),
        };
        let rendered = format!("{cfg:?}");
        assert!(!rendered.contains(&secret));
        assert!(rendered.contains("[REDACTED]"));
    }
}
