"""Physics and regression tests for TouchStepEngine (Step 1.3: C2; updated for H9-B4)."""

import itertools
import math
import pytest

from aegislps_engine.touch_step import TouchStepAssessmentInput, TouchStepEngine

EXPECTED_MITIGATION_WARNING = (
    "Mitigation flags are recommendations only. Any reduction credit requires "
    "engineer verification and is NOT applied in this calculation."
)

_BASE_TS_KWARGS = dict(
    lps_class="I",
    soil_resistivity_ohm_m=100.0,
    surface_layer_material="bare_soil",
    fault_duration_s=0.05,
    body_weight_kg=70.0,
    peak_impulse_current_ka=100.0,
    down_conductor_radius_m=0.005,
)


def test_gpr_and_equivalent_radius_required():
    """5.1: Missing or non-positive GPR / equivalent radius raises ValueError at model construction."""
    with pytest.raises(ValueError, match="earth_potential_rise_v"):
        TouchStepAssessmentInput(
            **_BASE_TS_KWARGS,
            electrode_equivalent_radius_m=2.0,
        )

    with pytest.raises(ValueError, match="electrode_equivalent_radius_m"):
        TouchStepAssessmentInput(
            **_BASE_TS_KWARGS,
            earth_potential_rise_v=10000.0,
        )

    with pytest.raises(ValueError, match="-50"):
        TouchStepAssessmentInput(
            **_BASE_TS_KWARGS,
            earth_potential_rise_v=-50.0,
            electrode_equivalent_radius_m=2.0,
        )

    with pytest.raises(ValueError, match="0.0"):
        TouchStepAssessmentInput(
            **_BASE_TS_KWARGS,
            earth_potential_rise_v=10000.0,
            electrode_equivalent_radius_m=0.0,
        )


def test_manual_hemispherical_prospective_voltages():
    """5.2: GPR=10000 V, r_e=2.0 m -> U_touch,prosp=3333.333 V, U_step,prosp=1666.667 V (within 0.1 V)."""
    engine = TouchStepEngine()
    gpr = 10000.0
    r_e = 2.0
    res = engine.evaluate(
        TouchStepAssessmentInput(
            **_BASE_TS_KWARGS,
            earth_potential_rise_v=gpr,
            electrode_equivalent_radius_m=r_e,
        )
    )

    v_1 = gpr * r_e / (r_e + 1.0)
    v_2 = gpr * r_e / (r_e + 2.0)
    expected_touch = gpr - v_1  # 3333.333... V
    expected_step = v_1 - v_2   # 1666.667... V

    assert res.prospective_touch_voltage_v == pytest.approx(expected_touch, abs=0.1)
    assert res.prospective_step_voltage_v == pytest.approx(expected_step, abs=0.1)


def test_surface_derating_cs_closed_form_and_guards():
    """5.3: IEEE 80 Eq. 27 closed-form C_s = 0.700 for rho=100, rho_s=3000, h_s=0.1, guard at rho_s=rho, and rejection of non-positive inputs."""
    cs = TouchStepEngine.calculate_surface_derating_cs(
        rho_soil=100.0, rho_surface=3000.0, h_surface_m=0.1
    )
    assert cs == pytest.approx(0.700, abs=1e-3)

    assert TouchStepEngine.calculate_surface_derating_cs(100.0, 100.0, 0.1) == 1.0
    with pytest.raises(ValueError, match="rho_surface"):
        TouchStepEngine.calculate_surface_derating_cs(100.0, 0.0, 0.1)
    with pytest.raises(ValueError, match="h_surface_m"):
        TouchStepEngine.calculate_surface_derating_cs(100.0, 3000.0, 0.0)


def test_tolerable_limit_formula_oracle():
    """5.4: Tolerable touch/step limits match analytical IEEE 80 / Dalziel equations within 0.1 V."""
    engine = TouchStepEngine()
    t_f = 0.05
    rho_s = 100.0
    c_s = 1.0

    k_t_70 = 0.157 / math.sqrt(t_f)
    expected_touch_70 = (1000.0 + 1.5 * c_s * rho_s) * k_t_70
    expected_step_70 = (1000.0 + 6.0 * c_s * rho_s) * k_t_70

    res_70 = engine.evaluate(
        TouchStepAssessmentInput(
            lps_class="I",
            soil_resistivity_ohm_m=100.0,
            surface_layer_material="bare_soil",
            fault_duration_s=t_f,
            body_weight_kg=70.0,
            peak_impulse_current_ka=100.0,
            down_conductor_radius_m=0.005,
            earth_potential_rise_v=10000.0,
            electrode_equivalent_radius_m=2.0,
        )
    )
    assert res_70.tolerable_touch_voltage_v == pytest.approx(expected_touch_70, abs=0.1)
    assert res_70.tolerable_step_voltage_v == pytest.approx(expected_step_70, abs=0.1)

    k_t_50 = 0.116 / math.sqrt(t_f)
    expected_touch_50 = (1000.0 + 1.5 * c_s * rho_s) * k_t_50
    res_50 = engine.evaluate(
        TouchStepAssessmentInput(
            lps_class="I",
            soil_resistivity_ohm_m=100.0,
            surface_layer_material="bare_soil",
            fault_duration_s=t_f,
            body_weight_kg=50.0,
            peak_impulse_current_ka=100.0,
            down_conductor_radius_m=0.005,
            earth_potential_rise_v=10000.0,
            electrode_equivalent_radius_m=2.0,
        )
    )
    assert res_50.tolerable_touch_voltage_v == pytest.approx(expected_touch_50, abs=0.1)


