"""Verification tests for IEC 62305-3:2024 Clause 5.2.2.1 Table 2 rolling-sphere radii."""

import inspect
import math

import pytest

import aegislps_geometry.rolling_sphere as rs_module
from aegislps_geometry.rolling_sphere import (
    ROLLING_SPHERE_RADIUS_M_BY_CLASS,
    RollingSphereEngine,
    protected_radius_at_height,
    rolling_sphere_radius_m,
)


EXPECTED_TABLE_2_RADII_M = {
    "I": 20.0,
    "II": 30.0,
    "III": 45.0,
    "IV": 60.0,
}


@pytest.mark.parametrize(
    ("lps_class", "expected_r_m"),
    [
        ("I", 20.0),
        ("II", 30.0),
        ("III", 45.0),
        ("IV", 60.0),
    ],
)
def test_table_2_radii_by_lps_class(lps_class: str, expected_r_m: float):
    assert ROLLING_SPHERE_RADIUS_M_BY_CLASS[lps_class] == expected_r_m
    assert rolling_sphere_radius_m(lps_class) == expected_r_m
    assert rolling_sphere_radius_m(f" {lps_class.lower()} ") == expected_r_m
    assert RollingSphereEngine(lps_class=lps_class).r == expected_r_m


def test_default_engine_uses_class_i_20m():
    assert RollingSphereEngine().r == 20.0


def test_no_radius_outside_table_2_for_classes_i_through_iv():
    allowed_classes = {"I", "II", "III", "IV"}
    allowed_radii = {20.0, 30.0, 45.0, 60.0}

    assert set(ROLLING_SPHERE_RADIUS_M_BY_CLASS.keys()) == allowed_classes
    assert set(ROLLING_SPHERE_RADIUS_M_BY_CLASS.values()) == allowed_radii

    produced_fn = {rolling_sphere_radius_m(cls) for cls in allowed_classes}
    produced_engine = {RollingSphereEngine(lps_class=cls).r for cls in allowed_classes}
    assert produced_fn == allowed_radii
    assert produced_engine == allowed_radii


@pytest.mark.parametrize(
    "unknown_class",
    ["", " ", "0", "1", "V", "VI", "III-IV", "CLASS_I", "unknown"],
)
def test_unknown_class_raises_value_error(unknown_class: str):
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(unknown_class)
    with pytest.raises(ValueError):
        RollingSphereEngine(lps_class=unknown_class)


@pytest.mark.parametrize("bad_current", [0, 0.0, -1e-9, -5.0, -100.0])
def test_non_positive_current_raises_value_error(bad_current: float):
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(current_ka=bad_current)
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(bad_current)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        RollingSphereEngine(sphere_radius_m=bad_current)


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_nan_and_infinite_inputs_raise_value_error(non_finite: float):
    assert math.isnan(non_finite) or math.isinf(non_finite)
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(current_ka=non_finite)
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(non_finite)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        RollingSphereEngine(sphere_radius_m=non_finite)
    with pytest.raises(ValueError):
        protected_radius_at_height(non_finite, 10.0, 2.0)


@pytest.mark.parametrize("bool_val", [True, False])
def test_bool_inputs_raise_value_error(bool_val: bool):
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(bool_val)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(current_ka=bool_val)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        RollingSphereEngine(sphere_radius_m=bool_val)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        RollingSphereEngine(lps_class=bool_val)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        protected_radius_at_height(bool_val, 10.0, 2.0)  # type: ignore[arg-type]


def test_missing_or_conflicting_arguments_raise_value_error():
    with pytest.raises(ValueError):
        rolling_sphere_radius_m()
    with pytest.raises(ValueError):
        RollingSphereEngine(sphere_radius_m=20.0, lps_class="I")


def test_normative_citation_present_in_rolling_sphere_source():
    source_text = inspect.getsource(rs_module)
    assert "IEC 62305-3:2024" in source_text
    assert "Clause 5.2.2.1" in source_text
    assert "Table 2" in source_text
