"""Step 2.1 (H5): Sunde equivalent-radius ring formula and explicit strip length tests."""

import pytest

from aegislps_engine.earthing import (
    RING_METHOD_LABEL,
    EarthingAssessmentInput,
    EarthingEngine,
    SoilLayerModel,
)


# ---------------------------------------------------------------------------
# Independently computed reference values (computed via standalone Python math
# script without importing earthing.py):
#
# Ring formula (Sunde equivalent-radius form):
#   R_ring = rho / (pi^2 * D) * ln(4 * D / sqrt(2 * a * h))
#   with D = 2 * max(1.0, ring_radius_m), a = conductor_diameter_m / 2,
#        h = max(0.1, burial_depth_m).
#
#   Case 1: rho=100, r=15.0 (D=30), d=0.01 (a=0.005), h=0.5
#           -> 4 sig figs: 2.512 ohm (full: 2.511634078340987 ohm)
#   Case 2: rho=250, r=8.0  (D=16), d=0.016 (a=0.008), h=0.8
#           -> 4 sig figs: 10.03 ohm (full: 10.034023844537897 ohm)
#   Case 3: rho=50,  r=30.0 (D=60), d=0.008 (a=0.004), h=0.6
#           -> 4 sig figs: 0.6882 ohm (full: 0.688157318897246 ohm)
#
# Horizontal strip formula (Sunde):
#   R_strip = rho / (pi * L) * [ln(2 * L / sqrt(2 * a * h)) - 1]
#   with L = strip_length_m, a = conductor_diameter_m / 2,
#        h = max(0.1, burial_depth_m).
#
#   Case 1: rho=100, L=30.0, d=0.01 (a=0.005), h=0.5
#           -> 4 sig figs: 6.094 ohm (full: 6.094046214567007 ohm)
#   Case 2: rho=250, L=10.0, d=0.016 (a=0.008), h=0.8
#           -> 4 sig figs: 33.22 ohm (full: 33.222697751821592 ohm)
#   Case 3: rho=50,  L=50.0, d=0.008 (a=0.004), h=0.6
#           -> 4 sig figs: 1.997 ohm (full: 1.997311732745587 ohm)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rho,ring_radius_m,conductor_diameter_m,burial_depth_m,expected_4sig,expected_full",
    [
        # Case 1: 4 sig figs = 2.512 ohm
        (100.0, 15.0, 0.01, 0.5, "2.512", 2.511634078340987),
        # Case 2: 4 sig figs = 10.03 ohm
        (250.0, 8.0, 0.016, 0.8, "10.03", 10.034023844537897),
        # Case 3: 4 sig figs = 0.6882 ohm
        (50.0, 30.0, 0.008, 0.6, "0.6882", 0.688157318897246),
    ],
)
def test_ring_sunde_matches_independent_values_within_1e6_rel(
    rho, ring_radius_m, conductor_diameter_m, burial_depth_m, expected_4sig, expected_full
):
    engine = EarthingEngine()
    res = engine.evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(rho_upper_ohm_m=rho),
            electrode_type="type_b_ring",
            ring_radius_m=ring_radius_m,
            conductor_diameter_m=conductor_diameter_m,
            burial_depth_m=burial_depth_m,
        )
    )
    assert f"{res.stationary_resistance_r_ohm:.4g}" == expected_4sig
    assert res.stationary_resistance_r_ohm == pytest.approx(expected_full, rel=1e-6)


def test_ring_carries_pending_confirmation_warning_and_keeps_status():
    engine = EarthingEngine()
    res = engine.evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(rho_upper_ohm_m=100.0),
            electrode_type="type_b_ring",
            ring_radius_m=15.0,
            conductor_diameter_m=0.01,
            burial_depth_m=0.5,
        )
    )
    assert RING_METHOD_LABEL in res.warnings
    assert any(
        "approximate; primary-source confirmation pending" in w for w in res.warnings
    )
    assert RING_METHOD_LABEL in res.method_details
    assert res.status == "PASS"


