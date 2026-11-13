"""Physics and IEC 62305-4:2024 Annex A verification tests for LEMPEngine (Step 1.5: C3-b; updated for H9-B4)."""

import math
import numpy as np
import pytest

from aegislps_engine.lemp_engine import (
    InternalCableLoop,
    LEMPEngine,
    LEMPTransientResult,
    LEMPWaveformSpecification,
    ShieldingGrid,
    _shielding_factor_db,
)

_DEFAULT_LOOP_KWARGS = dict(
    loop_area_m2=2.0,
    center_distance_from_down_conductor_m=3.0,
    equipment_withstand_uw_kv=1.5,
)


def _assert_result_finite(res: LEMPTransientResult) -> None:
    """Assert that every numeric scalar and waveform array element is finite."""
    for scalar in (
        res.peak_current_ka,
        res.max_di_dt_ka_per_us,
        res.unattenuated_peak_h_field_a_per_m,
        res.shielded_peak_h_field_a_per_m,
        res.grid_shielding_factor_kms,
        res.shielding_factor_db,
        res.safety_distance_m,
        res.peak_induced_voltage_kv,
        res.equipment_withstand_uw_kv,
    ):
        assert math.isfinite(scalar), f"Non-finite scalar in LEMPTransientResult: {scalar}"

    for arr in (
        res.time_series_us,
        res.current_waveform_ka,
        res.induced_voltage_waveform_kv,
    ):
        assert len(arr) > 0
        assert all(math.isfinite(v) for v in arr)


def test_01_copper_w2m_unbonded():
    """1. Copper/aluminium, w_m = 2 m: SF = 12.56 dB, K = 0.2353, d_SF = 2.51 m."""
    engine = LEMPEngine()
    res = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350",
            peak_current_ka=100.0,
        ),
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
            meshed_bonding_network=False,
        ),
        InternalCableLoop(**_DEFAULT_LOOP_KWARGS),
    )
    _assert_result_finite(res)
    assert res.k_source == "IEC 62305-4:2024 Table A.4"
    assert res.shielding_factor_db == pytest.approx(12.56, abs=0.01)
    assert res.grid_shielding_factor_kms == pytest.approx(0.2353, abs=0.001)
    assert res.safety_distance_m == pytest.approx(2.51, abs=0.01)


def test_02_copper_w2m_meshed_bonding():
    """2. Copper/aluminium, w_m = 2 m, meshed bonding (+6 dB): SF = 18.56 dB, K = 0.1177."""
    engine = LEMPEngine()
    res = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350",
            peak_current_ka=100.0,
        ),
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
            meshed_bonding_network=True,
        ),
        InternalCableLoop(**_DEFAULT_LOOP_KWARGS),
    )
    _assert_result_finite(res)
    assert res.shielding_factor_db == pytest.approx(18.56, abs=0.01)
    assert res.grid_shielding_factor_kms == pytest.approx(0.1177, abs=0.001)
    assert res.safety_distance_m == pytest.approx(3.71, abs=0.01)


def test_03_copper_w10m_negative_sf_clamped_to_zero():
    """3. Copper/aluminium, w_m = 10 m: SF_formula = -1.41 dB -> clamped to 0 -> K = 1.0."""
    sf_raw = 20.0 * math.log10(8.5 / 10.0)
    assert sf_raw == pytest.approx(-1.41, abs=0.01)

    engine = LEMPEngine()
    res = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350",
            peak_current_ka=100.0,
        ),
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=10.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
            meshed_bonding_network=False,
        ),
        InternalCableLoop(**_DEFAULT_LOOP_KWARGS),
    )
    _assert_result_finite(res)
    assert res.shielding_factor_db == 0.0
    assert res.grid_shielding_factor_kms == 1.0
    assert res.safety_distance_m == 10.0


def test_04_copper_w10m_meshed_bonding_after_zero_clamp():
    """4. Copper/aluminium, w_m = 10 m, bonded: clamp(-1.41 -> 0) + 6 = 6.0 dB, K = 0.501, d_SF = 10 m."""
    engine = LEMPEngine()
    res = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350",
            peak_current_ka=100.0,
        ),
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=10.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
            meshed_bonding_network=True,
        ),
        InternalCableLoop(**_DEFAULT_LOOP_KWARGS),
    )
    _assert_result_finite(res)
    assert res.shielding_factor_db == pytest.approx(6.0, abs=1e-6)
    assert res.grid_shielding_factor_kms == pytest.approx(0.501, abs=0.001)
    # Since SF = 6.0 < 10 dB, Eq. (A.15) gives d_SF/n = w_m = 10 m
    assert res.safety_distance_m == pytest.approx(10.0, abs=1e-6)


