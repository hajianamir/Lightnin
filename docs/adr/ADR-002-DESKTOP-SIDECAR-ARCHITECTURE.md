# ADR-002: Tauri Desktop Wrapper with Local Python Service Sidecar

- **Status**: Approved
- **Date**: 2025-05-15
- **Deciders**: Desktop Engineer, Cybersecurity Engineer, System Architect

## Context
AegisLPS must operate as a native, offline-first Windows x64 desktop application without requiring internet connectivity or cloud servers.

## Decision
Use **Tauri** for native desktop window management and process orchestration, running a bundled Python backend service as a sidecar process communicating over restricted local loopback IPC/HTTP.

## Security Controls
1. Local REST API binds ONLY to `127.0.0.1` on a dynamically assigned local port.
2. Requests MUST include a single-use or session-scoped bearer token generated at sidecar startup by Tauri and passed via environment variable.
3. No external network interfaces are exposed.