def test_mitigation_flags_do_not_change_voltages():
    """5.5: Barrier and fence flags never alter prospective voltages and never apply credit."""
    engine = TouchStepEngine()
    base_kwargs = dict(
        **_BASE_TS_KWARGS,
        earth_potential_rise_v=10000.0,
        electrode_equivalent_radius_m=2.0,
    )

    res_none = engine.evaluate(TouchStepAssessmentInput(**base_kwargs))
    res_barrier = engine.evaluate(
        TouchStepAssessmentInput(has_physical_insulation_barrier=True, **base_kwargs)
    )
    res_fence = engine.evaluate(
        TouchStepAssessmentInput(has_restricted_access_perimeter=True, **base_kwargs)
    )

    assert (
        res_none.prospective_touch_voltage_v
        == res_barrier.prospective_touch_voltage_v
        == res_fence.prospective_touch_voltage_v
    )
    assert (
        res_none.prospective_step_voltage_v
        == res_barrier.prospective_step_voltage_v
        == res_fence.prospective_step_voltage_v
    )
    for res in (res_none, res_barrier, res_fence):
        assert res.mitigation_credit_applied is False


def test_fence_only_scenario_is_not_compliant():
    """5.6: Restricted-access fence flag alone does not turn a 10 kV GPR bare-soil hazard compliant."""
    engine = TouchStepEngine()
    res_fence = engine.evaluate(
        TouchStepAssessmentInput(
            **_BASE_TS_KWARGS,
            has_restricted_access_perimeter=True,
            earth_potential_rise_v=10000.0,
            electrode_equivalent_radius_m=2.0,
        )
    )
    assert res_fence.status != "COMPLIANT"
    assert res_fence.touch_hazard_controlled is False
    assert res_fence.step_hazard_controlled is False


def test_no_zero_by_flag_path():
    """5.7: Prospective touch and step voltages remain strictly positive across all flag combinations."""
    engine = TouchStepEngine()
    for barrier, fence in itertools.product([False, True], repeat=2):
        res = engine.evaluate(
            TouchStepAssessmentInput(
                **_BASE_TS_KWARGS,
                has_physical_insulation_barrier=barrier,
                has_restricted_access_perimeter=fence,
                earth_potential_rise_v=10000.0,
                electrode_equivalent_radius_m=2.0,
            )
        )
        # Hemispherical potential V(x) = GPR * r_e / (r_e + x) for GPR = 10000 V, r_e = 2.0 m:
        # U_touch,prosp = 10000 - 10000*(2/3) = 3333.3 V; U_step,prosp = 10000*(2/3 - 2/4) = 1666.7 V.
        assert res.prospective_touch_voltage_v == pytest.approx(3333.3, abs=0.1)
        assert res.prospective_step_voltage_v == pytest.approx(1666.7, abs=0.1)


def test_formula_trace_contains_equations_and_substituted_numbers():
    """5.8: formula_trace is non-empty and records equations and substituted numbers for V(1) and V(2)."""
    engine = TouchStepEngine()
    res = engine.evaluate(
        TouchStepAssessmentInput(
            **_BASE_TS_KWARGS,
            earth_potential_rise_v=10000.0,
            electrode_equivalent_radius_m=2.0,
        )
    )
    assert len(res.formula_trace) > 0

    v1_lines = [line for line in res.formula_trace if line.startswith("V(1)")]
    v2_lines = [line for line in res.formula_trace if line.startswith("V(2)")]
    assert len(v1_lines) == 1
    assert len(v2_lines) == 1

    assert "10000.00" in v1_lines[0]
    assert "2.0000" in v1_lines[0]
    assert "6666.67" in v1_lines[0]

    assert "10000.00" in v2_lines[0]
    assert "2.0000" in v2_lines[0]
    assert "5000.00" in v2_lines[0]


def test_mitigation_warning_exact_text_in_all_results():
    """5.9: Exact mitigation warning string appears in every result."""
    engine = TouchStepEngine()
    for barrier, fence in itertools.product([False, True], repeat=2):
        res = engine.evaluate(
            TouchStepAssessmentInput(
                **_BASE_TS_KWARGS,
                has_physical_insulation_barrier=barrier,
                has_restricted_access_perimeter=fence,
                earth_potential_rise_v=10000.0,
                electrode_equivalent_radius_m=2.0,
            )
        )
        assert res.mitigation_warning == EXPECTED_MITIGATION_WARNING
