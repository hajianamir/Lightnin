#!/usr/bin/env python3
"""Build the Windows x64 PyInstaller one-file sidecar (`Step 5.3-B`, Owner Decision #2).

Target output:
    apps/desktop/src-tauri/binaries/aegislps-backend-x86_64-pc-windows-msvc.exe

Requirements:
    - Windows x64 runner (`sys.platform == "win32"`, `AMD64` / `x86_64`)
    - Python environment with `requirements.txt` and `pyinstaller` installed
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import platform
import subprocess
import sys
from typing import Callable, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_TRIPLE = "x86_64-pc-windows-msvc"
BINARY_STEM = f"aegislps-backend-{TARGET_TRIPLE}"
BINARIES_DIR = REPO_ROOT / "apps" / "desktop" / "src-tauri" / "binaries"
ENTRYPOINT = REPO_ROOT / "services" / "api" / "aegislps_api" / "sidecar_main.py"

PACKAGE_SEARCH_PATHS: tuple[str, ...] = (
    "packages/domain-model",
    "packages/geometry",
    "packages/reporting",
    "packages/standards-data",
    "services/calculation-engine",
    "services/api",
)


def build_pyinstaller_command(
    *,
    python_exe: str = sys.executable,
    repo_root: Path = REPO_ROOT,
) -> List[str]:
    binaries_dir = repo_root / "apps" / "desktop" / "src-tauri" / "binaries"
    work_dir = repo_root / "build" / "pyinstaller-work"
    spec_dir = repo_root / "build" / "pyinstaller-spec"
    entrypoint = repo_root / "services" / "api" / "aegislps_api" / "sidecar_main.py"

    cmd: List[str] = [
        python_exe,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        BINARY_STEM,
        "--distpath",
        str(binaries_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
        "--collect-data",
        "docx",
        "--collect-data",
        "ezdxf",
    ]
    for rel in PACKAGE_SEARCH_PATHS:
        cmd.extend(["--paths", str(repo_root / rel)])
    cmd.append(str(entrypoint))
    return cmd


def run_build(
    argv: Optional[Sequence[str]] = None,
    *,
    current_platform: Optional[str] = None,
    current_machine: Optional[str] = None,
    spec_finder: Callable[[str], object] = importlib.util.find_spec,
    run_cmd: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    repo_root: Path = REPO_ROOT,
) -> int:
    parser = argparse.ArgumentParser(
        description="Build the Windows x64 PyInstaller one-file sidecar for Tauri 2."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the PyInstaller command without executing it (runs on any OS).",
    )
    args = parser.parse_args(argv)

    cmd = build_pyinstaller_command(repo_root=repo_root)
    if args.dry_run:
        print(" ".join(cmd))
        return 0

    plat = sys.platform if current_platform is None else current_platform
    mach = (platform.machine() if current_machine is None else current_machine).lower()
    if plat != "win32" or mach not in {"amd64", "x86_64"}:
        print(
            f"ERROR: scripts/build_sidecar.py targets Windows x64 ({TARGET_TRIPLE}) only; "
            f"detected platform={plat!r}, machine={mach!r}. Run this script on a Windows x64 runner.",
            file=sys.stderr,
        )
        return 1

    if spec_finder("PyInstaller") is None:
        print(
            "ERROR: PyInstaller is not installed. Run `python -m pip install pyinstaller` first.",
            file=sys.stderr,
        )
        return 1

    binaries_dir = repo_root / "apps" / "desktop" / "src-tauri" / "binaries"
    binaries_dir.mkdir(parents=True, exist_ok=True)

    res = run_cmd(cmd, check=False)
    if res.returncode != 0:
        print(
            f"ERROR: PyInstaller exited with status {res.returncode}.",
            file=sys.stderr,
        )
        return int(res.returncode)

    expected_exe = binaries_dir / f"{BINARY_STEM}.exe"
    if not expected_exe.is_file():
        print(
            f"ERROR: Expected sidecar binary was not produced at {expected_exe}.",
            file=sys.stderr,
        )
        return 1

    print(f"Built sidecar binary: {expected_exe}")
    return 0


if __name__ == "__main__":
    sys.exit(run_build())
