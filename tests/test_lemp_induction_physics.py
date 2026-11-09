"""Physics and verification tests for LEMP induction, K_MS, and loop coupling (Step 1.5: C3-b)."""

import math
import numpy as np
import pytest
from pydantic import ValidationError

from aegislps_engine.lemp_engine import (
    K_MS_SOURCE,
    InternalCableLoop,
    LEMPEngine,
    LEMPTransientResult,
    LEMPWaveformSpecification,
    ShieldingGrid,
)


def _assert_result_finite(res: LEMPTransientResult) -> None:
    """Assert that every scalar and array output in LEMPTransientResult is finite."""
    for scalar in (
        res.peak_current_ka,
        res.max_di_dt_ka_per_us,
        res.unattenuated_peak_h_field_a_per_m,
        res.shielded_peak_h_field_a_per_m,
        res.grid_shielding_factor_kms,
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


def test_kms_source_flag_default_and_override():
    """D.1: K_MS source flag is UNVERIFIED for both default (conservative 1.0) and override."""
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification(
        stroke_type="first_positive_10_350",
        peak_current_ka=100.0,
        t_end_us=100.0,
    )
    loop = InternalCableLoop()

    # Default shielded case (no override): conservative K_MS = 1.0, source = UNVERIFIED
    res_default = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(is_shielded=True, mesh_width_w_m=5.0),
        loop,
    )
    _assert_result_finite(res_default)
    assert K_MS_SOURCE == "UNVERIFIED"
    assert res_default.kms_source == "UNVERIFIED"
    assert res_default.K_MS_SOURCE == "UNVERIFIED"
    assert res_default.grid_shielding_factor_kms == 1.0
    assert "conservative" in " ".join(res_default.engineering_insights).lower()

    # Explicit user override case: exact override value used, source remains UNVERIFIED
    override_kms = 0.0375
    res_override = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=5.0,
            shielding_factor_override=override_kms,
        ),
        loop,
    )
    _assert_result_finite(res_override)
    assert res_override.kms_source == "UNVERIFIED"
    assert res_override.K_MS_SOURCE == "UNVERIFIED"
    assert res_override.grid_shielding_factor_kms == override_kms
    assert res_override.shielded_peak_h_field_a_per_m == pytest.approx(
        res_default.unattenuated_peak_h_field_a_per_m * override_kms, abs=0.1
    )
    assert res_override.peak_induced_voltage_kv == pytest.approx(
        res_default.peak_induced_voltage_kv * override_kms, abs=1e-3
    )

    # Out-of-range overrides are rejected
    with pytest.raises(ValidationError):
        ShieldingGrid(shielding_factor_override=-0.1)
    with pytest.raises(ValidationError):
        ShieldingGrid(shielding_factor_override=1.5)


@pytest.mark.parametrize("override", [None, 0.15])
def test_no_mur_credit_without_verified_source(override: float | None):
    """D.2: relative_permeability_mur = 200 receives zero K_MS credit vs mu_r = 1."""
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification(
        stroke_type="subsequent_negative_025_100",
        peak_current_ka=50.0,
        t_end_us=100.0,
    )
    loop = InternalCableLoop()

    res_mur_1 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            relative_permeability_mur=1.0,
            shielding_factor_override=override,
        ),
        loop,
    )
    res_mur_200 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(
            is_shielded=True,
            mesh_width_w_m=2.0,
            relative_permeability_mur=200.0,
            shielding_factor_override=override,
        ),
        loop,
    )
    _assert_result_finite(res_mur_1)
    _assert_result_finite(res_mur_200)

    assert res_mur_200.grid_shielding_factor_kms == res_mur_1.grid_shielding_factor_kms
    assert res_mur_200.shielded_peak_h_field_a_per_m == res_mur_1.shielded_peak_h_field_a_per_m
    assert res_mur_200.peak_induced_voltage_kv == res_mur_1.peak_induced_voltage_kv


