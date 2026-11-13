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
    # Analytic stationary point of Heidler 10/350 (IEC 62305-1 Table A.1: tau1=19 us, tau2=485 us,
    # eta=0.93, n=10): 10 / (t * (1 + (t/19)^10)) = 1 / 485 -> t_peak = 31.4278 us (grid step ~0.1001 us);
    # analytic peak di/dt = 13.6624 kA/us.
    peak_time = t_us[np.argmax(current_ka)]
    assert peak_time == pytest.approx(31.4278, abs=0.11)
    assert max_di_dt == pytest.approx(13.6624, rel=1e-3)

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

    # 1. Unshielded Case: IEC 62305-4:2024 Eq. (A.6) H_0,max = i_max / (2 * pi * s_a)
    # With Table A.1 Heidler i_max(31.4278 us) = 100.1271 kA and s_a = 2.0 m: H_0,max = 7967.86 A/m.
    shield_none = ShieldingGrid(is_shielded=False)
    res_unshielded = engine.calculate_lemp_induction(waveform, shield_none, loop)
    assert res_unshielded.grid_shielding_factor_kms == 1.0
    assert res_unshielded.unattenuated_peak_h_field_a_per_m == pytest.approx(7967.9, abs=0.2)
    assert res_unshielded.shielded_peak_h_field_a_per_m == res_unshielded.unattenuated_peak_h_field_a_per_m

    # 2. Shielded Mesh Case (w = 2m copper/alu mesh): IEC 62305-4:2024 Table A.4
    # SF = 20 * log10(8.5 / 2.0) = 12.5678 dB -> K_MS = 2.0 / 8.5 = 0.2353
    shield_mesh = ShieldingGrid(
        is_shielded=True,
        mesh_width_w_m=2.0,
        rod_radius_m=0.005,
        material="copper_aluminium",
    )
    res_shielded = engine.calculate_lemp_induction(waveform, shield_mesh, loop)
    assert res_shielded.grid_shielding_factor_kms == pytest.approx(0.2353, abs=0.001)
    # Faraday-Maxwell induced loop voltage (docs/35 §3.1) with K_MS = 2.0 / 8.5, A_loop = 1.0 m^2,
    # s_a = 2.0 m, max(di/dt) = 13.6624 kA/us:
    # u_peak = (mu_0 / (2*pi*2.0)) * (2.0/8.5) * 1.0 * 13.6624e9 * 1e-3 = 0.3215 kV
    assert res_shielded.peak_induced_voltage_kv == pytest.approx(0.3215, abs=2e-3)
    assert res_shielded.peak_induced_voltage_kv == pytest.approx(
        (2.0 / 8.5) * res_unshielded.peak_induced_voltage_kv, abs=2e-3
    )
    # Sanity check only (downsampled UI waveform length is an API serialization choice, not a standard value):
    assert len(res_shielded.current_waveform_ka) > 0
    # Sanity check only (downsampled UI waveform length is an API serialization choice, not a standard value):
    assert len(res_shielded.induced_voltage_waveform_kv) > 0
