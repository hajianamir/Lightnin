"""Step 4.2 — H12(b): Explicit CORS origins, methods, and headers; no wildcard or credentials."""

from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from aegislps_api.main import app

client = TestClient(app)

EXPECTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
]


def test_cors_preflight_allows_configured_origins_exact_echo() -> None:
    for origin in ("tauri://localhost", "http://localhost:5173", *EXPECTED_ORIGINS):
        resp = client.options(
            "/api/v1/calculations/separation-distance",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == origin
        assert resp.headers.get("access-control-allow-credentials") is None


def test_cors_disallowed_origin_receives_no_allow_origin_header() -> None:
    preflight = client.options(
        "/api/v1/calculations/separation-distance",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert "access-control-allow-origin" not in preflight.headers

    simple_get = client.get("/health", headers={"Origin": "https://evil.example"})
    assert simple_get.status_code == 200
    assert "access-control-allow-origin" not in simple_get.headers


def test_cors_responses_never_contain_wildcard_allow_origin() -> None:
    for origin in (*EXPECTED_ORIGINS, "https://evil.example", "null"):
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
