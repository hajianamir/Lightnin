"""Step 3.3 tests: H7 roof-coverage disclosure label and Dalziel fault-duration range enforcement."""

import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aegislps_api.main import app
from aegislps_engine.optimization import (
    DesignOptimizationEngine,
    OptimizationInput,
    OptimizationResult,
    ProtectedTarget,
    ROOF_COVERAGE_VERIFICATION_NOTE,
)

EXPECTED_H7_NOTE = (
    "Roof coverage not verified (H7): the optimizer evaluates "
    "ground-referenced (z = 0) rolling-sphere coverage only."
)

client = TestClient(app)


def _converged_input() -> OptimizationInput:
    return OptimizationInput(
        lps_class="I",
        building_bounds=(-15.0, -10.0, 15.0, 10.0),
        roof_height_m=4.0,
        targets_to_protect=[
            ProtectedTarget(id="t1", x=-14.0, y=-9.0, z=4.0),
        ],
        iterations=10,
        random_seed=42,
    )


def _partial_zero_coverage_input() -> OptimizationInput:
    return OptimizationInput(
        lps_class="I",
        building_bounds=(-15.0, -10.0, 15.0, 10.0),
        roof_height_m=15.0,
        targets_to_protect=[
            ProtectedTarget(id="t1", x=-13.0, y=-8.0, z=15.0),
            ProtectedTarget(id="t2", x=13.0, y=-8.0, z=15.0),
            ProtectedTarget(id="t3", x=13.0, y=8.0, z=15.0),
            ProtectedTarget(id="t4", x=-13.0, y=8.0, z=15.0),
            ProtectedTarget(id="t5", x=0.0, y=0.0, z=16.5),
        ],
        iterations=10,
        random_seed=42,
    )


def test_optimization_result_disclosure_note_converged_and_partial():
    """A1: OptimizationResult carries exact H7 disclosure note on converged and non-converged runs."""
    assert ROOF_COVERAGE_VERIFICATION_NOTE == EXPECTED_H7_NOTE

    engine = DesignOptimizationEngine()

    res_ok = engine.optimize_air_terminations(_converged_input())
    assert res_ok.status == "CONVERGED"
    assert res_ok.roof_coverage_verification_note == EXPECTED_H7_NOTE

    res_partial = engine.optimize_air_terminations(_partial_zero_coverage_input())
    assert res_partial.status == "PARTIAL_COVERAGE"
    assert res_partial.roof_coverage_verification_note == EXPECTED_H7_NOTE

    res_default = OptimizationResult(
        selected_rods=[],
        uncovered_targets_count=1,
        coverage_percentage=0.0,
        total_rod_cost=0.0,
        iterations_run=0,
        pareto_score=0.0,
        status="PARTIAL_COVERAGE",
    )
    assert res_default.roof_coverage_verification_note == EXPECTED_H7_NOTE


def test_optimization_result_note_in_engineering_insights():
    """A2: Exact H7 disclosure note also appears in the result's insights/diagnostics list."""
    engine = DesignOptimizationEngine()

    for inp in (_converged_input(), _partial_zero_coverage_input()):
        res = engine.optimize_air_terminations(inp)
        assert EXPECTED_H7_NOTE in res.diagnostics
        assert EXPECTED_H7_NOTE in res.engineering_insights


def test_optimization_api_endpoint_returns_disclosure_note():
    """A3: POST /api/v1/optimization/optimize-rods returns HTTP 200 with exact H7 note in JSON body."""
    payload = {
        "lps_class": "I",
        "building_bounds": [-15.0, -10.0, 15.0, 10.0],
        "roof_height_m": 4.0,
        "targets_to_protect": [
            {"id": "t1", "x": -14.0, "y": -9.0, "z": 4.0},
        ],
        "iterations": 10,
        "random_seed": 42,
    }
    resp = client.post("/api/v1/optimization/optimize-rods", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["roof_coverage_verification_note"] == EXPECTED_H7_NOTE
    assert EXPECTED_H7_NOTE in body["diagnostics"]

    bad_payload = {**payload, "targets_to_protect": []}
    bad_resp = client.post("/api/v1/optimization/optimize-rods", json=bad_payload)
    assert bad_resp.status_code == 422


def test_optimization_strict_xfail_preserved():
    """A4: test_design_optimization_coverage_improvement retains @pytest.mark.xfail(strict=True)."""
    mod_path = Path(__file__).with_name("test_optimization_and_pv.py")
    spec = importlib.util.spec_from_file_location(
        "test_optimization_and_pv_mod", mod_path
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    marks = getattr(
        mod.test_design_optimization_coverage_improvement, "pytestmark", []
    )
    xfail_marks = [m for m in marks if m.name == "xfail"]
    assert len(xfail_marks) == 1
    assert xfail_marks[0].kwargs.get("strict") is True
    reason = str(xfail_marks[0].kwargs.get("reason", ""))
    assert "H7" in reason
    assert "step 3.3" in reason


@pytest.mark.parametrize(
    "fault_duration_s,expected_status",
    [
        (0.02, 422),
        (0.03, 200),
        (3.0, 200),
        (3.1, 422),
    ],
)
def test_touch_step_dalziel_fault_duration_bounds_api(
    fault_duration_s: float,
    expected_status: int,
):
    """B1: Dalziel fault_duration_s outside [0.03, 3.0] s -> HTTP 422; boundary values -> HTTP 200."""
    payload = {
        "lps_class": "I",
        "soil_resistivity_ohm_m": 100.0,
        "surface_layer_material": "bare_soil",
        "fault_duration_s": fault_duration_s,
        "body_weight_kg": 50.0,
        "peak_impulse_current_ka": 100.0,
        "down_conductor_radius_m": 0.005,
        "has_physical_insulation_barrier": False,
        "has_restricted_access_perimeter": False,
        "earth_potential_rise_v": 500.0,
        "electrode_equivalent_radius_m": 5.0,
    }
    resp = client.post("/api/v1/calculations/touch-step", json=payload)
    assert resp.status_code == expected_status
