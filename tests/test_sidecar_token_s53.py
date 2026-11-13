"""Step 5.3-B — ADR-002 sidecar bearer-token enforcement & sidecar builder tests."""

from __future__ import annotations

import hmac
import io
import logging
from pathlib import Path
import secrets
import sys
from typing import List

import pytest
from fastapi.testclient import TestClient

import aegislps_api.main as api_main
from aegislps_api.main import SIDECAR_TOKEN_ENV_VAR, app
from aegislps_api.sidecar_main import parse_sidecar_args

REPO_ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)

VALID_EARTHING_PAYLOAD = {
    "lps_class": "I",
    "soil": {"rho_upper_ohm_m": 100.0},
    "electrode_type": "type_b_ring",
    "ring_radius_m": 10.0,
    "burial_depth_m": 0.5,
    "conductor_diameter_m": 0.01,
}


def test_token_set_missing_header_returns_401(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = secrets.token_hex(32)
    monkeypatch.setenv(SIDECAR_TOKEN_ENV_VAR, expected)

    resp = client.post("/api/v1/calculations/earthing", json=VALID_EARTHING_PAYLOAD)
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate") == "Bearer"
    assert expected not in resp.text

    # Unauthenticated request with empty body must also fail with 401 before 422
    resp_empty = client.post("/api/v1/calculations/separation-distance", json={})
    assert resp_empty.status_code == 401


def test_token_set_wrong_or_malformed_token_returns_401_without_leaking_token(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    expected = secrets.token_hex(32)
    wrong = secrets.token_hex(32)
    monkeypatch.setenv(SIDECAR_TOKEN_ENV_VAR, expected)

    with caplog.at_level(logging.DEBUG):
        resp_wrong = client.post(
            "/api/v1/calculations/earthing",
            json=VALID_EARTHING_PAYLOAD,
            headers={"Authorization": f"Bearer {wrong}"},
        )
        resp_basic = client.post(
            "/api/v1/calculations/earthing",
            json=VALID_EARTHING_PAYLOAD,
            headers={"Authorization": f"Basic {expected}"},
        )
        resp_blank = client.post(
            "/api/v1/calculations/earthing",
            json=VALID_EARTHING_PAYLOAD,
            headers={"Authorization": "Bearer "},
        )

    assert resp_wrong.status_code == 401
    assert resp_basic.status_code == 401
    assert resp_blank.status_code == 401
    for r in (resp_wrong, resp_basic, resp_blank):
        assert expected not in r.text
        assert wrong not in r.text
    assert expected not in caplog.text
    assert wrong not in caplog.text


def test_token_set_correct_token_returns_200_and_uses_constant_time_compare(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    expected = secrets.token_hex(32)
    monkeypatch.setenv(SIDECAR_TOKEN_ENV_VAR, expected)

    compare_calls: List[int] = []
    real_compare = hmac.compare_digest

    def _spy_compare(a, b) -> bool:
        compare_calls.append(1)
        return real_compare(a, b)

    monkeypatch.setattr(api_main.hmac, "compare_digest", _spy_compare)

    with caplog.at_level(logging.DEBUG):
        resp = client.post(
            "/api/v1/calculations/earthing",
            json=VALID_EARTHING_PAYLOAD,
            headers={"Authorization": f"Bearer {expected}"},
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "PASS"
    assert len(compare_calls) == 1
    assert expected not in resp.text
    assert expected not in caplog.text


def test_token_unset_succeeds_and_health_is_unauthenticated_in_both_modes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 1. Token unset -> /api/v1/* and /health both return 200 without Authorization header
    monkeypatch.delenv(SIDECAR_TOKEN_ENV_VAR, raising=False)
    resp_api_unset = client.post(
        "/api/v1/calculations/earthing", json=VALID_EARTHING_PAYLOAD
    )
    assert resp_api_unset.status_code == 200

    resp_health_unset = client.get("/health")
    assert resp_health_unset.status_code == 200
    assert resp_health_unset.json()["status"] == "ok"

    # 2. Token set -> /health still returns 200 without Authorization header
    monkeypatch.setenv(SIDECAR_TOKEN_ENV_VAR, secrets.token_hex(32))
    resp_health_set = client.get("/health")
    assert resp_health_set.status_code == 200
    assert resp_health_set.json()["status"] == "ok"


def test_launcher_dev_mode_leaves_token_unset_unless_provided(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.append(str(REPO_ROOT))
    import run_aegislps

    captured_envs: List[dict] = []

    class _DummyChild:
        def __init__(self, cmd, **kwargs) -> None:
            captured_envs.append(dict(kwargs["env"]))
            self.stdout = io.StringIO("")
            self.stderr = io.StringIO("")
            self._rc = None

        def poll(self):
            return self._rc

        def terminate(self) -> None:
            self._rc = 0

        def kill(self) -> None:
            self._rc = -9

        def wait(self, timeout=None) -> int:
            self._rc = 0
            return 0

    # Dev mode (unset): launcher must NOT fabricate AEGISLPS_SIDECAR_TOKEN
    monkeypatch.delenv(SIDECAR_TOKEN_ENV_VAR, raising=False)
    rc_unset = run_aegislps.run_launcher(
        [],
        popen_fn=_DummyChild,
        readiness_fn=lambda _url: True,
        hold_until_interrupt=False,
    )
    assert rc_unset == 0
    assert SIDECAR_TOKEN_ENV_VAR not in captured_envs[-1]
    capsys.readouterr()

    # Provided mode: launcher passes token through to child env and never prints it
    provided_tok = secrets.token_hex(32)
    monkeypatch.setenv(SIDECAR_TOKEN_ENV_VAR, provided_tok)
    rc_set = run_aegislps.run_launcher(
        [],
        popen_fn=_DummyChild,
        readiness_fn=lambda _url: True,
        hold_until_interrupt=False,
    )
    captured_io = capsys.readouterr()
    assert rc_set == 0
    assert captured_envs[-1][SIDECAR_TOKEN_ENV_VAR] == provided_tok
    assert provided_tok not in captured_io.out
    assert provided_tok not in captured_io.err


def test_sidecar_entrypoint_and_build_script_target_triple_and_guards(
    capsys: pytest.CaptureFixture[str],
) -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.append(str(REPO_ROOT))
    from scripts import build_sidecar

    # Loopback enforcement in sidecar_main
    parsed = parse_sidecar_args(["--host", "127.0.0.1", "--port", "54321"])
    assert parsed.host == "127.0.0.1"
    assert parsed.port == 54321

    with pytest.raises(SystemExit):
        parse_sidecar_args(["--host", "0.0.0.0", "--port", "8000"])

    # Dry-run verifies exact target-triple binary name & PyInstaller flags
    rc_dry = build_sidecar.run_build(["--dry-run"])
    dry_out = capsys.readouterr().out
    assert rc_dry == 0
    assert "--onefile" in dry_out
    assert "aegislps-backend-x86_64-pc-windows-msvc" in dry_out

    # Non-Windows platform guard exits nonzero cleanly
    rc_linux = build_sidecar.run_build(
        [], current_platform="linux", current_machine="x86_64"
    )
    err_out = capsys.readouterr().err
    assert rc_linux == 1
    assert "Windows x64" in err_out
