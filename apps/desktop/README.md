# AegisLPS Desktop Wrapper (Tauri 2 + Windows x64 Python Sidecar)

## Architecture & Security Controls (`ADR-002`)

1. **Pinned Tauri 2.x**:
   - CLI: `@tauri-apps/cli@2.12.4` (`apps/desktop/package.json`)
   - Rust crates: `tauri = "=2.12.5"`, `tauri-build = "=2.7.4"`, `tauri-plugin-shell = "=2.6.0"`, `tauri-plugin-http = "=2.9.0"`, `keyring = "=3.6.3"` (`apps/desktop/src-tauri/Cargo.toml`).
2. **Dynamic Loopback Port & Session Bearer Token**:
   - On launch, the Rust host binds `127.0.0.1:0` to select a free ephemeral loopback port, generates a 32-byte CSPRNG session token, spawns `binaries/aegislps-backend` on `127.0.0.1:<port>` with `AEGISLPS_SIDECAR_TOKEN`, and exposes `get_backend_config` returning `{ baseUrl, token }` to the WebView.
   - `/health` remains unauthenticated; every `/api/v1/*` route enforces `Authorization: Bearer <token>` via constant-time `hmac.compare_digest` when `AEGISLPS_SIDECAR_TOKEN` is set.
3. **Per-Installation Project Integrity Key (`AEGISLPS_INTEGRITY_KEY`)**:
   - On first launch, the Rust host generates 32 CSPRNG bytes (`64` hex UTF-8 bytes) and stores them in **Windows Credential Manager** (`service = "org.aegislps.desktop"`, `account = "project_integrity_hmac_key"`).
   - On subsequent launches, the stored key is retrieved from Windows Credential Manager and passed exclusively to the sidecar process environment (`AEGISLPS_INTEGRITY_KEY`). It is never written to logs, files, or returned to the frontend.
   - **Portability limitation**: Because the HMAC key is unique to each Windows installation's Credential Manager entry, `.lps` project checksums verify only on the installation that created them.

## Building on a Windows x64 Runner

1. **Build the PyInstaller one-file sidecar (`x86_64-pc-windows-msvc`)**:
   ```powershell
   python -m pip install -r requirements.txt pyinstaller
   python scripts/build_sidecar.py
   ```
   Produces `apps/desktop/src-tauri/binaries/aegislps-backend-x86_64-pc-windows-msvc.exe` (ignored by Git; never commit binaries).

2. **Generate/verify `Cargo.lock` and run Rust host unit tests**:
   ```powershell
   cd apps/desktop/src-tauri
   cargo generate-lockfile
   cargo test --locked
   cd ../../..
   ```

3. **Build the Tauri 2 Windows bundle**:
   ```powershell
   npm install
   npm run build --workspace=apps/desktop
   ```

## Manual Credential Manager Verification (Windows 11)

1. Launch the built AegisLPS desktop executable once.
2. Open **Control Panel -> User Accounts -> Credential Manager -> Windows Credentials** and confirm an entry named `org.aegislps.desktop` (`project_integrity_hmac_key`) exists.
3. Call `/api/v1/projects/compute-checksum` via the app, restart the app, and confirm the identical project payload produces the same 64-character hex HMAC-SHA256 digest without any key material appearing in stdout/stderr logs.
