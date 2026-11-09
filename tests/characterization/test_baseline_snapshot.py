"""Compare current engine outputs with the recorded characterization snapshots.

The snapshots record CURRENT behaviour (including known defects). A failure
means behaviour changed; it is not automatically a bug. Regenerate with
`python tests/characterization/generate_baseline.py` only in a step that
explicitly allows it.
"""
import json
import math
import os

import pytest

import importlib.util

_GEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_baseline.py")
_spec = importlib.util.spec_from_file_location("generate_baseline", _GEN_PATH)
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)

BASELINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline")
REL_TOL = 1e-9

_SNAPSHOTS = None


def _current():
    global _SNAPSHOTS
    if _SNAPSHOTS is None:
        _SNAPSHOTS = {name: gb._norm(obj) for name, obj in gb.build_snapshots().items()}
    return _SNAPSHOTS


def _compare(path, expected, actual):
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: type dict expected"
        assert set(expected) == set(actual), f"{path}: key set differs: {set(expected) ^ set(actual)}"
        for k in expected:
            _compare(f"{path}.{k}", expected[k], actual[k])
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(expected) == len(actual), f"{path}: length differs"
        for i, (e, a) in enumerate(zip(expected, actual)):
            _compare(f"{path}[{i}]", e, a)
    elif isinstance(expected, bool) or isinstance(expected, str) or expected is None:
        assert expected == actual, f"{path}: expected {expected!r}, got {actual!r}"
    elif isinstance(expected, int):
        assert expected == actual, f"{path}: expected {expected}, got {actual}"
    elif isinstance(expected, float):
        assert isinstance(actual, (int, float)), f"{path}: expected float, got {actual!r}"
        if math.isnan(expected):
            assert math.isnan(actual), f"{path}: expected NaN"
        else:
            assert math.isclose(expected, actual, rel_tol=REL_TOL, abs_tol=0.0), \
                f"{path}: expected {expected!r}, got {actual!r}"
    else:
        raise AssertionError(f"{path}: unsupported type {type(expected)}")


def _snapshot_names():
    return sorted(f[:-5] for f in os.listdir(BASELINE_DIR) if f.endswith(".json"))


@pytest.mark.parametrize("name", _snapshot_names())
def test_snapshot_matches_baseline(name):
    with open(os.path.join(BASELINE_DIR, f"{name}.json"), encoding="utf-8") as fh:
        expected = json.load(fh)
    actual = _current()[name]
    _compare(name, expected, actual)


def test_no_snapshot_missing_or_extra():
    assert set(_snapshot_names()) == set(_current()), "snapshot set changed; regenerate only if allowed"
