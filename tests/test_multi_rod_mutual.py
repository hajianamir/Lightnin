"""Step 2.3 (H4): Pairwise uniform-leakage mutual coupling tests for vertical rod arrays."""

import math
import pytest

from aegislps_engine.earth_rod_sizing import EarthRodSizingEngine, EarthRodSizingInput
from aegislps_engine.earthing import (
    MULTI_ROD_METHOD_LABEL,
    EarthingAssessmentInput,
    EarthingEngine,
    SoilLayerModel,
    array_resistance_identical_rods,
    mutual_resistance_rods,
    single_vertical_rod_resistance,
)

# IEEE Std 142-2007, Table 4-6 (p. 167): Multiplying factors F for N rods at s = L
IEEE_142_TABLE_4_6 = {
    2: 1.16,
    3: 1.29,
    4: 1.36,
    8: 1.68,
    12: 1.80,
    16: 1.92,
    20: 2.00,
    24: 2.16,
}


def test_r_m_reference_values():
    """
    Reference check at rho=100, L=10, a=0.01 (secondary reference: erdep thread):
      R1      = 11.608841 (erdep: 11.573)
      R_m(10) = 1.487017  (erdep: 1.3027, accepted +14.1% uniform-leakage model error at s=L)
      R_m(100)= 0.159023  (erdep: 0.1586)
      R_2(10) = 6.547929  (erdep: 6.4378, accepted +1.71% error at s=L)
    """
    rho, L, a = 100.0, 10.0, 0.01
    r1 = single_vertical_rod_resistance(rho, L, a)
    rm_10 = mutual_resistance_rods(rho, L, 10.0)
    rm_100 = mutual_resistance_rods(rho, L, 100.0)
    r2_10 = array_resistance_identical_rods(rho, L, a, 2, 10.0)

    assert abs(r1 - 11.608841) <= 1e-4
    assert abs(rm_10 - 1.487017) <= 1e-4
    assert abs(rm_100 - 0.159023) <= 1e-4
    assert abs(r2_10 - 6.547929) <= 1e-4


def test_r_m_far_field_asymptote():
    """At s=100, L=10, rho=100, R_m(s) is within 1% of far-field asymptote rho/(2*pi*s)."""
    rho, L, s = 100.0, 10.0, 100.0
    asym = rho / (2.0 * math.pi * s)  # 0.159154943...
    rm_val = mutual_resistance_rods(rho, L, s)
    assert abs(rm_val - asym) / asym < 0.01


def test_type_a_vertical_rejects_single_rod_per_clause_5_4_2_2():
    """array_resistance_identical_rods(N=1) equals R1, while EarthingAssessmentInput rejects 1-rod Type A."""
    rho, L, a, s = 100.0, 3.0, 0.005, 5.0
    r1 = single_vertical_rod_resistance(rho, L, a)
    rn1 = array_resistance_identical_rods(rho, L, a, 1, s)
    assert abs(rn1 - r1) <= 1e-12 * r1

    with pytest.raises(ValueError, match="vertical_rod_count"):
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(rho_upper_ohm_m=100.0),
            electrode_type="type_a_vertical",
            conductor_diameter_m=0.01,
            vertical_rod_count=1,
            vertical_rod_length_m=3.0,
            vertical_rod_spacing_m=5.0,
            peak_impulse_current_ka=100.0,
        )


def test_n2_at_spacing_L_within_ieee142_band():
    """
    IEEE 142-2007 Table 4-6: F(2) = 1.16 at s = L; erdep secondary reference: F(2) ≈ 1.113.
    Uniform-leakage equal-current formula gives F(2) ≈ 1.1281 inside [1.10, 1.20].
    """
    rho, L, a = 100.0, 10.0, 0.01
    r1 = single_vertical_rod_resistance(rho, L, a)
    r2 = array_resistance_identical_rods(rho, L, a, 2, L)
    f2 = r2 / (r1 / 2.0)
    assert 1.10 <= f2 <= 1.20


