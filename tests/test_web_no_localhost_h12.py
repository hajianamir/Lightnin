"""Step 4.1 — H12(a): Browser code under apps/web/src must not hard-code localhost,
127.0.0.1, or absolute http(s):// URLs in fetch calls.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEB_SRC = REPO_ROOT / "apps" / "web" / "src"

_LOOPBACK_RE = re.compile(r"(localhost|127\.0\.0\.1)", re.IGNORECASE)
# Step 5.3-C: App.tsx routes requests through `apiFetch('/api/v1/...')`, which
# delegates to `fetch(...)` using relative paths outside Tauri and `get_backend_config` inside Tauri.
_FETCH_ARG_RE = re.compile(r"\b(?:apiFetch|fetch)\s*\(\s*([`'\"])(.*?)\1", re.DOTALL)


def _resolve_web_src() -> Path:
    override = os.environ.get("AEGISLPS_TEST_WEB_SRC_DIR")
    return Path(override) if override else DEFAULT_WEB_SRC


def _iter_source_files(web_src: Path) -> List[Path]:
    assert web_src.is_dir(), f"Expected web source directory at {web_src}"
    files = sorted(p for p in web_src.rglob("*") if p.is_file())
    assert files, f"No source files found under {web_src}"
    return files


def test_web_src_contains_no_localhost_or_127_0_0_1() -> None:
    web_src = _resolve_web_src()
    offenders: List[str] = []
    for path in _iter_source_files(web_src):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _LOOPBACK_RE.search(line):
                rel = path.relative_to(web_src)
                offenders.append(f"{rel}:{lineno}: {line.strip()}")

    assert not offenders, (
        "Browser source under apps/web/src must not reference localhost or 127.0.0.1:\n  "
        + "\n  ".join(offenders)
    )


def test_web_src_fetch_calls_use_relative_paths_without_http_scheme() -> None:
    web_src = _resolve_web_src()
    fetch_urls: List[Tuple[str, int, str]] = []
    absolute_offenders: List[str] = []

    for path in _iter_source_files(web_src):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(web_src))
        for match in _FETCH_ARG_RE.finditer(text):
            url = match.group(2).strip()
            lineno = text.count("\n", 0, match.start()) + 1
            fetch_urls.append((rel, lineno, url))
            if (
                re.match(r"^https?://", url, re.IGNORECASE)
                or url.startswith("//")
                or not url.startswith("/api/")
            ):
                absolute_offenders.append(f"{rel}:{lineno}: fetch({url!r})")

    assert len(fetch_urls) >= 6, (
        f"Expected at least 6 fetch() calls in apps/web/src, found {len(fetch_urls)}"
    )
    assert not absolute_offenders, (
        "All fetch() calls in apps/web/src must use relative /api/... URLs (no http://):\n  "
        + "\n  ".join(absolute_offenders)
    )
