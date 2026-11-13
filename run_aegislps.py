#!/usr/bin/env python3
"""
AegisLPS Production & Local Application Launcher (Step 4.5, M10).
Runs pre-flight engineering diagnostics, starts the local FastAPI sidecar, and
reports readiness only after the HTTP health endpoint responds.
"""

from __future__ import annotations

import argparse
from collections import deque
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from typing import Callable, Deque, List, Optional, Sequence
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parent
PACKAGE_REL_PATHS: tuple[str, ...] = (
    "packages/domain-model",
    "packages/geometry",
    "packages/reporting",
    "packages/standards-data",
    "services/calculation-engine",
    "services/api",
)


def _repo_python_paths() -> List[str]:
    return [str(REPO_ROOT / rel) for rel in PACKAGE_REL_PATHS]


def ensure_repo_sys_path() -> None:
    for path_str in reversed(_repo_python_paths()):
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _build_child_env() -> dict[str, str]:
    env = os.environ.copy()
    repo_paths = _repo_python_paths()
    existing = env.get("PYTHONPATH", "")
    combined = repo_paths + ([existing] if existing else [])
    env["PYTHONPATH"] = os.pathsep.join(combined)
    return env


def check_server_readiness(health_url: str, request_timeout_s: float = 1.0) -> bool:
    """Return True iff GET `health_url` returns HTTP 200 with JSON status 'ok'."""
    req = urllib.request.Request(health_url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=request_timeout_s) as resp:
            if resp.status != 200:
                return False
            payload = json.loads(resp.read().decode("utf-8"))
            return isinstance(payload, dict) and payload.get("status") == "ok"
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ):
        return False


def _start_stream_drain(stream, tail_buffer: Deque[str]) -> threading.Thread:
    def _reader() -> None:
        if stream is None:
            return
        try:
            for line in iter(stream.readline, ""):
                stripped = line.rstrip("\r\n")
                if stripped:
                    tail_buffer.append(stripped)
        except ValueError:
            pass

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    return thread


def _terminate_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2.0)


def _format_stderr_tail(stderr_tail: Deque[str]) -> str:
    if not stderr_tail:
        return "  (no stderr output captured)"
    return "\n".join(f"  {line}" for line in stderr_tail)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AegisLPS pre-flight diagnostics and local API server launcher."
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Run self-test diagnostics only; do not start the local API server.",
    )
    return parser.parse_args(argv)


