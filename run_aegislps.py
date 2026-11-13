#!/usr/bin/env python3
"""
AegisLPS Production & Local Application Launcher (Step 4.5, M10).
Runs pre-flight engineering diagnostics, starts the local FastAPI sidecar, and
reports readiness only after the HTTP health endpoint responds.
"""

from __future__ import annotations

import argparse
from collections import deque
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from typing import Callable, Deque, List, Optional, Sequence, Tuple
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

REQUIRED_CORE_DEPENDENCIES: tuple[Tuple[str, str], ...] = (
    ("pydantic", "pydantic"),
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("networkx", "networkx"),
)

REQUIRED_SERVER_DEPENDENCIES: tuple[Tuple[str, str], ...] = (
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("ezdxf", "ezdxf"),
    ("reportlab", "reportlab"),
    ("docx", "python-docx"),
)


def _repo_python_paths() -> List[str]:
    return [str(REPO_ROOT / rel) for rel in PACKAGE_REL_PATHS]


def ensure_repo_sys_path() -> None:
    for path_str in reversed(_repo_python_paths()):
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _venv_python_candidates(venv_dir: Path) -> Tuple[Path, ...]:
    if os.name == "nt":
        return (
            venv_dir / "Scripts" / "python.exe",
            venv_dir / "bin" / "python",
        )
    return (
        venv_dir / "bin" / "python",
        venv_dir / "Scripts" / "python.exe",
    )


def find_repo_venv_python(repo_root: Path = REPO_ROOT) -> Optional[Path]:
    """Locate an existing repo-local virtual environment Python executable if present."""
    for venv_name in (".venv", "venv"):
        venv_dir = repo_root / venv_name
        for candidate in _venv_python_candidates(venv_dir):
            if candidate.is_file():
                return candidate
    return None


def _platform_venv_python_hint() -> str:
    return r".venv\Scripts\python" if os.name == "nt" else ".venv/bin/python"


def check_missing_dependencies(
    *,
    include_server: bool,
    spec_finder: Callable[[str], object] = importlib.util.find_spec,
) -> List[str]:
    """Return pip package names for any required third-party modules missing from this Python."""
    checks = list(REQUIRED_CORE_DEPENDENCIES)
    if include_server:
        checks.extend(REQUIRED_SERVER_DEPENDENCIES)

    missing: List[str] = []
    for module_name, pip_name in checks:
        try:
            found = spec_finder(module_name)
        except (ImportError, ValueError):
            found = None
        if found is None and pip_name not in missing:
            missing.append(pip_name)
    return missing


def _print_missing_dependencies_help(missing_packages: Sequence[str]) -> None:
    venv_py = _platform_venv_python_hint()
    missing_csv = ", ".join(missing_packages)
    print(
        "\n[1/3] System Pre-Flight Diagnostics: MISSING DEPENDENCIES",
        flush=True,
    )
    print(
        f"ERROR: Required Python packages are not installed: {missing_csv}",
        flush=True,
    )
    print(f"  Active interpreter: {sys.executable}", flush=True)
    print(
        "\nCreate a virtual environment and install requirements:",
        flush=True,
    )
    print("  python -m venv .venv", flush=True)
    print(f"  {venv_py} -m pip install -r requirements.txt", flush=True)
    print(f"  {venv_py} run_aegislps.py", flush=True)
    print(
        "\nOr bootstrap .venv and launch in one command:",
        flush=True,
    )
    print("  python run_aegislps.py --bootstrap", flush=True)
    print("=" * 60, flush=True)


