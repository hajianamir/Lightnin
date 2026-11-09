"""Verification tests for IEC 62305-3:2024 Clause 5.2.2.1 Table 2 rolling-sphere radii."""

import inspect

import pytest

import aegislps_geometry.rolling_sphere as rs_module
from aegislps_geometry.rolling_sphere import (
    ROLLING_SPHERE_RADIUS_M_BY_CLASS,
    RollingSphereEngine,
    rolling_sphere_radius_m,
)


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


def test_default_engine_uses_class_i_20m():
    assert RollingSphereEngine().r == 20.0


def test_no_radius_outside_table_2_for_classes_i_through_iv():
    allowed_classes = {"I", "II", "III", "IV"}
    allowed_radii = {20.0, 30.0, 45.0, 60.0}

    assert set(ROLLING_SPHERE_RADIUS_M_BY_CLASS.keys()) == allowed_classes
    assert set(ROLLING_SPHERE_RADIUS_M_BY_CLASS.values()) == allowed_radii

    produced = {rolling_sphere_radius_m(cls) for cls in allowed_classes}
    assert produced == allowed_radii


@pytest.mark.parametrize(
    "unknown_class",
    ["", " ", "0", "1", "V", "VI", "III-IV", "CLASS_I", "unknown"],
)
def test_unknown_class_raises_value_error(unknown_class: str):
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(unknown_class)


@pytest.mark.parametrize("bool_val", [True, False])
def test_bool_class_raises_value_error(bool_val: bool):
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(bool_val)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "non_string_val",
    [None, 0, 20, 20.0, -5.0, float("nan"), float("inf"), float("-inf"), ["I"], {"lps_class": "I"}],
)
def test_non_string_nan_inf_class_raises_value_error(non_string_val):
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(non_string_val)  # type: ignore[arg-type]


def test_normative_citation_present_in_rolling_sphere_source():
    source_text = inspect.getsource(rs_module)
    assert "IEC 62305-3:2024" in source_text
    assert "Clause 5.2.2.1" in source_text
    assert "Table 2" in source_text
