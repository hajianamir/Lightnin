"""Step 5.3 — Tauri 2 configuration, capabilities, version pins, and H11 key-forwarding checks."""

from __future__ import annotations

import io
import json
from pathlib import Path
import re
import secrets
import sys
from typing import Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_TAURI_CONF_PATH = REPO_ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
LEGACY_DESKTOP_CONF_PATH = REPO_ROOT / "apps" / "desktop" / "tauri.conf.json"
CAPABILITY_PATH = (
    REPO_ROOT / "apps" / "desktop" / "src-tauri" / "capabilities" / "default.json"
)
DESKTOP_PKG_JSON_PATH = REPO_ROOT / "apps" / "desktop" / "package.json"
CARGO_TOML_PATH = REPO_ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"


def _parse_csp_directives(csp: str) -> Dict[str, list[str]]:
    directives: Dict[str, list[str]] = {}
    for raw_part in csp.split(";"):
        part = raw_part.strip()
        if not part:
            continue
        tokens = part.split()
        directives[tokens[0]] = tokens[1:]
    return directives


@pytest.mark.parametrize(
    "conf_path,expected_dist",
    [
        (SRC_TAURI_CONF_PATH, "../../web/dist"),
        (LEGACY_DESKTOP_CONF_PATH, "../web/dist"),
    ],
)
def test_tauri_v2_conf_layout_csp_and_no_v1_allowlist(
    conf_path: Path, expected_dist: str
) -> None:
    cfg = json.loads(conf_path.read_text(encoding="utf-8"))

    assert cfg["$schema"] == "https://schema.tauri.app/config/2"
    assert "tauri" not in cfg
    assert "package" not in cfg
    assert "allowlist" not in cfg
    assert "allowlist" not in cfg.get("app", {})

    assert cfg["productName"] == "AegisLPS"
    assert cfg["identifier"] == "org.aegislps.app"
    assert cfg["build"]["devUrl"] == "http://localhost:5173"
    assert cfg["build"]["frontendDist"] == expected_dist
    assert cfg["bundle"]["externalBin"] == ["binaries/aegislps-backend"]

    main_win = cfg["app"]["windows"][0]
    assert main_win["label"] == "main"
    assert main_win["useHttpsScheme"] is False

    security = cfg["app"]["security"]
    assert security["capabilities"] == ["default"]

    csp = security["csp"]
    assert "unsafe-eval" not in csp
    directives = _parse_csp_directives(csp)
    assert directives["default-src"] == ["'self'"]
    assert directives["script-src"] == ["'self'"]
    assert "'unsafe-inline'" not in directives["default-src"]
    assert "'unsafe-inline'" not in directives["script-src"]
    assert directives["style-src"] == ["'self'", "'unsafe-inline'"]
    assert set(directives["connect-src"]) == {
        "'self'",
        "http://127.0.0.1:*",
        "http://localhost:*",
    }


def test_tauri_v2_capability_grants_only_get_backend_config_and_loopback_http() -> None:
    cap = json.loads(CAPABILITY_PATH.read_text(encoding="utf-8"))
    assert cap["identifier"] == "default"
    assert cap["windows"] == ["main"]

    perms = cap["permissions"]
    assert perms == [
        "allow-get-backend-config",
        {
            "identifier": "http:default",
            "allow": [
                {"url": "http://127.0.0.1:*/*"},
                {"url": "http://localhost:*/*"},
            ],
        },
    ]


def test_tauri_cli_and_crate_versions_are_pinned_exactly() -> None:
    pkg = json.loads(DESKTOP_PKG_JSON_PATH.read_text(encoding="utf-8"))
    cli_ver = pkg["devDependencies"]["@tauri-apps/cli"]
    assert re.fullmatch(r"2\.\d+\.\d+", cli_ver), f"Expected exact 2.x.y pin, got {cli_ver!r}"

    cargo_toml = CARGO_TOML_PATH.read_text(encoding="utf-8")
    assert re.search(r'^tauri\s*=\s*\{\s*version\s*=\s*"=2\.\d+\.\d+"', cargo_toml, re.M)
    assert re.search(
        r'^tauri-build\s*=\s*\{\s*version\s*=\s*"=2\.\d+\.\d+"', cargo_toml, re.M
    )
    assert re.search(r'^keyring\s*=\s*\{\s*version\s*=\s*"=3\.\d+\.\d+"', cargo_toml, re.M)


def test_launcher_forwards_integrity_key_to_sidecar_env_without_logging_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.append(str(REPO_ROOT))
    import run_aegislps

    runtime_key = secrets.token_hex(32)
    monkeypatch.setenv("AEGISLPS_INTEGRITY_KEY", runtime_key)

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
    assert "--host" in captured_cmds[0]
    host_idx = captured_cmds[0].index("--host") + 1
    assert captured_cmds[0][host_idx] == "127.0.0.1"
    assert captured_envs[0]["AEGISLPS_INTEGRITY_KEY"] == runtime_key
    assert runtime_key not in io_captured.out
    assert runtime_key not in io_captured.err
