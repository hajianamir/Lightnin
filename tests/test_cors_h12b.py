"""Step 4.2 & Step 5.3-D — H12(b): Explicit CORS origins matching Tauri 2 (`useHttpsScheme: false`)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from aegislps_api.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)

EXPECTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "tauri://localhost",
    "http://tauri.localhost",
]


def test_cors_preflight_allows_configured_origins_exact_echo() -> None:
    for origin in ("tauri://localhost", "http://localhost:5173", *EXPECTED_ORIGINS):
        resp = client.options(
            "/api/v1/calculations/separation-distance",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == origin
        assert resp.headers.get("access-control-allow-credentials") is None


def test_cors_disallowed_origins_including_unused_https_tauri_receive_no_header() -> None:
    tauri_cfg = json.loads(
        (REPO_ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").read_text(
            encoding="utf-8"
        )
    )
    assert tauri_cfg["app"]["windows"][0]["useHttpsScheme"] is False

    for disallowed in ("https://evil.example", "https://tauri.localhost"):
        preflight = client.options(
            "/api/v1/calculations/separation-distance",
            headers={
                "Origin": disallowed,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert "access-control-allow-origin" not in preflight.headers

        simple_get = client.get("/health", headers={"Origin": disallowed})
        assert simple_get.status_code == 200
        assert "access-control-allow-origin" not in simple_get.headers


def test_cors_responses_never_contain_wildcard_allow_origin() -> None:
    for origin in (*EXPECTED_ORIGINS, "https://evil.example", "https://tauri.localhost", "null"):
        r_opt = client.options(
            "/api/v1/calculations/separation-distance",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert r_opt.headers.get("access-control-allow-origin") != "*"

        r_get = client.get("/health", headers={"Origin": origin})
        assert r_get.headers.get("access-control-allow-origin") != "*"


def test_cors_middleware_config_has_no_wildcard_or_credentials() -> None:
    cors_middlewares = [
        m for m in app.user_middleware if m.cls is CORSMiddleware
    ]
    assert len(cors_middlewares) == 1
    kwargs = cors_middlewares[0].kwargs

    assert kwargs.get("allow_credentials") is False
    assert "*" not in kwargs.get("allow_origins", [])
    assert "*" not in kwargs.get("allow_methods", [])
    assert "*" not in kwargs.get("allow_headers", [])
    assert list(kwargs.get("allow_origins", [])) == EXPECTED_ORIGINS
    assert list(kwargs.get("allow_methods", [])) == ["GET", "POST", "OPTIONS"]
    assert list(kwargs.get("allow_headers", [])) == ["Content-Type", "Authorization"]
