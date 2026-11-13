"""Pytest session configuration (Step 4.3, H11).

Provides a test-only session-scoped AEGISLPS_INTEGRITY_KEY so existing tests
exercising ProjectIntegrityEngine run without modifying their assertions.
"""

from __future__ import annotations

import os
from typing import Iterator

import pytest

TEST_ONLY_SESSION_INTEGRITY_KEY = (
    "test-only-aegislps-session-hmac-key-not-for-production-0001"
)


@pytest.fixture(scope="session", autouse=True)
def _configure_test_session_integrity_key() -> Iterator[None]:
    previous = os.environ.get("AEGISLPS_INTEGRITY_KEY")
    os.environ["AEGISLPS_INTEGRITY_KEY"] = TEST_ONLY_SESSION_INTEGRITY_KEY
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("AEGISLPS_INTEGRITY_KEY", None)
        else:
            os.environ["AEGISLPS_INTEGRITY_KEY"] = previous
