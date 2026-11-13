"""Step 4.5 — M10: Launcher reports server readiness only after a real start and health check."""

from __future__ import annotations

import importlib
import io
import socket
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _find_free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class _FakeDummyPopen:
    """Lightweight child-process stand-in for testing readiness ordering without real sockets."""

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs
        self.stdout = io.StringIO("")
        self.stderr = io.StringIO("")
        self._returncode: int | None = None
        self.terminated = False

    def poll(self) -> int | None:
        return self._returncode

    def terminate(self) -> None:
        self.terminated = True
        self._returncode = 0

    def kill(self) -> None:
        self.terminated = True
        self._returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        if self._returncode is None:
            self._returncode = 0
        return self._returncode


def _ensure_fallback_repo_root() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.append(str(REPO_ROOT))


def test_import_run_aegislps_has_no_side_effects(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    popen_calls: List[tuple] = []
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **kw: popen_calls.append((a, kw))
    )

    _ensure_fallback_repo_root()

    if "run_aegislps" in sys.modules:
        mod = importlib.reload(sys.modules["run_aegislps"])
    else:
        mod = importlib.import_module("run_aegislps")

    out = capsys.readouterr().out
    assert popen_calls == []
    assert out == ""
    assert hasattr(mod, "run_launcher")


def test_no_server_flag_prints_manual_command_and_not_started_without_ready_claim(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _ensure_fallback_repo_root()
    import run_aegislps

    rc = run_aegislps.run_launcher(["--no-server"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "NOT started" in out
    assert "uvicorn aegislps_api.main:app --host 127.0.0.1 --port 8000" in out
    assert "npm run dev --workspace=apps/web" in out
    assert "Ready on" not in out
    assert "Ready for" not in out
    assert "running" not in out.lower()


def test_failed_server_start_exits_nonzero_prints_stderr_and_never_prints_ready(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _ensure_fallback_repo_root()
    import run_aegislps

    port = _find_free_tcp_port()
    monkeypatch.setenv("AEGISLPS_PORT", str(port))
    monkeypatch.setenv("AEGISLPS_ASGI_APP", "nonexistent_step45_module.main:app")

    rc = run_aegislps.run_launcher(
        [], startup_timeout_s=8.0, poll_interval_s=0.1, hold_until_interrupt=False
    )
    out = capsys.readouterr().out

    assert rc != 0
    assert "ERROR:" in out
    assert "nonexistent_step45_module" in out
    assert "Ready on" not in out
    assert "Ready for" not in out


def test_readiness_timeout_terminates_child_and_never_prints_ready(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _ensure_fallback_repo_root()
    import run_aegislps

    created: List[_FakeDummyPopen] = []

    def _spawn(*args, **kwargs):
        proc = _FakeDummyPopen(*args, **kwargs)
        proc.stderr = io.StringIO("simulated bind stall on port\n")
        created.append(proc)
        return proc

    rc = run_aegislps.run_launcher(
        [],
        readiness_fn=lambda _url: False,
        popen_fn=_spawn,
        startup_timeout_s=0.35,
        poll_interval_s=0.05,
        hold_until_interrupt=False,
    )
    out = capsys.readouterr().out

    assert rc != 0
    assert len(created) == 1 and created[0].terminated is True
    assert "simulated bind stall on port" in out
    assert "Ready on" not in out
    assert "Ready for" not in out


def test_ready_line_printed_only_after_readiness_check_succeeds(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _ensure_fallback_repo_root()
    import run_aegislps

    created: List[_FakeDummyPopen] = []
    probe_snapshots_before_true: List[str] = []
    accumulated_stdout: List[str] = []

    def _spawn(*args, **kwargs):
        assert kwargs.get("shell") in (None, False)
        proc = _FakeDummyPopen(*args, **kwargs)
        created.append(proc)
        return proc

    attempts = {"count": 0}

    def _probe(url: str) -> bool:
        assert url == "http://127.0.0.1:8000/health"
        chunk = capsys.readouterr().out
        accumulated_stdout.append(chunk)
        so_far = "".join(accumulated_stdout)
        # At the instant the readiness check executes, Ready text MUST NOT have been printed yet!
        probe_snapshots_before_true.append(so_far)
        assert "Ready on http://127.0.0.1:8000" not in so_far
        assert "Ready for" not in so_far
        attempts["count"] += 1
        return attempts["count"] >= 2

    rc = run_aegislps.run_launcher(
        [],
        readiness_fn=_probe,
        popen_fn=_spawn,
        startup_timeout_s=5.0,
        poll_interval_s=0.02,
        hold_until_interrupt=False,
    )
    tail_out = capsys.readouterr().out
    accumulated_stdout.append(tail_out)

    assert rc == 0
    assert attempts["count"] == 2
    assert len(probe_snapshots_before_true) == 2
    assert "Local Calculation Engine Ready on http://127.0.0.1:8000" in tail_out
    assert "Ready for Engineering Workflow" in tail_out
    assert "NOT started by this launcher" in tail_out
    assert len(created) == 1 and created[0].terminated is True


def test_real_server_launch_and_clean_child_termination(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _ensure_fallback_repo_root()
    import run_aegislps

    port = _find_free_tcp_port()
    monkeypatch.setenv("AEGISLPS_PORT", str(port))

    rc = run_aegislps.run_launcher(
        [], startup_timeout_s=15.0, poll_interval_s=0.15, hold_until_interrupt=False
    )
    out = capsys.readouterr().out

    assert rc == 0
    assert f"Local Calculation Engine Ready on http://127.0.0.1:{port}" in out
    # After run_launcher returns, child uvicorn must be terminated (port no longer responding)
    assert run_aegislps.check_server_readiness(f"http://127.0.0.1:{port}/health") is False