def test_05_steel_w2m_rc5mm_first_positive_reduces_sf():
    """5. Steel, w_m = 2 m, r_c = 5 mm, first positive (25 kHz): SF = 10.22 dB, K = 0.3087, d_SF = 2.04 m."""
    engine = LEMPEngine()
    res_steel = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350",
            peak_current_ka=100.0,
        ),
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material="steel",
            meshed_bonding_network=False,
        ),
        InternalCableLoop(**_DEFAULT_LOOP_KWARGS),
    )
    res_copper = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350",
            peak_current_ka=100.0,
        ),
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
            meshed_bonding_network=False,
        ),
        InternalCableLoop(**_DEFAULT_LOOP_KWARGS),
    )
    _assert_result_finite(res_steel)
    assert res_steel.shielding_factor_db == pytest.approx(10.22, abs=0.01)
    assert res_steel.grid_shielding_factor_kms == pytest.approx(0.3087, abs=0.001)
    assert res_steel.safety_distance_m == pytest.approx(2.04, abs=0.01)

    # Steel impedance term divides 8.5/w_m -> reduces SF (increases K_MS) relative to copper
    assert res_steel.shielding_factor_db < res_copper.shielding_factor_db
    assert res_steel.grid_shielding_factor_kms > res_copper.grid_shielding_factor_kms


def test_06_steel_w2m_subsequent_stroke():
    """6. Steel, w_m = 2 m, subsequent stroke (1 MHz): SF = 12.56 dB, K = 0.2353."""
    engine = LEMPEngine()
    res = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="subsequent_negative_025_100",
            peak_current_ka=100.0,
        ),
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material="steel",
            meshed_bonding_network=False,
        ),
        InternalCableLoop(**_DEFAULT_LOOP_KWARGS),
    )
    _assert_result_finite(res)
    assert res.shielding_factor_db == pytest.approx(12.56, abs=0.01)
    assert res.grid_shielding_factor_kms == pytest.approx(0.2353, abs=0.001)


@pytest.mark.parametrize(
    "s_a_m,expected_h1_a_per_m",
    [
        (67.0, 56.0),
        (87.0, 43.0),
        (137.0, 27.0),
    ],
)
def test_07_table_a6_shielded_magnetic_field_cases(
    s_a_m: float, expected_h1_a_per_m: float
):
    """7. IEC 62305-4:2024 Table A.6 example: I_0 = 100 kA, w_m = 2 m, H_1 from H_0 and SF within 2%."""
    engine = LEMPEngine()
    res = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350",
            peak_current_ka=100.0,
            t_end_us=100.0,
        ),
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
            meshed_bonding_network=False,
        ),
        InternalCableLoop(
            loop_area_m2=2.0,
            center_distance_from_down_conductor_m=s_a_m,
            equipment_withstand_uw_kv=1.5,
        ),
    )
    _assert_result_finite(res)
    assert res.shielding_factor_db == pytest.approx(12.56, abs=0.01)
    assert res.shielded_peak_h_field_a_per_m == pytest.approx(
        expected_h1_a_per_m, rel=0.02
    )


def test_08_unshielded_gives_unit_k_and_override_source():
    """8. is_shielded = False gives K = 1.0; explicit override sets k_source = 'override'."""
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification(
        stroke_type="first_positive_10_350",
        peak_current_ka=100.0,
    )
    loop = InternalCableLoop(**_DEFAULT_LOOP_KWARGS)

    for shield in (
        ShieldingGrid(is_shielded=False),
        ShieldingGrid(
            is_shielded=False,
            mesh_width_w_m=1.0,
            rod_radius_m=0.005,
            material="steel",
            meshed_bonding_network=True,
            shielding_factor_override_db=20.0,
        ),
    ):
        res = engine.calculate_lemp_induction(waveform, shield, loop)
        _assert_result_finite(res)
        assert res.grid_shielding_factor_kms == 1.0
        assert res.shielding_factor_db == 0.0
        assert res.shielded_peak_h_field_a_per_m == res.unattenuated_peak_h_field_a_per_m

    res_override = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
            shielding_factor_override_db=20.0,
        ),
        loop,
    )
    _assert_result_finite(res_override)
    assert res_override.k_source == "override"
    assert res_override.shielding_factor_db == 20.0
    assert res_override.grid_shielding_factor_kms == pytest.approx(0.1, abs=1e-9)
    assert res_override.safety_distance_m == pytest.approx(4.0, abs=1e-9)


def test_09_mesh_width_warning_above_5m():
    """9. Warning emitted when mesh_width_w_m > 5 m, and absent when mesh_width_w_m <= 5 m."""
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification(
        stroke_type="first_positive_10_350",
        peak_current_ka=100.0,
    )
    loop = InternalCableLoop(**_DEFAULT_LOOP_KWARGS)

    res_w10 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=10.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
        ),
        loop,
    )
    res_w5 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=5.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
        ),
        loop,
    )
    res_w2 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material="copper_aluminium",
        ),
        loop,
    )
    _assert_result_finite(res_w10)
    _assert_result_finite(res_w5)
    _assert_result_finite(res_w2)

    assert len(res_w10.warnings) == 1
    assert "5.0 m" in res_w10.warnings[0]
    assert res_w5.warnings == []
    assert res_w2.warnings == []