@pytest.mark.parametrize(
    "stroke_type",
    ["first_positive_10_350", "subsequent_negative_025_100"],
)
def test_peak_induced_voltage_grid_independence(stroke_type: str):
    """D.3 / B.3: Peak induced voltage agrees within 0.5% across 500, 5000, and 50000 steps."""
    engine = LEMPEngine()
    shield = ShieldingGrid(is_shielded=True, mesh_width_w_m=5.0)
    loop = InternalCableLoop()

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

        # Output waveform lists keep downsampling tied to num_time_steps
        expected_step = max(1, n_steps // 50)
        expected_len = len(range(0, n_steps, expected_step))
        assert len(res.time_series_us) == expected_len
        assert len(res.current_waveform_ka) == expected_len
        assert len(res.induced_voltage_waveform_kv) == expected_len

    assert peaks[500] == pytest.approx(peaks[50_000], rel=0.005)
    assert peaks[5_000] == pytest.approx(peaks[50_000], rel=0.005)
    assert peaks[500] == pytest.approx(peaks[5_000], rel=0.005)


def test_faraday_loop_model_comparison_documented_errors():
    """
    D.4 / C.1-C.2: Compare uniform-field area coupling against exact rectangular-loop
    mutual inductance M_exact = (mu_0 * a / (2 * pi)) * ln((d + b) / d).

    Documented relative errors (M_approx - M_exact) / M_exact:
    1) Inner-edge evaluation r = d, M_area(d) = mu_0 * a * b / (2 * pi * d):
       - b/d = 0.1 -> +4.9206%
       - b/d = 1.0 -> +44.2695%
       - b/d = 3.0 -> +116.4043%
    2) Center-distance evaluation r_c = d + b/2, M_area(r_c) = mu_0 * a * b / (2 * pi * r_c)
       (used by InternalCableLoop.center_distance_from_down_conductor_m):
       - b/d = 0.1 -> -0.0756%
       - b/d = 1.0 -> -3.8203%
       - b/d = 3.0 -> -13.4383%
    3) Default InternalCableLoop (loop_area_m2 = 2.0, center_distance = 3.0):
       For square loop a = b = sqrt(2) m (d = 3 - sqrt(2)/2 = 2.2929 m, b/d = 0.6168),
       engine coupling error is -1.8801% (well within the 10% replacement gate).
    """
    mu_0 = LEMPEngine.MU_0
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification(
        stroke_type="first_positive_10_350",
        peak_current_ka=100.0,
        t_end_us=100.0,
    )
    shield = ShieldingGrid(is_shielded=False)

    # Documented (ratio b/d, expected rel_err at r=d, expected rel_err at r_c=d+b/2)
    cases = [
        (0.1, +0.049206, -0.000756),
        (1.0, +0.442695, -0.038203),
        (3.0, +1.164043, -0.134383),
    ]

    for ratio_b_over_d, expected_err_inner, expected_err_center in cases:
        a_m = 2.0
        d_m = 2.0  # >= 0.5 m so r_m clamp in calculate_lemp_induction is inactive
        b_m = ratio_b_over_d * d_m
        area_m2 = a_m * b_m
        r_center_m = d_m + 0.5 * b_m

        m_exact = (mu_0 * a_m / (2.0 * math.pi)) * math.log((d_m + b_m) / d_m)
        m_area_inner = mu_0 * area_m2 / (2.0 * math.pi * d_m)
        m_area_center = mu_0 * area_m2 / (2.0 * math.pi * r_center_m)

        rel_err_inner = (m_area_inner - m_exact) / m_exact
        rel_err_center = (m_area_center - m_exact) / m_exact

        assert rel_err_inner == pytest.approx(expected_err_inner, abs=1e-5)
        assert rel_err_center == pytest.approx(expected_err_center, abs=1e-5)

        # Verify engine output matches M_area(r_center) * max_di_dt
        res = engine.calculate_lemp_induction(
            waveform,
            shield,
            InternalCableLoop(
                loop_area_m2=area_m2,
                center_distance_from_down_conductor_m=r_center_m,
            ),
        )
        _assert_result_finite(res)
        u_exact_kv = m_exact * (res.max_di_dt_ka_per_us * 1e9) * 1e-3
        u_engine_err = (res.peak_induced_voltage_kv - u_exact_kv) / u_exact_kv
        assert u_engine_err == pytest.approx(expected_err_center, abs=2e-3)

    # Default geometry gate check: loop_area_m2 = 2.0, center_distance = 3.0 (square loop)
    default_loop = InternalCableLoop()
    a_def = math.sqrt(default_loop.loop_area_m2)
    b_def = math.sqrt(default_loop.loop_area_m2)
    d_def = default_loop.center_distance_from_down_conductor_m - 0.5 * b_def
    m_exact_def = (mu_0 * a_def / (2.0 * math.pi)) * math.log((d_def + b_def) / d_def)
    m_engine_def = (
        mu_0
        * default_loop.loop_area_m2
        / (2.0 * math.pi * default_loop.center_distance_from_down_conductor_m)
    )
    rel_err_default = (m_engine_def - m_exact_def) / m_exact_def
    assert rel_err_default == pytest.approx(-0.018801, abs=1e-5)
    assert abs(rel_err_default) < 0.10


def test_mesh_width_warning_threshold():
    """D.5: mesh_width_w_m = 10 emits warning; mesh_width_w_m = 5 does not."""
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification()
    loop = InternalCableLoop()

    res_w10 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(is_shielded=True, mesh_width_w_m=10.0),
        loop,
    )
    _assert_result_finite(res_w10)
    assert len(res_w10.warnings) == 1
    assert "5.0 m" in res_w10.warnings[0]

    res_w5 = engine.calculate_lemp_induction(
        waveform,
        ShieldingGrid(is_shielded=True, mesh_width_w_m=5.0),
        loop,
    )
    _assert_result_finite(res_w5)
    assert res_w5.warnings == []


