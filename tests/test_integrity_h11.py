"""Step 4.3 — H11: Fail-closed AEGISLPS_INTEGRITY_KEY for HMAC-SHA256 project integrity."""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import aegislps_domain.integrity as integrity_mod
from aegislps_api.main import app
from aegislps_domain.integrity import (
    INTEGRITY_KEY_ENV_VAR,
    IntegrityKeyNotConfigured,
    ProjectIntegrityEngine,
)

client = TestClient(app)

TEST_ONLY_KEY_PRIMARY = "test-only-step43-reference-hmac-key-36b!"
TEST_ONLY_KEY_ALTERNATE = "test-only-step43-alternate-hmac-key-36b!"

SAMPLE_PROJECT_DICT = {
    "project_id": "proj-step43-sample-001",
    "name": "Step 4.3 Sample Substation",
    "lps_class": "I",
    "approved": True,
}

VALID_API_PROJECT_PAYLOAD = {
    "name": "Step 4.3 API Project",
    "lps_class": "I",
    "building": {"length_m": 20.0, "width_m": 10.0, "height_m": 15.0, "roof_type": "flat"},
    "nodes": [{"id": "n1", "x": 0.0, "y": 0.0, "z": 15.0, "node_type": "air_termination"}],
    "segments": [],
    "separation_points": [],
}


def test_checksum_hex64_determinism_key_sensitivity_tamper_and_excluded_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(INTEGRITY_KEY_ENV_VAR, TEST_ONLY_KEY_PRIMARY)

    digest_1 = ProjectIntegrityEngine.compute_project_checksum(SAMPLE_PROJECT_DICT)
    digest_2 = ProjectIntegrityEngine.compute_project_checksum(dict(SAMPLE_PROJECT_DICT))

    assert isinstance(digest_1, str)
    assert len(digest_1) == 64
    int(digest_1, 16)
    assert digest_1 == digest_2
    assert ProjectIntegrityEngine.verify_project_integrity(SAMPLE_PROJECT_DICT, digest_1) is True

    # Excluded metadata keys ("checksum", "updated_at") must not change digest
    with_metadata = {
        **SAMPLE_PROJECT_DICT,
        "checksum": "stale-digest-value",
        "updated_at": "2026-11-09T12:34:56Z",
    }
    assert ProjectIntegrityEngine.compute_project_checksum(with_metadata) == digest_1

    # Tampered payload must fail verification
    tampered = {**SAMPLE_PROJECT_DICT, "lps_class": "II"}
    assert ProjectIntegrityEngine.verify_project_integrity(tampered, digest_1) is False

    # Different key must produce a different digest
    monkeypatch.setenv(INTEGRITY_KEY_ENV_VAR, TEST_ONLY_KEY_ALTERNATE)
    digest_alt = ProjectIntegrityEngine.compute_project_checksum(SAMPLE_PROJECT_DICT)
    assert digest_alt != digest_1
    assert ProjectIntegrityEngine.verify_project_integrity(SAMPLE_PROJECT_DICT, digest_1) is False


def test_missing_or_short_key_fails_closed_naming_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(INTEGRITY_KEY_ENV_VAR, raising=False)
    with pytest.raises(IntegrityKeyNotConfigured, match=INTEGRITY_KEY_ENV_VAR):
        ProjectIntegrityEngine.compute_project_checksum(SAMPLE_PROJECT_DICT)
    with pytest.raises(IntegrityKeyNotConfigured, match=INTEGRITY_KEY_ENV_VAR):
        ProjectIntegrityEngine.verify_project_integrity(SAMPLE_PROJECT_DICT, "0" * 64)

    monkeypatch.setenv(INTEGRITY_KEY_ENV_VAR, "")
    with pytest.raises(IntegrityKeyNotConfigured, match=INTEGRITY_KEY_ENV_VAR):
        ProjectIntegrityEngine.compute_project_checksum(SAMPLE_PROJECT_DICT)

    short_31_byte_secret = "x" * 31
    monkeypatch.setenv(INTEGRITY_KEY_ENV_VAR, short_31_byte_secret)
    with pytest.raises(IntegrityKeyNotConfigured, match=INTEGRITY_KEY_ENV_VAR) as exc_info:
        ProjectIntegrityEngine.compute_project_checksum(SAMPLE_PROJECT_DICT)
    assert short_31_byte_secret not in str(exc_info.value)

    exact_32_byte_key = "y" * 32
    monkeypatch.setenv(INTEGRITY_KEY_ENV_VAR, exact_32_byte_key)
    digest_32 = ProjectIntegrityEngine.compute_project_checksum(SAMPLE_PROJECT_DICT)
    assert len(digest_32) == 64


def test_integrity_module_has_no_hardcoded_secret_or_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_attr = "".join(["SECRET", "_SALT"])
    legacy_prefix = "".join(["AegisLPS", "_Engineering", "_Integrity"])

    assert not hasattr(ProjectIntegrityEngine, legacy_attr)
    src = Path(integrity_mod.__file__).read_text(encoding="utf-8")
    assert legacy_attr not in src
    assert legacy_prefix not in src

    monkeypatch.delenv(INTEGRITY_KEY_ENV_VAR, raising=False)
    with pytest.raises(IntegrityKeyNotConfigured):
        ProjectIntegrityEngine.compute_project_checksum(SAMPLE_PROJECT_DICT)


def test_api_compute_checksum_returns_200_when_set_503_when_unset_and_422_on_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(INTEGRITY_KEY_ENV_VAR, TEST_ONLY_KEY_PRIMARY)
    resp_ok = client.post("/api/v1/projects/compute-checksum", json=VALID_API_PROJECT_PAYLOAD)
    assert resp_ok.status_code == 200
    body_ok = resp_ok.json()
    assert len(body_ok["checksum"]) == 64
    assert TEST_ONLY_KEY_PRIMARY not in resp_ok.text

    monkeypatch.delenv(INTEGRITY_KEY_ENV_VAR, raising=False)
    resp_unset = client.post(
        "/api/v1/projects/compute-checksum", json=VALID_API_PROJECT_PAYLOAD
    )
    assert resp_unset.status_code == 503
    assert resp_unset.json() == {"detail": "Integrity key is not configured on the server."}

    resp_invalid = client.post("/api/v1/projects/compute-checksum", json={})
    assert resp_invalid.status_code == 422


def test_legacy_salt_digest_differs_and_canonical_hmac_sha256_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(INTEGRITY_KEY_ENV_VAR, TEST_ONLY_KEY_PRIMARY)
    new_digest = ProjectIntegrityEngine.compute_project_checksum(SAMPLE_PROJECT_DICT)

    canonical_json = json.dumps(SAMPLE_PROJECT_DICT, sort_keys=True, separators=(",", ":"))
    legacy_salt_bytes = "".join(
        ["AegisLPS", "_Engineering", "_Integrity", "_Salt_2026"]
    ).encode("ascii")
    legacy_digest = hmac.new(
        legacy_salt_bytes, canonical_json.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert new_digest != legacy_digest

    reference_digest = hmac.new(
        TEST_ONLY_KEY_PRIMARY.encode("utf-8"),
        canonical_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert new_digest == reference_digest
