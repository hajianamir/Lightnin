"""Loopback-only entrypoint for the PyInstaller Windows x64 sidecar (`ADR-002`, Step 5.3-B)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Sequence

import uvicorn

from aegislps_api.main import app

ALLOWED_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost"})


def parse_sidecar_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AegisLPS loopback FastAPI sidecar process."
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("AEGISLPS_HOST", "127.0.0.1"),
        help="Loopback bind address (127.0.0.1 only per ADR-002).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AEGISLPS_PORT", "8000")),
        help="Loopback TCP port assigned by the desktop host.",
    )
    args = parser.parse_args(argv)
    if args.host not in ALLOWED_LOOPBACK_HOSTS:
        parser.error(
            f"ADR-002 violation: sidecar must bind only to loopback ({sorted(ALLOWED_LOOPBACK_HOSTS)}); got {args.host!r}."
        )
    if not (1 <= args.port <= 65535):
        parser.error(f"Invalid TCP port: {args.port}.")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_sidecar_args(argv)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        access_log=False,
        log_level="warning",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