def test_unshielded_gives_unit_kms():
    """D.6: is_shielded = False always gives K_MS = 1.0."""
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification()
    loop = InternalCableLoop()

    for shield in (
        ShieldingGrid(is_shielded=False),
        ShieldingGrid(
            is_shielded=False,
            mesh_width_w_m=1.0,
            relative_permeability_mur=200.0,
            shielding_factor_override=0.05,
        ),
    ):
        res = engine.calculate_lemp_induction(waveform, shield, loop)
        _assert_result_finite(res)
        assert res.grid_shielding_factor_kms == 1.0
        assert res.shielded_peak_h_field_a_per_m == res.unattenuated_peak_h_field_a_per_m


@pytest.mark.parametrize(
    "stroke_type,peak_ka,t_end_us,n_steps,is_shielded,w_m,override",
    [
        ("first_positive_10_350", 0.0, 100.0, 500, True, 5.0, None),
        ("first_positive_10_350", 200.0, 500.0, 1, True, 0.5, 0.0),
        ("subsequent_negative_025_100", 50.0, 0.1, 2, True, 10.0, 1.0),
        ("subsequent_negative_025_100", 100.0, 20.0, 5000, False, 5.0, None),
        ("unknown_stroke_fallback", 100.0, 100.0, 50, True, 2.0, 0.25),
    ],
)
def test_no_nan_or_inf_across_diverse_inputs(
    stroke_type: str,
    peak_ka: float,
    t_end_us: float,
    n_steps: int,
    is_shielded: bool,
    w_m: float,
    override: float | None,
):
    """D.7: No NaN or inf in any scalar or array field across edge and nominal inputs."""
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
            shielding_factor_override=override,
        ),
        InternalCableLoop(
            loop_area_m2=0.001,
            center_distance_from_down_conductor_m=0.1,
            equipment_withstand_uw_kv=1.5,
        ),
    )
    _assert_result_finite(res)
    assert not np.any(np.isnan(res.induced_voltage_waveform_kv))
    assert not np.any(np.isinf(res.induced_voltage_waveform_kv))