@pytest.mark.parametrize("material", ["copper_aluminium", "steel"])
def test_10_relative_permeability_mur_has_no_effect_on_k(material: str):
    """10. relative_permeability_mur = 200 leaves K identical to mu_r = 1."""
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification(
        stroke_type="first_positive_10_350",
        peak_current_ka=100.0,
    )
    loop = InternalCableLoop(**_DEFAULT_LOOP_KWARGS)

    res_mur_1 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material=material,
            relative_permeability_mur=1.0,
        ),
        loop,
    )
    res_mur_200 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            rod_radius_m=0.005,
            material=material,
            relative_permeability_mur=200.0,
        ),
        loop,
    )
    _assert_result_finite(res_mur_1)
    _assert_result_finite(res_mur_200)
    assert res_mur_200.grid_shielding_factor_kms == res_mur_1.grid_shielding_factor_kms
    assert res_mur_200.shielding_factor_db == res_mur_1.shielding_factor_db
    assert res_mur_200.peak_induced_voltage_kv == res_mur_1.peak_induced_voltage_kv


@pytest.mark.parametrize(
    "stroke_type",
    ["first_positive_10_350", "subsequent_negative_025_100"],
)
def test_11_peak_induced_voltage_independent_of_num_time_steps(stroke_type: str):
    """11. Peak induced voltage agrees within 0.5% across 500, 5000, and 50000 points."""
    engine = LEMPEngine()
    shield = ShieldingGrid(
        is_shielded=True,
        mesh_width_w_m=5.0,
        rod_radius_m=0.005,
        material="copper_aluminium",
    )
    loop = InternalCableLoop(**_DEFAULT_LOOP_KWARGS)

    peaks = {}
    for n_steps in (500, 5_000, 50_000):
        res = engine.calculate_lemp_induction(
            LEMPWaveformSpecification(
                stroke_type=stroke_type,
                peak_current_ka=100.0,
                t_end_us=100.0,
                num_time_steps=n_steps,
            ),
            shield,
            loop,
        )
        _assert_result_finite(res)
        peaks[n_steps] = res.peak_induced_voltage_kv

        expected_step = max(1, n_steps // 50)
        expected_len = len(range(0, n_steps, expected_step))
        assert len(res.time_series_us) == expected_len
        assert len(res.current_waveform_ka) == expected_len
        assert len(res.induced_voltage_waveform_kv) == expected_len

    assert peaks[500] == pytest.approx(peaks[50_000], rel=0.005)
    assert peaks[5_000] == pytest.approx(peaks[50_000], rel=0.005)
    assert peaks[500] == pytest.approx(peaks[5_000], rel=0.005)


@pytest.mark.parametrize(
    "stroke_type,peak_ka,t_end_us,n_steps,is_shielded,w_m,material,bonded,override_db",
    [
        ("first_positive_10_350", 0.1, 100.0, 500, True, 5.0, "copper_aluminium", False, None),
        ("first_positive_10_350", 200.0, 500.0, 2, True, 0.5, "steel", True, None),
        ("subsequent_negative_025_100", 50.0, 0.1, 2, True, 12.0, "steel", False, None),
        ("subsequent_negative_025_100", 100.0, 20.0, 5000, False, 5.0, "copper_aluminium", False, None),
        ("first_positive_10_350", 100.0, 100.0, 50, True, 2.0, "copper_aluminium", True, 15.0),
    ],
)
def test_12_no_nan_or_inf_for_any_input(
    stroke_type: str,
    peak_ka: float,
    t_end_us: float,
    n_steps: int,
    is_shielded: bool,
    w_m: float,
    material: str,
    bonded: bool,
    override_db: float | None,
):
    """12. No NaN or inf in any scalar or array field across valid edge and nominal inputs."""
    engine = LEMPEngine()
    res = engine.calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type=stroke_type,
            peak_current_ka=peak_ka,
            t_end_us=t_end_us,
            num_time_steps=n_steps,
        ),
        ShieldingGrid(
            is_shielded=is_shielded,
            mesh_width_w_m=w_m,
            rod_radius_m=0.005,
            material=material,
            meshed_bonding_network=bonded,
            shielding_factor_override_db=override_db,
        ),
        InternalCableLoop(
            loop_area_m2=0.01,
            center_distance_from_down_conductor_m=0.5,
            equipment_withstand_uw_kv=1.5,
        ),
    )
    _assert_result_finite(res)
    assert not np.any(np.isnan(res.induced_voltage_waveform_kv))
    assert not np.any(np.isinf(res.induced_voltage_waveform_kv))
    with pytest.raises(ValueError):
        _shielding_factor_db(0.0, 0.005, "first_positive_10_350", False, "copper_aluminium")
    with pytest.raises(ValueError):
        _shielding_factor_db(2.0, 0.0, "first_positive_10_350", False, "copper_aluminium")
    with pytest.raises(ValueError):
        LEMPWaveformSpecification(stroke_type="first_positive_10_350", peak_current_ka=0.0)
    with pytest.raises(ValueError):
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350", peak_current_ka=100.0, num_time_steps=1
        )
    with pytest.raises(ValueError):
        LEMPWaveformSpecification(stroke_type="unknown_stroke_fallback", peak_current_ka=100.0)
