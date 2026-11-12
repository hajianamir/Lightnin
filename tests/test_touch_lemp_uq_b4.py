"""Dedicated H9-B4 validation tests for touch_step.py, lemp_engine.py, and uq_engine.py.

Covers at least one reject test and at least one accept test for every rule:
- TouchStep (Rules A.1 through A.10)
- LEMP (Rules B.1 through B.6)
- UQ (Rules C.1 through C.6)
Plus HTTP API probes (422 on empty body, 200 on explicit valid body).
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from aegislps_api.main import app
from aegislps_engine.touch_step import TouchStepAssessmentInput, TouchStepEngine
from aegislps_engine.lemp_engine import (
    InternalCableLoop,
    LEMPEngine,
    LEMPWaveformSpecification,
    ShieldingGrid,
    _shielding_factor_db,
)
from aegislps_engine.uq_engine import (
    UQInputDistribution,
    UQSimulationConfig,
    UncertaintyQuantificationEngine,
)

client = TestClient(app)


def _valid_ts_kwargs(**overrides):
    base = dict(
        lps_class="I",
        soil_resistivity_ohm_m=100.0,
        surface_layer_material="bare_soil",
        fault_duration_s=0.05,
        body_weight_kg=70.0,
        peak_impulse_current_ka=100.0,
        down_conductor_radius_m=0.005,
        earth_potential_rise_v=10000.0,
        electrode_equivalent_radius_m=2.0,
    )
    base.update(overrides)
    return base


def _valid_lemp_parts():
    waveform = LEMPWaveformSpecification(
        stroke_type="first_positive_10_350",
        peak_current_ka=100.0,
    )
    shield = ShieldingGrid(
        is_shielded=True,
        mesh_width_w_m=5.0,
        rod_radius_m=0.005,
        material="copper_aluminium",
    )
    loop = InternalCableLoop(
        loop_area_m2=2.0,
        center_distance_from_down_conductor_m=3.0,
        equipment_withstand_uw_kv=1.5,
    )
    return waveform, shield, loop


def _valid_uq_kwargs(**overrides):
    base = dict(
        lps_class="I",
        target_clearance_d_m=1.0,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0,
        ring_radius_m=15.0,
    )
    base.update(overrides)
    return base


# ============================================================================
# Section A: touch_step.py (Rules A.1 - A.10)
# ============================================================================


def test_a1_lps_class_reject():
    kw = _valid_ts_kwargs()
    kw.pop("lps_class")
    with pytest.raises(ValueError, match="lps_class"):
        TouchStepAssessmentInput(**kw)

    for bad in ("V", "0", "", None, 1, True):
        with pytest.raises(ValueError, match="LPS class"):
            TouchStepAssessmentInput(**_valid_ts_kwargs(lps_class=bad))

    bad_obj = TouchStepAssessmentInput.model_construct(**_valid_ts_kwargs(lps_class="V"))
    with pytest.raises(ValueError, match="LPS class"):
        TouchStepEngine().evaluate(bad_obj)


def test_a1_lps_class_accept():
    engine = TouchStepEngine()
    results = [
        engine.evaluate(TouchStepAssessmentInput(**_valid_ts_kwargs(lps_class=cls)))
        for cls in ("I", "II", "III", "IV")
    ]
    # Unused in evaluate(); all 4 classes yield identical touch/step voltages
    assert len({r.tolerable_touch_voltage_v for r in results}) == 1
    assert len({r.prospective_touch_voltage_v for r in results}) == 1


def test_a2_soil_resistivity_reject():
    kw = _valid_ts_kwargs()
    kw.pop("soil_resistivity_ohm_m")
    with pytest.raises(ValueError, match="soil_resistivity_ohm_m"):
        TouchStepAssessmentInput(**kw)

    for bad in (0.0, -50.0, float("nan"), float("inf"), float("-inf"), True, False):
        with pytest.raises(ValueError):
            TouchStepAssessmentInput(**_valid_ts_kwargs(soil_resistivity_ohm_m=bad))


def test_a2_soil_resistivity_accept():
    engine = TouchStepEngine()
    r50 = engine.evaluate(TouchStepAssessmentInput(**_valid_ts_kwargs(soil_resistivity_ohm_m=50.0)))
    r200 = engine.evaluate(TouchStepAssessmentInput(**_valid_ts_kwargs(soil_resistivity_ohm_m=200.0)))
    assert r200.tolerable_touch_voltage_v > r50.tolerable_touch_voltage_v


def test_a3_surface_layer_material_reject():
    kw = _valid_ts_kwargs()
    kw.pop("surface_layer_material")
    with pytest.raises(ValueError, match="surface_layer_material"):
        TouchStepAssessmentInput(**kw)

    for bad in ("crushed_rock", "", None, 1, True):
        with pytest.raises(ValueError, match="surface_layer_material"):
            TouchStepAssessmentInput(**_valid_ts_kwargs(surface_layer_material=bad))

    bad_obj = TouchStepAssessmentInput.model_construct(
        **_valid_ts_kwargs(surface_layer_material="crushed_rock")
    )
    with pytest.raises(ValueError, match="surface_layer_material"):
        TouchStepEngine().evaluate(bad_obj)


def test_a3_surface_layer_material_accept():
    engine = TouchStepEngine()
    res_bare = engine.evaluate(
        TouchStepAssessmentInput(**_valid_ts_kwargs(surface_layer_material="bare_soil"))
    )
    assert res_bare.surface_derating_factor_cs == 1.0

    for mat in ("gravel_5cm", "asphalt_5cm", "concrete"):
        res = engine.evaluate(
            TouchStepAssessmentInput(
                **_valid_ts_kwargs(
                    surface_layer_material=mat,
                    surface_layer_resistivity_ohm_m=2500.0,
                )
            )
        )
        assert 0.1 <= res.surface_derating_factor_cs < 1.0


def test_a4_surface_layer_thickness_reject():
    for bad in (-0.01, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            TouchStepAssessmentInput(**_valid_ts_kwargs(surface_layer_thickness_m=bad))

    # Non-bare-soil with h_s == 0 must raise ValueError (no silent C_s = 1.0)
    for mat in ("gravel_5cm", "asphalt_5cm", "concrete"):
        with pytest.raises(ValueError, match="surface_layer_thickness_m"):
            TouchStepAssessmentInput(
                **_valid_ts_kwargs(
                    surface_layer_material=mat,
                    surface_layer_thickness_m=0.0,
                    surface_layer_resistivity_ohm_m=3000.0,
                )
            )

    with pytest.raises(ValueError, match="h_surface_m"):
        TouchStepEngine.calculate_surface_derating_cs(100.0, 3000.0, 0.0)

    bad_engine_inp = TouchStepAssessmentInput.model_construct(
        **_valid_ts_kwargs(
            surface_layer_material="gravel_5cm",
            surface_layer_thickness_m=0.0,
            surface_layer_resistivity_ohm_m=3000.0,
        )
    )
    with pytest.raises(ValueError, match="surface_layer_thickness_m"):
        TouchStepEngine().evaluate(bad_engine_inp)


def test_a4_surface_layer_thickness_accept():
    engine = TouchStepEngine()
    # Default 0.05 m preserved for non-bare-soil
    inp_default_hs = TouchStepAssessmentInput(
        **_valid_ts_kwargs(
            surface_layer_material="gravel_5cm",
            surface_layer_resistivity_ohm_m=3000.0,
        )
    )
    assert inp_default_hs.surface_layer_thickness_m == 0.05
    res_gravel = engine.evaluate(inp_default_hs)
    expected_cs = 1.0 - 0.09 * (1.0 - 100.0 / 3000.0) / (2.0 * 0.05 + 0.09)
    assert res_gravel.surface_derating_factor_cs == round(expected_cs, 3)

    # bare_soil allows h_s >= 0 and always sets C_s = 1.0 per IEEE Std 80-2013 Clause 8.4
    res_bare_zero = engine.evaluate(
        TouchStepAssessmentInput(
            **_valid_ts_kwargs(
                surface_layer_material="bare_soil",
                surface_layer_thickness_m=0.0,
            )
        )
    )
    assert res_bare_zero.surface_derating_factor_cs == 1.0


def test_a5_surface_layer_resistivity_reject():
    # Required when surface_layer_material != "bare_soil"
    for mat in ("gravel_5cm", "asphalt_5cm", "concrete"):
        with pytest.raises(ValueError, match="surface_layer_resistivity_ohm_m"):
            TouchStepAssessmentInput(**_valid_ts_kwargs(surface_layer_material=mat))

    for bad in (0.0, -100.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            TouchStepAssessmentInput(
                **_valid_ts_kwargs(
                    surface_layer_material="gravel_5cm",
                    surface_layer_resistivity_ohm_m=bad,
                )
            )


def test_a5_surface_layer_resistivity_accept_without_floors():
    """Measured resistivities below former 3000/10000/1000 floors are honored verbatim."""
    engine = TouchStepEngine()
    cases = [
        ("gravel_5cm", 1500.0),   # < former 3000.0 floor
        ("asphalt_5cm", 4000.0),  # < former 10000.0 floor
        ("concrete", 500.0),      # < former 1000.0 floor
    ]
    for mat, rho_s in cases:
        res = engine.evaluate(
            TouchStepAssessmentInput(
                **_valid_ts_kwargs(
                    surface_layer_material=mat,
                    surface_layer_thickness_m=0.05,
                    surface_layer_resistivity_ohm_m=rho_s,
                    fault_duration_s=0.05,
                    body_weight_kg=70.0,
                )
            )
        )
        cs_exact = 1.0 - 0.09 * (1.0 - 100.0 / rho_s) / (2.0 * 0.05 + 0.09)
        kt = 0.157 / math.sqrt(0.05)
        expected_touch = round((1000.0 + 1.5 * cs_exact * rho_s) * kt, 1)
        assert res.tolerable_touch_voltage_v == expected_touch


def test_a6_fault_duration_reject():
    kw = _valid_ts_kwargs()
    kw.pop("fault_duration_s")
    with pytest.raises(ValueError, match="fault_duration_s"):
        TouchStepAssessmentInput(**kw)

    for bad in (0.029, 0.01, 0.0, -0.5, 3.001, 10.0, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            TouchStepAssessmentInput(**_valid_ts_kwargs(fault_duration_s=bad))


def test_a6_fault_duration_accept():
    engine = TouchStepEngine()
    res_min = engine.evaluate(TouchStepAssessmentInput(**_valid_ts_kwargs(fault_duration_s=0.03)))
    res_max = engine.evaluate(TouchStepAssessmentInput(**_valid_ts_kwargs(fault_duration_s=3.0)))
    assert res_min.tolerable_touch_voltage_v > res_max.tolerable_touch_voltage_v


def test_a7_body_weight_reject():
    kw = _valid_ts_kwargs()
    kw.pop("body_weight_kg")
    with pytest.raises(ValueError, match="body_weight_kg"):
        TouchStepAssessmentInput(**kw)

    for bad in (60.0, 75.0, 80.0, 0.0, -50.0, float("nan"), True, False):
        with pytest.raises(ValueError):
            TouchStepAssessmentInput(**_valid_ts_kwargs(body_weight_kg=bad))


def test_a7_body_weight_accept():
    engine = TouchStepEngine()
    res_50 = engine.evaluate(TouchStepAssessmentInput(**_valid_ts_kwargs(body_weight_kg=50.0)))
    res_70 = engine.evaluate(TouchStepAssessmentInput(**_valid_ts_kwargs(body_weight_kg=70.0)))
    assert res_70.tolerable_touch_voltage_v > res_50.tolerable_touch_voltage_v


def test_a8_unused_impulse_and_conductor_fields_reject():
    for field in ("peak_impulse_current_ka", "down_conductor_radius_m"):
        kw = _valid_ts_kwargs()
        kw.pop(field)
        with pytest.raises(ValueError, match=field):
            TouchStepAssessmentInput(**kw)

        for bad in (0.0, -1.0, float("nan"), float("inf"), True, False):
            with pytest.raises(ValueError):
                TouchStepAssessmentInput(**_valid_ts_kwargs(**{field: bad}))


def test_a8_unused_impulse_and_conductor_fields_accept():
    engine = TouchStepEngine()
    r1 = engine.evaluate(
        TouchStepAssessmentInput(
            **_valid_ts_kwargs(peak_impulse_current_ka=50.0, down_conductor_radius_m=0.004)
        )
    )
    r2 = engine.evaluate(
        TouchStepAssessmentInput(
            **_valid_ts_kwargs(peak_impulse_current_ka=200.0, down_conductor_radius_m=0.010)
        )
    )
    assert r1.tolerable_touch_voltage_v == r2.tolerable_touch_voltage_v
    assert r1.prospective_touch_voltage_v == r2.prospective_touch_voltage_v


def test_a9_mitigation_flags_reject():
    for field in ("has_physical_insulation_barrier", "has_restricted_access_perimeter"):
        for bad in (1, 0, "true", "false", None):
            with pytest.raises(ValueError):
                TouchStepAssessmentInput(**_valid_ts_kwargs(**{field: bad}))


def test_a9_mitigation_flags_accept():
    inp_defaults = TouchStepAssessmentInput(**_valid_ts_kwargs())
    assert inp_defaults.has_physical_insulation_barrier is False
    assert inp_defaults.has_restricted_access_perimeter is False

    res = TouchStepEngine().evaluate(
        TouchStepAssessmentInput(
            **_valid_ts_kwargs(
                has_physical_insulation_barrier=True,
                has_restricted_access_perimeter=True,
            )
        )
    )
    assert res.mitigation_credit_applied is False


def test_a10_gpr_and_equivalent_radius_reject():
    for field in ("earth_potential_rise_v", "electrode_equivalent_radius_m"):
        kw = _valid_ts_kwargs()
        kw.pop(field)
        with pytest.raises(ValueError, match=field):
            TouchStepAssessmentInput(**kw)

        for bad in (None, 0.0, -10.0, float("nan"), float("inf"), True, False):
            with pytest.raises(ValueError):
                TouchStepAssessmentInput(**_valid_ts_kwargs(**{field: bad}))


def test_a10_gpr_and_equivalent_radius_accept():
    res = TouchStepEngine().evaluate(
        TouchStepAssessmentInput(
            **_valid_ts_kwargs(
                earth_potential_rise_v=5000.0,
                electrode_equivalent_radius_m=2.5,
            )
        )
    )
    assert res.prospective_touch_voltage_v == pytest.approx(5000.0 - 5000.0 * 2.5 / 3.5, abs=0.1)


# ============================================================================
# Section B: lemp_engine.py (Rules B.1 - B.6)
# ============================================================================


def test_b1_stroke_type_reject():
    with pytest.raises(ValueError, match="stroke_type"):
        LEMPWaveformSpecification(peak_current_ka=100.0)

    for bad in ("10_350", "", None, 1, True):
        with pytest.raises(ValueError, match="stroke_type"):
            LEMPWaveformSpecification(stroke_type=bad, peak_current_ka=100.0)
        with pytest.raises(ValueError, match="stroke_type"):
            LEMPEngine.evaluate_heidler_current(np.linspace(0, 10, 10), bad, 100.0)


def test_b1_stroke_type_accept():
    for stroke in ("first_positive_10_350", "subsequent_negative_025_100"):
        wf = LEMPWaveformSpecification(stroke_type=stroke, peak_current_ka=100.0)
        assert wf.stroke_type == stroke


def test_b2_peak_current_ka_reject():
    with pytest.raises(ValueError, match="peak_current_ka"):
        LEMPWaveformSpecification(stroke_type="first_positive_10_350")

    for bad in (0.0, -100.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            LEMPWaveformSpecification(stroke_type="first_positive_10_350", peak_current_ka=bad)
        with pytest.raises(ValueError):
            LEMPEngine.evaluate_heidler_current(
                np.linspace(0, 10, 10), "first_positive_10_350", bad
            )


def test_b2_peak_current_ka_accept():
    _, shield, loop = _valid_lemp_parts()
    res_50 = LEMPEngine().calculate_lemp_induction(
        LEMPWaveformSpecification(stroke_type="first_positive_10_350", peak_current_ka=50.0),
        shield,
        loop,
    )
    res_100 = LEMPEngine().calculate_lemp_induction(
        LEMPWaveformSpecification(stroke_type="first_positive_10_350", peak_current_ka=100.0),
        shield,
        loop,
    )
    assert res_100.peak_induced_voltage_kv == pytest.approx(2.0 * res_50.peak_induced_voltage_kv, abs=2e-3)


def test_b3_simulation_window_reject():
    for bad_tend in (0.0, -5.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            LEMPWaveformSpecification(
                stroke_type="first_positive_10_350",
                peak_current_ka=100.0,
                t_end_us=bad_tend,
            )

    for bad_steps in (1, 0, -10, True, False, 100.5, "500"):
        with pytest.raises(ValueError):
            LEMPWaveformSpecification(
                stroke_type="first_positive_10_350",
                peak_current_ka=100.0,
                num_time_steps=bad_steps,
            )


def test_b3_simulation_window_accept():
    wf_default = LEMPWaveformSpecification(
        stroke_type="first_positive_10_350", peak_current_ka=100.0
    )
    assert wf_default.t_end_us == 100.0
    assert wf_default.num_time_steps == 500

    _, shield, loop = _valid_lemp_parts()
    res_min = LEMPEngine().calculate_lemp_induction(
        LEMPWaveformSpecification(
            stroke_type="first_positive_10_350",
            peak_current_ka=100.0,
            t_end_us=25.0,
            num_time_steps=2,
        ),
        shield,
        loop,
    )
    assert len(res_min.time_series_us) == 2


def test_b4_shielding_grid_is_shielded_reject():
    with pytest.raises(ValueError, match="is_shielded"):
        ShieldingGrid()

    for bad in (1, 0, "true", None):
        with pytest.raises(ValueError, match="is_shielded"):
            ShieldingGrid(is_shielded=bad)


def test_b4_shielding_grid_is_shielded_accept():
    wf, _, loop = _valid_lemp_parts()
    unshielded = ShieldingGrid(is_shielded=False)
    res_unshielded = LEMPEngine().calculate_lemp_induction(wf, unshielded, loop)
    assert res_unshielded.grid_shielding_factor_kms == 1.0

    shielded = ShieldingGrid(
        is_shielded=True,
        mesh_width_w_m=2.0,
        rod_radius_m=0.005,
        material="copper_aluminium",
    )
    res_shielded = LEMPEngine().calculate_lemp_induction(wf, shielded, loop)
    assert res_shielded.grid_shielding_factor_kms < 1.0


def test_b5_shielded_parameters_reject():
    # Missing required shielded fields
    with pytest.raises(ValueError, match="mesh_width_w_m"):
        ShieldingGrid(is_shielded=True, rod_radius_m=0.005, material="copper_aluminium")
    with pytest.raises(ValueError, match="rod_radius_m"):
        ShieldingGrid(is_shielded=True, mesh_width_w_m=2.0, material="copper_aluminium")
    with pytest.raises(ValueError, match="material"):
        ShieldingGrid(is_shielded=True, mesh_width_w_m=2.0, rod_radius_m=0.005)

    # Invalid values
    for bad_num in (0.0, -1.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            ShieldingGrid(
                is_shielded=True,
                mesh_width_w_m=bad_num,
                rod_radius_m=0.005,
                material="copper_aluminium",
            )
        with pytest.raises(ValueError):
            ShieldingGrid(
                is_shielded=True,
                mesh_width_w_m=2.0,
                rod_radius_m=bad_num,
                material="copper_aluminium",
            )
        with pytest.raises(ValueError):
            ShieldingGrid(is_shielded=False, relative_permeability_mur=bad_num)

    for bad_mat in ("iron", "copper", "", True):
        with pytest.raises(ValueError, match="material"):
            ShieldingGrid(
                is_shielded=True,
                mesh_width_w_m=2.0,
                rod_radius_m=0.005,
                material=bad_mat,
            )
        with pytest.raises(ValueError, match="material"):
            _shielding_factor_db(2.0, 0.005, "first_positive_10_350", False, bad_mat)


def test_b5_shielded_parameters_accept():
    g_cu = ShieldingGrid(
        is_shielded=True,
        mesh_width_w_m=2.0,
        rod_radius_m=0.005,
        material="copper_aluminium",
    )
    assert g_cu.relative_permeability_mur == 1.0

    g_st = ShieldingGrid(
        is_shielded=True,
        mesh_width_w_m=2.0,
        rod_radius_m=0.005,
        material="steel",
        relative_permeability_mur=200.0,
    )
    assert g_st.material == "steel"


def test_b6_internal_cable_loop_reject():
    base = dict(
        loop_area_m2=2.0,
        center_distance_from_down_conductor_m=3.0,
        equipment_withstand_uw_kv=1.5,
    )
    for field in base:
        kw = dict(base)
        kw.pop(field)
        with pytest.raises(ValueError, match=field):
            InternalCableLoop(**kw)

        for bad in (0.0, -1.0, float("nan"), float("inf"), True, False):
            bad_kw = dict(base, **{field: bad})
            with pytest.raises(ValueError):
                InternalCableLoop(**bad_kw)


def test_b6_internal_cable_loop_accept_without_clamps():
    """Values below former clamps (a_loop < 0.01 m^2, s_a < 0.5 m) scale linearly without clamping."""
    wf = LEMPWaveformSpecification(
        stroke_type="subsequent_negative_025_100", peak_current_ka=100.0
    )
    shield = ShieldingGrid(is_shielded=False)
    engine = LEMPEngine()

    r_small_area = engine.calculate_lemp_induction(
        wf,
        shield,
        InternalCableLoop(
            loop_area_m2=0.002,
            center_distance_from_down_conductor_m=1.0,
            equipment_withstand_uw_kv=1.5,
        ),
    )
    r_ten_area = engine.calculate_lemp_induction(
        wf,
        shield,
        InternalCableLoop(
            loop_area_m2=0.02,
            center_distance_from_down_conductor_m=1.0,
            equipment_withstand_uw_kv=1.5,
        ),
    )
    assert r_ten_area.peak_induced_voltage_kv == pytest.approx(
        10.0 * r_small_area.peak_induced_voltage_kv, abs=0.01
    )

    r_close_sa = engine.calculate_lemp_induction(
        wf,
        shield,
        InternalCableLoop(
            loop_area_m2=1.0,
            center_distance_from_down_conductor_m=0.1,
            equipment_withstand_uw_kv=1.5,
        ),
    )
    r_half_sa = engine.calculate_lemp_induction(
        wf,
        shield,
        InternalCableLoop(
            loop_area_m2=1.0,
            center_distance_from_down_conductor_m=0.5,
            equipment_withstand_uw_kv=1.5,
        ),
    )
    assert r_close_sa.unattenuated_peak_h_field_a_per_m == pytest.approx(
        5.0 * r_half_sa.unattenuated_peak_h_field_a_per_m, rel=1e-3
    )


# ============================================================================
# Section C: uq_engine.py (Rules C.1 - C.6)
# ============================================================================


def test_c1_uq_input_distribution_reject():
    for field in ("std_dev", "shape_k", "scale_lambda"):
        for bad in (0.0, -1.0, float("nan"), float("inf"), True, False):
            with pytest.raises(ValueError):
                UQInputDistribution(
                    parameter_name="soil_rho",
                    mean=100.0,
                    **{field: bad},
                )

    for bad_mean in (float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            UQInputDistribution(parameter_name="soil_rho", mean=bad_mean)

    with pytest.raises(ValueError, match="min_val"):
        UQInputDistribution(
            parameter_name="soil_rho", mean=100.0, min_val=50.0, max_val=10.0
        )


def test_c1_uq_input_distribution_accept():
    dist_default = UQInputDistribution(parameter_name="soil_rho", mean=100.0)
    assert dist_default.std_dev == 0.1
    assert dist_default.shape_k == 2.0
    assert dist_default.scale_lambda == 100.0

    dist_custom = UQInputDistribution(
        parameter_name="flash_density",
        distribution_type="weibull",
        mean=4.0,
        std_dev=0.5,
        shape_k=1.5,
        scale_lambda=10.0,
        min_val=0.1,
        max_val=20.0,
    )
    assert dist_custom.scale_lambda == 10.0


def test_c2_num_samples_reject():
    for bad in (99, 1, 0, -100, True, False, 250.5, "2000"):
        with pytest.raises(ValueError, match="num_samples"):
            UQSimulationConfig(**_valid_uq_kwargs(num_samples=bad))

    bad_cfg = UQSimulationConfig.model_construct(**_valid_uq_kwargs(num_samples=50))
    with pytest.raises(ValueError, match="num_samples"):
        UncertaintyQuantificationEngine().run_monte_carlo(bad_cfg)


def test_c2_num_samples_accept():
    cfg_default = UQSimulationConfig(**_valid_uq_kwargs())
    assert cfg_default.num_samples == 2000

    res_100 = UncertaintyQuantificationEngine().run_monte_carlo(
        UQSimulationConfig(**_valid_uq_kwargs(num_samples=100))
    )
    assert res_100.num_samples == 100


def test_c3_random_seed_reject():
    for bad in (-1, 2**32, True, False, 42.5, "42"):
        with pytest.raises(ValueError, match="random_seed"):
            UQSimulationConfig(**_valid_uq_kwargs(random_seed=bad))

    bad_cfg = UQSimulationConfig.model_construct(**_valid_uq_kwargs(random_seed=-5))
    with pytest.raises(ValueError, match="random_seed"):
        UncertaintyQuantificationEngine().run_monte_carlo(bad_cfg)


def test_c3_random_seed_accept():
    cfg_default = UQSimulationConfig(**_valid_uq_kwargs())
    assert cfg_default.random_seed == 42

    engine = UncertaintyQuantificationEngine()
    res_zero = engine.run_monte_carlo(
        UQSimulationConfig(**_valid_uq_kwargs(num_samples=100, random_seed=0))
    )
    res_max = engine.run_monte_carlo(
        UQSimulationConfig(**_valid_uq_kwargs(num_samples=100, random_seed=2**32 - 1))
    )
    assert res_zero.num_samples == 100
    assert res_max.num_samples == 100


def test_c4_lps_class_reject():
    kw = _valid_uq_kwargs()
    kw.pop("lps_class")
    with pytest.raises(ValueError, match="lps_class"):
        UQSimulationConfig(**kw)

    for bad in ("V", "", None, 1, True):
        with pytest.raises(ValueError, match="LPS class"):
            UQSimulationConfig(**_valid_uq_kwargs(lps_class=bad))

    bad_cfg = UQSimulationConfig.model_construct(**_valid_uq_kwargs(lps_class="V"))
    with pytest.raises(ValueError, match="LPS class"):
        UncertaintyQuantificationEngine().run_monte_carlo(bad_cfg)


def test_c4_lps_class_accept():
    engine = UncertaintyQuantificationEngine()
    res_i = engine.run_monte_carlo(
        UQSimulationConfig(**_valid_uq_kwargs(num_samples=200, lps_class="I"))
    )
    res_iv = engine.run_monte_carlo(
        UQSimulationConfig(**_valid_uq_kwargs(num_samples=200, lps_class="IV"))
    )
    assert res_i.mean_s_req_m == pytest.approx(2.0 * res_iv.mean_s_req_m, abs=2e-3)


def test_c5_uq_geometry_and_soil_fields_reject():
    for field in (
        "target_clearance_d_m",
        "nominal_path_length_m",
        "nominal_soil_rho_ohm_m",
        "ring_radius_m",
    ):
        kw = _valid_uq_kwargs()
        kw.pop(field)
        with pytest.raises(ValueError, match=field):
            UQSimulationConfig(**kw)

    for bad_d in (-0.01, -5.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            UQSimulationConfig(**_valid_uq_kwargs(target_clearance_d_m=bad_d))

    for field in ("nominal_path_length_m", "nominal_soil_rho_ohm_m", "ring_radius_m"):
        for bad in (0.0, -1.0, float("nan"), float("inf"), True, False):
            with pytest.raises(ValueError):
                UQSimulationConfig(**_valid_uq_kwargs(**{field: bad}))


def test_c5_uq_geometry_and_soil_fields_accept_without_clamps():
    """Values below former clamps (path_length < 1.0 m, soil_rho < 10.0 ohm.m) are honored verbatim."""
    engine = UncertaintyQuantificationEngine()
    res_l_small = engine.run_monte_carlo(
        UQSimulationConfig(
            num_samples=500,
            random_seed=42,
            lps_class="I",
            target_clearance_d_m=0.0,
            nominal_path_length_m=0.2,
            nominal_soil_rho_ohm_m=2.0,
            ring_radius_m=5.0,
        )
    )
    res_l_unit = engine.run_monte_carlo(
        UQSimulationConfig(
            num_samples=500,
            random_seed=42,
            lps_class="I",
            target_clearance_d_m=0.0,
            nominal_path_length_m=1.0,
            nominal_soil_rho_ohm_m=10.0,
            ring_radius_m=5.0,
        )
    )
    assert res_l_small.mean_s_req_m < res_l_unit.mean_s_req_m
    assert res_l_unit.mean_s_req_m == pytest.approx(5.0 * res_l_small.mean_s_req_m, abs=5e-3)
    assert res_l_unit.earthing_p95_resistance_ohm == pytest.approx(
        5.0 * res_l_small.earthing_p95_resistance_ohm, abs=5e-2
    )


def test_c6_sobol_degenerate_zero_variance_reject(monkeypatch):
    engine = UncertaintyQuantificationEngine()
    cfg = UQSimulationConfig(**_valid_uq_kwargs(num_samples=100))

    monkeypatch.setattr(np, "var", lambda *args, **kwargs: 0.0)
    with pytest.raises(ValueError, match="var_total"):
        engine.run_monte_carlo(cfg)


def test_c6_sobol_small_variance_accept_without_hardcoded_fallback():
    """Small valid path length (var_total < 1e-8) computes true Sobol indices, not {0.5, 0.35, 0.15}."""
    engine = UncertaintyQuantificationEngine()
    res_tiny = engine.run_monte_carlo(
        UQSimulationConfig(
            **_valid_uq_kwargs(num_samples=500, random_seed=42, nominal_path_length_m=1e-4)
        )
    )
    res_nominal = engine.run_monte_carlo(
        UQSimulationConfig(
            **_valid_uq_kwargs(num_samples=500, random_seed=42, nominal_path_length_m=15.0)
        )
    )
    assert res_tiny.sobol_first_order_indices != {
        "conductor_length_l": 0.5,
        "current_sharing_kc": 0.35,
        "insulation_medium_km": 0.15,
    }
    assert res_tiny.sobol_first_order_indices == res_nominal.sobol_first_order_indices


# ============================================================================
# Section D: HTTP API Probes (422 on empty body, 200 on explicit valid body)
# ============================================================================


def test_http_probes_422_on_empty_and_200_on_valid():
    for path in (
        "/api/v1/calculations/touch-step",
        "/api/v1/calculations/lemp-induced-voltage",
        "/api/v1/calculations/uq-monte-carlo",
    ):
        r_empty = client.post(path, json={})
        assert r_empty.status_code == 422, f"{path} returned {r_empty.status_code} on empty body"

    r_ts = client.post("/api/v1/calculations/touch-step", json=_valid_ts_kwargs())
    assert r_ts.status_code == 200

    r_lemp = client.post(
        "/api/v1/calculations/lemp-induced-voltage",
        json={
            "waveform": {
                "stroke_type": "first_positive_10_350",
                "peak_current_ka": 100.0,
            },
            "shield": {
                "is_shielded": True,
                "mesh_width_w_m": 5.0,
                "rod_radius_m": 0.005,
                "material": "copper_aluminium",
            },
            "loop": {
                "loop_area_m2": 2.0,
                "center_distance_from_down_conductor_m": 3.0,
                "equipment_withstand_uw_kv": 1.5,
            },
        },
    )
    assert r_lemp.status_code == 200

    r_uq = client.post(
        "/api/v1/calculations/uq-monte-carlo",
        json=_valid_uq_kwargs(num_samples=200),
    )
    assert r_uq.status_code == 200