def bootstrap_repo_venv(
    forwarded_argv: Sequence[str],
    *,
    repo_root: Path = REPO_ROOT,
    run_cmd: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> int:
    """Create `.venv` if needed, install `requirements.txt`, and invoke `run_aegislps.py` inside it."""
    venv_dir = repo_root / ".venv"
    requirements_file = repo_root / "requirements.txt"
    if not requirements_file.is_file():
        print(
            f"ERROR: Cannot bootstrap dependencies; missing {requirements_file}.",
            flush=True,
        )
        return 1

    venv_python: Optional[Path] = None
    for candidate in _venv_python_candidates(venv_dir):
        if candidate.is_file():
            venv_python = candidate
            break

    if venv_python is None:
        print(f"[Bootstrap] Creating virtual environment at {venv_dir}...", flush=True)
        create_res = run_cmd([sys.executable, "-m", "venv", str(venv_dir)], check=False)
        if create_res.returncode != 0:
            print(
                f"ERROR: Failed to create virtual environment (exit code {create_res.returncode}).",
                flush=True,
            )
            return int(create_res.returncode) or 1
        for candidate in _venv_python_candidates(venv_dir):
            if candidate.is_file():
                venv_python = candidate
                break
        if venv_python is None:
            print(
                f"ERROR: Virtual environment created at {venv_dir}, but Python executable was not found.",
                flush=True,
            )
            return 1

    print(
        f"[Bootstrap] Installing dependencies from {requirements_file.name}...",
        flush=True,
    )
    install_res = run_cmd(
        [str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
        check=False,
    )
    if install_res.returncode != 0:
        print(
            f"ERROR: pip install failed (exit code {install_res.returncode}).",
            flush=True,
        )
        return int(install_res.returncode) or 1

    child_env = os.environ.copy()
    child_env["_AEGISLPS_VENV_REEXEC"] = "1"
    exec_res = run_cmd(
        [str(venv_python), str(repo_root / "run_aegislps.py"), *forwarded_argv],
        env=child_env,
        check=False,
    )
    return int(exec_res.returncode)


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
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Create .venv if needed, install requirements.txt, and run inside .venv.",
    )
    return parser.parse_args(argv)


def run_launcher(
    argv: Optional[Sequence[str]] = None,
    *,
    readiness_fn: Optional[Callable[[str], bool]] = None,
    popen_fn: Optional[Callable[..., subprocess.Popen]] = None,
    spec_finder: Callable[[str], object] = importlib.util.find_spec,
    startup_timeout_s: float = 20.0,
    poll_interval_s: float = 0.2,
    hold_until_interrupt: bool = True,
) -> int:
    effective_argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(effective_argv)

    if args.bootstrap:
        forwarded = [tok for tok in effective_argv if tok != "--bootstrap"]
        return bootstrap_repo_venv(forwarded)

    ensure_repo_sys_path()

    print("=" * 60, flush=True)
    print(" AegisLPS - Advanced Lightning Protection Engineering Suite", flush=True)
    print(" Version: 1.0.0-alpha.1 | Standards: IEC 62305:2024 Suite", flush=True)
    print("=" * 60, flush=True)

    # Pre-flight third-party dependency check before importing engine modules
    include_server_deps = (not args.no_server) and (popen_fn is None)
    missing_pkgs = check_missing_dependencies(
        include_server=include_server_deps,
        spec_finder=spec_finder,
    )
    if missing_pkgs:
        _print_missing_dependencies_help(missing_pkgs)
        return 1

    # 1. Run Internal Self-Test
    try:
        from aegislps_engine.diagnostics import SystemDiagnostics
    except ModuleNotFoundError as exc:
        missing_name = exc.name or str(exc)
        _print_missing_dependencies_help([missing_name])
        return 1

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


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    repo_root: Path = REPO_ROOT,
    run_cmd: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> None:
    effective_argv = list(sys.argv[1:] if argv is None else argv)
    if (
        "--bootstrap" not in effective_argv
        and os.environ.get("_AEGISLPS_VENV_REEXEC") != "1"
        and os.environ.get("_AEGISLPS_NO_VENV_REEXEC") != "1"
        and sys.prefix == sys.base_prefix
    ):
        venv_python = find_repo_venv_python(repo_root)
        if venv_python is not None:
            child_env = os.environ.copy()
            child_env["_AEGISLPS_VENV_REEXEC"] = "1"
            res = run_cmd(
                [str(venv_python), str(repo_root / "run_aegislps.py"), *effective_argv],
                env=child_env,
                check=False,
            )
            sys.exit(int(res.returncode))

    sys.exit(run_launcher(effective_argv))


if __name__ == "__main__":
    main()