def test_table_report_only(capsys):
    """
    Report-only table of F_new(N) and F_old(N) at s = 2*L alongside IEEE 142-2007 Table 4-6.
    Does NOT assert equality for N >= 3.
    """
    rho, L, a = 120.0, 3.0, 0.008
    s = 2.0 * L
    r1 = single_vertical_rod_resistance(rho, L, a)
    c_old = (L / (2.0 * math.pi * s)) * math.log(1.0 + s / L)

    lines = ["N | F_new(s=2L) | F_old(s=2L) | IEEE142_F(s=L)"]
    for n in (2, 3, 4, 8, 12, 16, 20, 24):
        r_new = array_resistance_identical_rods(rho, L, a, n, s)
        f_new = r_new / (r1 / n)
        f_old = 1.0 + (n - 1) * c_old
        assert math.isfinite(f_new) and f_new >= 1.0
        lines.append(f"{n:2d} | {f_new:11.4f} | {f_old:11.4f} | {IEEE_142_TABLE_4_6[n]:14.2f}")

    print("\n" + "\n".join(lines))
    captured = capsys.readouterr()
    assert "IEEE142_F" in captured.out


def test_old_formula_overestimate_documented():
    """
    Documents the old coupling defect: at s = L, literal old c(s) = (L/(2*pi*s))*ln(1+s/L)
    yields F_old(24) = 1 + 23 * ln(2)/(2*pi) ≈ 3.537 > 1.5 * 2.16 = 3.24.
    """
    L = 10.0
    s = L
    c_old = (L / (2.0 * math.pi * s)) * math.log(1.0 + s / L)
    f_old_24 = 1.0 + (24 - 1) * c_old
    assert f_old_24 > 1.5 * IEEE_142_TABLE_4_6[24]


def test_earthing_engine_vertical_multi_rod_uses_pairwise_mutual():
    """Exercises EarthingEngine type_a_vertical multi-rod path (guards M1)."""
    res = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            electrode_type="type_a_vertical",
            soil=SoilLayerModel(rho_upper_ohm_m=100.0),
            vertical_rod_count=4,
            vertical_rod_length_m=3.0,
            vertical_rod_spacing_m=5.0,
            conductor_diameter_m=0.01,
            peak_impulse_current_ka=100.0,
        )
    )
    assert abs(res.stationary_resistance_r_ohm - 10.68) < 0.01
    assert MULTI_ROD_METHOD_LABEL in res.method_details


def test_earth_rod_sizing_engine_uses_pairwise_mutual():
    """Exercises EarthRodSizingEngine multi-rod sizing loop (guards M2)."""
    res = EarthRodSizingEngine().size_earth_rod_system(
        EarthRodSizingInput(
            lps_class="I",
            soil_resistivity_ohm_m=120.0,
            target_resistance_ohm=10.0,
            electrode_material="copper_bonded_steel",
            rod_length_per_unit_m=3.0,
            min_distance_to_building_foundation_m=1.0,
            site_boundary_length_m=40.0,
            site_boundary_width_m=25.0,
        )
    )
    assert res.required_number_of_rods == 5
    assert abs(res.total_array_resistance_ohm - 9.65) < 0.01
    assert len(res.recommended_rod_coordinates) == 5


@pytest.mark.parametrize(
    "rho,L,a,n,s",
    [
        (0.0, 3.0, 0.008, 2, 6.0),
        (-10.0, 3.0, 0.008, 2, 6.0),
        (100.0, 0.0, 0.008, 2, 6.0),
        (100.0, 3.0, 0.0, 2, 6.0),
        (100.0, 3.0, 0.008, 0, 6.0),
        (100.0, 3.0, 0.008, 2.5, 6.0),
        (100.0, 3.0, 0.008, True, 6.0),
        (100.0, 3.0, 0.008, 2, 0.0),
        (100.0, 3.0, 0.008, 2, -5.0),
    ],
)
def test_validation_raises_on_invalid_inputs(rho, L, a, n, s):
    with pytest.raises(ValueError):
        array_resistance_identical_rods(rho, L, a, n, s)
