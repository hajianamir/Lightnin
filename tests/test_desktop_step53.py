"""Step 5.3 — M9 & linked desktop configuration / H11 key-forwarding checks."""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
from typing import Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TAURI_CONF_PATH = REPO_ROOT / "apps" / "desktop" / "tauri.conf.json"


def _load_tauri_conf() -> Dict:
    return json.loads(TAURI_CONF_PATH.read_text(encoding="utf-8"))


def _parse_csp_directives(csp: str) -> Dict[str, list[str]]:
    directives: Dict[str, list[str]] = {}
    for raw_part in csp.split(";"):
        part = raw_part.strip()
        if not part:
            continue
        tokens = part.split()
        directives[tokens[0]] = tokens[1:]
    return directives


def test_tauri_conf_dev_vs_dist_and_narrowed_http_allowlist() -> None:
    cfg = _load_tauri_conf()

    assert cfg["build"]["devPath"] == "http://localhost:5173"
    assert cfg["build"]["distDir"] == "../web/dist"

    allowlist = cfg["tauri"]["allowlist"]
    assert allowlist["all"] is False
    http_cfg = allowlist["http"]
    assert http_cfg["all"] is False
    assert http_cfg["request"] is True

    scopes = http_cfg["scope"]
    assert len(scopes) > 0
    for pattern in scopes:
        assert ":*" not in pattern
        assert pattern.startswith(
            ("http://127.0.0.1:8000/", "http://localhost:8000/")
        )


def test_tauri_conf_csp_has_no_unsafe_eval_and_no_inline_scripts() -> None:
    cfg = _load_tauri_conf()
    csp = cfg["tauri"]["security"]["csp"]

    assert "unsafe-eval" not in csp
    assert ":*" not in csp

    directives = _parse_csp_directives(csp)
    assert directives["default-src"] == ["'self'"]
    assert directives["script-src"] == ["'self'"]
    assert "'unsafe-inline'" not in directives["default-src"]
    assert "'unsafe-inline'" not in directives["script-src"]
    # Retained strictly on style-src because apps/web/index.html uses <body style="...">
    assert "'unsafe-inline'" in directives["style-src"]
    assert set(directives["connect-src"]) == {
        "'self'",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    }


def test_launcher_forwards_integrity_key_to_sidecar_env_without_logging_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.append(str(REPO_ROOT))
    import run_aegislps

    secret_value = "step53-super-secret-hmac-key-material-do-not-log-998877"
    monkeypatch.setenv("AEGISLPS_INTEGRITY_KEY", secret_value)

    captured_envs: list[dict] = []
    captured_cmds: list[list[str]] = []

    class _DummyChild:
        def __init__(self, cmd, **kwargs) -> None:
            captured_cmds.append(list(cmd))
            captured_envs.append(dict(kwargs["env"]))
            self.stdout = io.StringIO("")
            self.stderr = io.StringIO("simulated startup exit\n")
            self._rc = 1

        def poll(self):
            return self._rc

        def terminate(self) -> None:
            pass

        def kill(self) -> None:
            pass

        def wait(self, timeout=None) -> int:
            return self._rc

    rc = run_aegislps.run_launcher(
        [],
        popen_fn=_DummyChild,
        readiness_fn=lambda _url: False,
        startup_timeout_s=0.5,
        poll_interval_s=0.05,
        hold_until_interrupt=False,
    )
    io_captured = capsys.readouterr()

    assert rc == 1
    assert len(captured_envs) == 1
    # ADR-002 Control 1: default bind host is loopback 127.0.0.1
    assert "--host" in captured_cmds[0]
    host_idx = captured_cmds[0].index("--host") + 1
    assert captured_cmds[0][host_idx] == "127.0.0.1"
    # H11 / Step 5.3(e): key reaches child process via environment and is never logged
    assert captured_envs[0]["AEGISLPS_INTEGRITY_KEY"] == secret_value
    assert secret_value not in io_captured.out
    assert secret_value not in io_captured.err