def run_launcher(
    argv: Optional[Sequence[str]] = None,
    *,
    readiness_fn: Optional[Callable[[str], bool]] = None,
    popen_fn: Optional[Callable[..., subprocess.Popen]] = None,
    startup_timeout_s: float = 20.0,
    poll_interval_s: float = 0.2,
    hold_until_interrupt: bool = True,
) -> int:
    args = parse_args(argv)
    ensure_repo_sys_path()

    print("=" * 60, flush=True)
    print(" AegisLPS - Advanced Lightning Protection Engineering Suite", flush=True)
    print(" Version: 1.0.0-alpha.1 | Standards: IEC 62305:2024 Suite", flush=True)
    print("=" * 60, flush=True)

    # 1. Run Internal Self-Test
    from aegislps_engine.diagnostics import SystemDiagnostics

    diag = SystemDiagnostics.run_self_test()
    print(f"\n[1/3] System Pre-Flight Diagnostics: {diag['system_status']}", flush=True)
    for k, v in diag["tests"].items():
        print(
            f"  • {k.replace('_', ' ').title()}: [{v['status']}] {v['message']}",
            flush=True,
        )

    if diag["system_status"] != "OPERATIONAL":
        print("ERROR: Self-test failed. Please inspect dependencies.", flush=True)
        return 1

    host = os.environ.get("AEGISLPS_HOST", "127.0.0.1")
    port = int(os.environ.get("AEGISLPS_PORT", "8000"))
    app_target = os.environ.get("AEGISLPS_ASGI_APP", "aegislps_api.main:app")

    if args.no_server:
        print(
            "\n[2/3] API server was NOT started (--no-server requested).",
            flush=True,
        )
        print("  Manual command to start API backend:", flush=True)
        print(f"    uvicorn {app_target} --host {host} --port {port}", flush=True)
        print(
            "\n[3/3] Web frontend was NOT started (manual step):",
            flush=True,
        )
        print("    npm run dev --workspace=apps/web", flush=True)
        print("=" * 60, flush=True)
        return 0

    probe = readiness_fn if readiness_fn is not None else check_server_readiness
    spawn = popen_fn if popen_fn is not None else subprocess.Popen
    health_url = f"http://{host}:{port}/health"

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        app_target,
        "--host",
        host,
        "--port",
        str(port),
    ]

    print(
        f"\n[2/3] Starting local API server ({host}:{port}) and polling {health_url}...",
        flush=True,
    )

    stderr_tail: Deque[str] = deque(maxlen=40)
    stdout_tail: Deque[str] = deque(maxlen=40)
    proc = spawn(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_build_child_env(),
    )
    err_thread = _start_stream_drain(proc.stderr, stderr_tail)
    out_thread = _start_stream_drain(proc.stdout, stdout_tail)

    previous_sigterm = signal.getsignal(signal.SIGTERM)
    previous_sigint = signal.getsignal(signal.SIGINT)

    def _handle_stop_signal(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _handle_stop_signal)
        signal.signal(signal.SIGINT, _handle_stop_signal)
    except ValueError:
        # Not in main thread during certain test invocations
        previous_sigterm = None
        previous_sigint = None

    try:
        deadline = time.monotonic() + startup_timeout_s
        ready = False
        while time.monotonic() < deadline:
            exit_code = proc.poll()
            if exit_code is not None:
                err_thread.join(timeout=1.0)
                print(
                    f"ERROR: API server exited prematurely (code {exit_code}) before passing health check.",
                    flush=True,
                )
                print("Last server stderr lines:", flush=True)
                print(_format_stderr_tail(stderr_tail), flush=True)
                return 1

            if probe(health_url):
                ready = True
                break

            time.sleep(poll_interval_s)

        if not ready:
            _terminate_process(proc)
            err_thread.join(timeout=1.0)
            print(
                f"ERROR: Timed out after {startup_timeout_s:.1f}s waiting for API health check at {health_url}.",
                flush=True,
            )
            print("Last server stderr lines:", flush=True)
            print(_format_stderr_tail(stderr_tail), flush=True)
            return 1

        print(
            f"[2/3] Local Calculation Engine Ready on http://{host}:{port}",
            flush=True,
        )
        print(
            "[3/3] Ready for Engineering Workflow & Field Operation.",
            flush=True,
        )
        print(
            "\nWeb Frontend (manual step — NOT started by this launcher):",
            flush=True,
        )
        print("  npm run dev --workspace=apps/web", flush=True)
        print("Press Ctrl+C to stop the local API server.", flush=True)
        print("=" * 60, flush=True)

        if hold_until_interrupt:
            try:
                proc.wait()
            except KeyboardInterrupt:
                print("\nStopping local API server...", flush=True)
        return 0
    finally:
        _terminate_process(proc)
        err_thread.join(timeout=1.0)
        out_thread.join(timeout=1.0)
        if proc.stderr is not None:
            proc.stderr.close()
        if proc.stdout is not None:
            proc.stdout.close()
        if previous_sigterm is not None:
            try:
                signal.signal(signal.SIGTERM, previous_sigterm)
            except ValueError:
                pass
        if previous_sigint is not None:
            try:
                signal.signal(signal.SIGINT, previous_sigint)
            except ValueError:
                pass


def main(argv: Optional[Sequence[str]] = None) -> None:
    sys.exit(run_launcher(argv))


if __name__ == "__main__":
    main()
