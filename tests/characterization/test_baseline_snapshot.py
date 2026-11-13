"""Characterization snapshot comparison tests (Step 0.1).

Recomputes current engine outputs via `generate_baseline.py` and compares them
against the JSON snapshots stored in `tests/characterization/baseline/`.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Dict, List

import pytest

HERE = Path(__file__).resolve().parent
BASELINE_DIR = HERE / "baseline"
REL_TOL = 1e-9

_GEN_SPEC = importlib.util.spec_from_file_location(
    "generate_baseline", HERE / "generate_baseline.py"
)
assert _GEN_SPEC is not None and _GEN_SPEC.loader is not None
generate_baseline = importlib.util.module_from_spec(_GEN_SPEC)
_GEN_SPEC.loader.exec_module(generate_baseline)

_COMPUTED_CACHE: Dict[str, Any] | None = None


def _get_computed_snapshots() -> Dict[str, Any]:
    global _COMPUTED_CACHE
    if _COMPUTED_CACHE is None:
        _COMPUTED_CACHE = generate_baseline.compute_all_snapshots()
    return _COMPUTED_CACHE


def _baseline_engine_names() -> List[str]:
    if not BASELINE_DIR.is_dir():
        return []
    return sorted(p.stem for p in BASELINE_DIR.glob("*.json"))


def _compare_values(
    engine: str,
    key_path: str,
    expected: Any,
    actual: Any,
    mismatches: List[str],
) -> None:
    loc = key_path or "<root>"

    if expected is None:
        if actual is not None:
            mismatches.append(
                f"engine='{engine}', key='{loc}': expected None, got {actual!r}"
            )
        return

    if isinstance(expected, bool):
        if not isinstance(actual, bool) or expected != actual:
            mismatches.append(
                f"engine='{engine}', key='{loc}': expected bool {expected!r}, got {actual!r}"
            )
        return

    if isinstance(expected, int):
        if isinstance(actual, bool) or not isinstance(actual, int) or expected != actual:
            mismatches.append(
                f"engine='{engine}', key='{loc}': expected int {expected!r}, got {actual!r} ({type(actual).__name__})"
            )
        return

    if isinstance(expected, str):
        if not isinstance(actual, str) or expected != actual:
            mismatches.append(
                f"engine='{engine}', key='{loc}': expected str {expected!r}, got {actual!r}"
            )
        return

    if isinstance(expected, float):
        if isinstance(actual, bool) or not isinstance(actual, float):
            mismatches.append(
                f"engine='{engine}', key='{loc}': expected float {expected!r}, got {actual!r} ({type(actual).__name__})"
            )
        elif not math.isclose(expected, actual, rel_tol=REL_TOL, abs_tol=0.0):
            mismatches.append(
                f"engine='{engine}', key='{loc}': float differs beyond rel_tol={REL_TOL}: "
                f"expected {expected!r}, got {actual!r}"
            )
        return

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            mismatches.append(
                f"engine='{engine}', key='{loc}': expected dict, got {type(actual).__name__}"
            )
            return
        missing_keys = sorted(set(expected) - set(actual))
        extra_keys = sorted(set(actual) - set(expected))
        for k in missing_keys:
            sub = f"{key_path}.{k}" if key_path else k
            mismatches.append(f"engine='{engine}', key='{sub}': missing key in actual output")
        for k in extra_keys:
            sub = f"{key_path}.{k}" if key_path else k
            mismatches.append(f"engine='{engine}', key='{sub}': unexpected key in actual output")
        for k in sorted(set(expected) & set(actual)):
            sub = f"{key_path}.{k}" if key_path else k
            _compare_values(engine, sub, expected[k], actual[k], mismatches)
        return

    if isinstance(expected, list):
        if not isinstance(actual, list):
            mismatches.append(
                f"engine='{engine}', key='{loc}': expected list, got {type(actual).__name__}"
            )
            return
        if len(expected) != len(actual):
            mismatches.append(
                f"engine='{engine}', key='{loc}': list length differs: expected {len(expected)}, got {len(actual)}"
            )
            return
        for idx, (exp_item, act_item) in enumerate(zip(expected, actual)):
            sub = f"{key_path}[{idx}]" if key_path else f"[{idx}]"
            _compare_values(engine, sub, exp_item, act_item, mismatches)
        return

    mismatches.append(
        f"engine='{engine}', key='{loc}': unsupported baseline type {type(expected).__name__}"
    )


def test_baseline_engine_inventory() -> None:
    recorded = set(_baseline_engine_names())
    computed = set(_get_computed_snapshots().keys())
    assert recorded == computed, (
        f"Baseline JSON file set differs from computed engines: "
        f"missing_files={sorted(computed - recorded)}, extra_files={sorted(recorded - computed)}"
    )


@pytest.mark.parametrize("engine_name", _baseline_engine_names())
def test_engine_matches_baseline_snapshot(engine_name: str) -> None:
    baseline_path = BASELINE_DIR / f"{engine_name}.json"
    with baseline_path.open("r", encoding="utf-8") as fh:
        expected = json.load(fh)
    computed = _get_computed_snapshots()
    assert engine_name in computed, f"engine='{engine_name}': not produced by generate_baseline.py"
    actual = computed[engine_name]

    mismatches: List[str] = []
    _compare_values(engine_name, "", expected, actual, mismatches)
    if mismatches:
        pytest.fail("Characterization snapshot mismatch:\n  " + "\n  ".join(mismatches))
