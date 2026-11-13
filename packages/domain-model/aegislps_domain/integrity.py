"""Keyed HMAC-SHA256 project integrity check (Step 4.3, H11).

Standard basis:
- `docs/37_P0-S2_OWNER_DECISION_BRIEF.md`, item R1: "HMAC is only an integrity
  check with a shared key (NIST FIPS 198-1)" — the key must remain secret and
  must never be embedded in source code.
- Keyed HMAC-SHA256 construction per RFC 2104 / NIST FIPS 198-1 over canonical
  JSON (`sort_keys=True`, `separators=(",", ":")`, excluding `"checksum"` and
  `"updated_at"`).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any, Dict

INTEGRITY_KEY_ENV_VAR = "AEGISLPS_INTEGRITY_KEY"
MIN_INTEGRITY_KEY_BYTES = 32


class IntegrityKeyNotConfigured(RuntimeError):
    """Raised when AEGISLPS_INTEGRITY_KEY is missing or shorter than 32 UTF-8 bytes."""


class ProjectIntegrityEngine:
    """
    Keyed HMAC-SHA256 integrity check for AegisLPS project dictionaries.

    Reads the shared secret at call time from `AEGISLPS_INTEGRITY_KEY` (minimum
    32 UTF-8 bytes) and fails closed with `IntegrityKeyNotConfigured` when unset
    or too short.
    """

    @staticmethod
    def _load_integrity_key() -> bytes:
        raw_key = os.environ.get(INTEGRITY_KEY_ENV_VAR)
        if raw_key is None or raw_key == "":
            raise IntegrityKeyNotConfigured(
                f"Environment variable {INTEGRITY_KEY_ENV_VAR} is not configured; "
                f"provide at least {MIN_INTEGRITY_KEY_BYTES} UTF-8 bytes."
            )
        key_bytes = raw_key.encode("utf-8")
        if len(key_bytes) < MIN_INTEGRITY_KEY_BYTES:
            raise IntegrityKeyNotConfigured(
                f"Environment variable {INTEGRITY_KEY_ENV_VAR} must be at least "
                f"{MIN_INTEGRITY_KEY_BYTES} UTF-8 bytes (got {len(key_bytes)} bytes)."
            )
        return key_bytes

    @classmethod
    def compute_project_checksum(cls, project_dict: Dict[str, Any]) -> str:
        """
        Generates deterministic HMAC-SHA256 hex digest over canonicalized JSON.
        Excludes transient/metadata keys 'checksum' and 'updated_at'.
        """
        key_bytes = cls._load_integrity_key()
        clean_dict = {
            k: v for k, v in project_dict.items() if k not in ["checksum", "updated_at"]
        }
        canonical_json = json.dumps(clean_dict, sort_keys=True, separators=(",", ":"))
        return hmac.new(
            key_bytes, canonical_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @classmethod
    def verify_project_integrity(
        cls, project_dict: Dict[str, Any], expected_checksum: str
    ) -> bool:
        computed = cls.compute_project_checksum(project_dict)
        return hmac.compare_digest(computed, expected_checksum)