def test_ring_preserves_lower_bounds_on_radius_and_burial_depth():
    # Clamped at r_ring = 1.0 m (D = 2.0 m) and h_depth = 0.1 m:
    # R_ring = 100 / (pi^2 * 2) * ln(8 / sqrt(2 * 0.005 * 0.1)) = 28.03 ohm (4 sig figs)
    engine = EarthingEngine()
    res = engine.evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(rho_upper_ohm_m=100.0),
            electrode_type="type_b_ring",
            ring_radius_m=0.4,
            conductor_diameter_m=0.01,
            burial_depth_m=0.02,
        )
    )
    assert f"{res.stationary_resistance_r_ohm:.4g}" == "28.03"
    assert res.stationary_resistance_r_ohm == pytest.approx(
        28.032122445354364, rel=1e-6
    )


@pytest.mark.parametrize(
    "rho,strip_length_m,conductor_diameter_m,burial_depth_m,expected_4sig,expected_full",
    [
        # Case 1: 4 sig figs = 6.094 ohm
        (100.0, 30.0, 0.01, 0.5, "6.094", 6.094046214567007),
        # Case 2: 4 sig figs = 33.22 ohm
        (250.0, 10.0, 0.016, 0.8, "33.22", 33.222697751821592),
        # Case 3: 4 sig figs = 1.997 ohm
        (50.0, 50.0, 0.008, 0.6, "1.997", 1.997311732745587),
    ],
)
def test_strip_sunde_matches_independent_values_within_1e6_rel(
    rho, strip_length_m, conductor_diameter_m, burial_depth_m, expected_4sig, expected_full
):
    engine = EarthingEngine()
    res = engine.evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(rho_upper_ohm_m=rho),
            electrode_type="type_a_horizontal",
            strip_length_m=strip_length_m,
            conductor_diameter_m=conductor_diameter_m,
            burial_depth_m=burial_depth_m,
        )
    )
    assert f"{res.stationary_resistance_r_ohm:.4g}" == expected_4sig
    assert res.stationary_resistance_r_ohm == pytest.approx(expected_full, rel=1e-6)
    assert res.actual_effective_length_m == pytest.approx(strip_length_m, rel=1e-9)


def test_strip_uses_strip_length_m_and_ignores_ring_radius_m():
    engine = EarthingEngine()
    results = [
        engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                lps_class="I",
                soil=SoilLayerModel(rho_upper_ohm_m=100.0),
                electrode_type="type_a_horizontal",
                strip_length_m=20.0,
                ring_radius_m=ring_r,
                conductor_diameter_m=0.01,
                burial_depth_m=0.5,
            )
        )
        for ring_r in (2.0, 15.0, 80.0)
    ]
    r0 = results[0].stationary_resistance_r_ohm
    for res in results[1:]:
        assert res.stationary_resistance_r_ohm == r0
        assert res.actual_effective_length_m == 20.0
        assert res.impulse_impedance_z_ohm == results[0].impulse_impedance_z_ohm


@pytest.mark.parametrize("bad_strip_length", [None, 0.0, -5.0, float("nan"), float("inf")])
def test_strip_missing_or_non_positive_length_raises_value_error(bad_strip_length):
    engine = EarthingEngine()
    inp = EarthingAssessmentInput(
        electrode_type="type_a_horizontal",
        ring_radius_m=15.0,
        strip_length_m=bad_strip_length,
    )
    with pytest.raises(ValueError, match="strip_length_m"):
        engine.evaluate_earthing_system(inp)


def test_rod_and_foundation_paths_unchanged():
    engine = EarthingEngine()
    res_rod = engine.evaluate_earthing_system(
        EarthingAssessmentInput(
            electrode_type="type_a_vertical",
            vertical_rod_count=4,
            vertical_rod_spacing_m=5.0,
            vertical_rod_length_m=3.0,
        )
    )
    res_found = engine.evaluate_earthing_system(
        EarthingAssessmentInput(electrode_type="foundation")
    )
    assert res_rod.stationary_resistance_r_ohm == 11.52
    assert res_found.stationary_resistance_r_ohm == 3.47
