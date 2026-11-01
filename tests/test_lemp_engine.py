import pytest
import numpy as np
from aegislps_engine.lemp_engine import (
    LEMPEngine,
    LEMPWaveformSpecification,
    ShieldingGrid,
    InternalCableLoop
)

def test_heidler_first_positive_stroke_properties():
    engine = LEMPEngine()
    t_us = np.linspace(0, 100, 1000)
    current_ka, di_dt, max_di_dt = engine.evaluate_heidler_current(
        t_us, "first_positive_10_350", 100.0
    )
    # Peak current must reach ~100 kA
    assert pytest.approx(np.max(current_ka), 0.05) == 100.0
    # Peak occurs around 10-20 us
    peak_time = t_us[np.argmax(current_ka)]
    assert 5.0 <= peak_time <= 25.0
    assert max_di_dt > 0.0

def test_heidler_subsequent_negative_stroke_steepness():
    engine = LEMPEngine()
    t_us = np.linspace(0, 20, 2000)
    _, _, max_di_dt_subsequent = engine.evaluate_heidler_current(
        t_us, "subsequent_negative_025_100", 50.0
    )
    _, _, max_di_dt_first = engine.evaluate_heidler_current(
        t_us, "first_positive_10_350", 100.0
    )
    # Subsequent stroke has much faster rise time -> much higher di/dt
    assert max_di_dt_subsequent > max_di_dt_first

def test_lemp_induction_and_shielding_attenuation():
    engine = LEMPEngine()
    waveform = LEMPWaveformSpecification(
        stroke_type="first_positive_10_350",
        peak_current_ka=100.0,
        t_end_us=100.0
    )
    loop = InternalCableLoop(
        loop_area_m2=1.0,
        center_distance_from_down_conductor_m=2.0,
        equipment_withstand_uw_kv=1.5
    )

    # 1. Unshielded Case
    shield_none = ShieldingGrid(is_shielded=False)
    res_unshielded = engine.calculate_lemp_induction(waveform, shield_none, loop)
    assert res_unshielded.grid_shielding_factor_kms == 1.0
    assert res_unshielded.unattenuated_peak_h_field_a_per_m > 0
    assert res_unshielded.shielded_peak_h_field_a_per_m == res_unshielded.unattenuated_peak_h_field_a_per_m

    # 2. Shielded Mesh Case (w = 2m mesh)
    shield_mesh = ShieldingGrid(is_shielded=True, mesh_width_w_m=2.0)
    res_shielded = engine.calculate_lemp_induction(waveform, shield_mesh, loop)
    # K_MS = 0.01 * 2m = 0.02
    assert res_shielded.grid_shielding_factor_kms == pytest.approx(0.02, 0.005)
    # Peak induced voltage should be reduced significantly
    assert res_shielded.peak_induced_voltage_kv < res_unshielded.peak_induced_voltage_kv
    assert len(res_shielded.current_waveform_ka) > 0
    assert len(res_shielded.induced_voltage_waveform_kv) > 0
