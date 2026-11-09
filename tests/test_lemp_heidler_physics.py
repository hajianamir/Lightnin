"""Physics and numerical verification tests for Heidler waveforms in LEMPEngine (Step 1.4: C3)."""

import numpy as np
import pytest

from aegislps_engine.lemp_engine import HEIDLER_IEC_62305_1, LEMPEngine


def test_heidler_parameter_table_matches_iec_62305_1():
    """D.1: Module-level HEIDLER_IEC_62305_1 matches IEC 62305-1 Table A.1 values."""
    assert set(HEIDLER_IEC_62305_1.keys()) == {
        "first_positive_10_350",
        "subsequent_negative_025_100",
    }

    p_first = HEIDLER_IEC_62305_1["first_positive_10_350"]
    assert p_first == {
        "tau1": 19.0,
        "tau2": 485.0,
        "eta": 0.93,
        "n": 10.0,
    }

    p_sub = HEIDLER_IEC_62305_1["subsequent_negative_025_100"]
    assert p_sub == {
        "tau1": 0.454,
        "tau2": 143.0,
        "eta": 0.993,
        "n": 10.0,
    }


@pytest.mark.parametrize(
    "stroke_type,t_end_us",
    [
        ("first_positive_10_350", 100.0),
        ("subsequent_negative_025_100", 10.0),
    ],
)
def test_heidler_peak_current_within_one_percent(stroke_type: str, t_end_us: float):
    """D.2: Peak current max(i) lies within [0.99 * I, 1.01 * I] for I = 100 kA."""
    i_target = 100.0
    t_us = np.linspace(0.0, t_end_us, 50_000)
    current_ka, _, _ = LEMPEngine.evaluate_heidler_current(t_us, stroke_type, i_target)
    peak_i = float(np.max(current_ka))
    assert 0.99 * i_target <= peak_i <= 1.01 * i_target


def test_analytic_derivative_matches_numerical_gradient():
    """D.3: Analytic di/dt agrees with central finite-difference np.gradient."""
    # 10/350 stroke at 20,000 points on [0, 100 us] (dt = 0.005 us): rel diff ~ 6.1e-7 < 1e-3
    t_100 = np.linspace(0.0, 100.0, 20_000)
    dt_100 = float(t_100[1] - t_100[0])
    i_first, didt_first, _ = LEMPEngine.evaluate_heidler_current(
        t_100, "first_positive_10_350", 100.0
    )
    grad_first = np.gradient(i_first, dt_100)
    assert np.max(np.abs(didt_first - grad_first)) < 1e-3 * np.max(np.abs(didt_first))

    # 0.25/100 stroke (tau1 = 0.454 us): at 20,000 points on [0, 20 us] (dt = 0.001 us),
    # np.gradient O(dt^2) truncation error is 4.21e-5 * max|di/dt| < 1e-3; on [0, 100 us]
    # (dt = 0.005 us), np.gradient's 2nd-order truncation term |i'''|*dt^2/6 is 1.052e-3.
    t_20 = np.linspace(0.0, 20.0, 20_000)
    dt_20 = float(t_20[1] - t_20[0])
    i_sub_20, didt_sub_20, _ = LEMPEngine.evaluate_heidler_current(
        t_20, "subsequent_negative_025_100", 100.0
    )
    grad_sub_20 = np.gradient(i_sub_20, dt_20)
    assert np.max(np.abs(didt_sub_20 - grad_sub_20)) < 1e-3 * np.max(
        np.abs(didt_sub_20)
    )

    i_sub_100, didt_sub_100, _ = LEMPEngine.evaluate_heidler_current(
        t_100, "subsequent_negative_025_100", 100.0
    )
    grad_sub_100 = np.gradient(i_sub_100, dt_100)
    assert np.max(np.abs(didt_sub_100 - grad_sub_100)) < 1.1e-3 * np.max(
        np.abs(didt_sub_100)
    )


@pytest.mark.parametrize(
    "stroke_type",
    ["first_positive_10_350", "subsequent_negative_025_100"],
)
def test_max_di_dt_grid_independence(stroke_type: str):
    """D.4: max_di_dt across 500, 20,000, and 200,000 points differs by < 1e-6 relative."""
    values = []
    for n_pts in (500, 20_000, 200_000):
        t_us = np.linspace(0.0, 100.0, n_pts)
        _, _, max_di_dt = LEMPEngine.evaluate_heidler_current(t_us, stroke_type, 100.0)
        values.append(max_di_dt)

    ref = values[-1]
    for val in values:
        assert abs(val - ref) / ref < 1e-6


def test_max_di_dt_matches_reference_values():
    """D.5: Reference max di/dt checks for 10/350 (13.66 kA/us) and 0.25/100 (558 kA/us at 100 kA)."""
    t_us = np.linspace(0.0, 100.0, 2_000)

    _, _, max_first_100 = LEMPEngine.evaluate_heidler_current(
        t_us, "first_positive_10_350", 100.0
    )
    assert max_first_100 == pytest.approx(13.66, abs=0.05)

    _, _, max_sub_100 = LEMPEngine.evaluate_heidler_current(
        t_us, "subsequent_negative_025_100", 100.0
    )
    assert max_sub_100 == pytest.approx(558.0, abs=3.0)

    _, _, max_sub_50 = LEMPEngine.evaluate_heidler_current(
        t_us, "subsequent_negative_025_100", 50.0
    )
    assert max_sub_50 == pytest.approx(279.0, abs=1.5)


@pytest.mark.parametrize(
    "stroke_type",
    ["first_positive_10_350", "subsequent_negative_025_100"],
)
def test_zero_and_finite_for_nonpositive_times(stroke_type: str):
    """D.6: i(t) == 0 and di/dt == 0 for t <= 0, with no NaN or inf on grids starting at <= 0."""
    for grid in (
        np.linspace(0.0, 100.0, 500),
        np.linspace(-10.0, 100.0, 551),
        np.array([0.0]),
    ):
        current_ka, di_dt, max_di_dt = LEMPEngine.evaluate_heidler_current(
            grid, stroke_type, 100.0
        )
        assert np.all(np.isfinite(current_ka))
        assert np.all(np.isfinite(di_dt))
        assert np.isfinite(max_di_dt)

        nonpos_mask = grid <= 0.0
        assert np.all(current_ka[nonpos_mask] == 0.0)
        assert np.all(di_dt[nonpos_mask] == 0.0)


@pytest.mark.parametrize(
    "stroke_type,t_end_us",
    [
        ("first_positive_10_350", 60.0),
        ("subsequent_negative_025_100", 5.0),
    ],
)
def test_monotone_rising_front_up_to_peak(stroke_type: str, t_end_us: float):
    """D.7: Current i(t) is non-decreasing from t = 0 up to the peak time."""
    t_us = np.linspace(0.0, t_end_us, 10_000)
    current_ka, _, _ = LEMPEngine.evaluate_heidler_current(t_us, stroke_type, 100.0)
    peak_idx = int(np.argmax(current_ka))
    assert peak_idx > 0
    diffs = np.diff(current_ka[: peak_idx + 1])
    assert np.all(diffs >= 0.0)


def test_unknown_stroke_type_falls_back_to_first_positive():
    """D.8: Unrecognized stroke_type preserves current fallback to first_positive_10_350."""
    t_us = np.linspace(0.0, 100.0, 500)
    i_ref, didt_ref, max_ref = LEMPEngine.evaluate_heidler_current(
        t_us, "first_positive_10_350", 100.0
    )
    i_unk, didt_unk, max_unk = LEMPEngine.evaluate_heidler_current(
        t_us, "unrecognized_stroke_type", 100.0
    )
    assert np.array_equal(i_unk, i_ref)
    assert np.array_equal(didt_unk, didt_ref)
    assert max_unk == max_ref


def test_front_and_tail_time_definitions():
    """C: Verify IEC 10%-90% front time T1 = 1.25 * (t90 - t10) and T2 at 0.5 * I_peak on tail."""
    # 1. First positive 10/350 us (I = 100 kA)
    t_front_1 = np.linspace(0.0, 40.0, 200_000)
    i_front_1, _, _ = LEMPEngine.evaluate_heidler_current(
        t_front_1, "first_positive_10_350", 100.0
    )
    peak_idx_1 = int(np.argmax(i_front_1))
    i_peak_1 = float(i_front_1[peak_idx_1])
    t_rise_1 = t_front_1[: peak_idx_1 + 1]
    i_rise_1 = i_front_1[: peak_idx_1 + 1]
    t10_1 = float(np.interp(0.1 * i_peak_1, i_rise_1, t_rise_1))
    t90_1 = float(np.interp(0.9 * i_peak_1, i_rise_1, t_rise_1))
    t1_first = 1.25 * (t90_1 - t10_1)

    t_tail_1 = np.linspace(t_front_1[peak_idx_1], 600.0, 200_000)
    i_tail_1, _, _ = LEMPEngine.evaluate_heidler_current(
        t_tail_1, "first_positive_10_350", 100.0
    )
    t2_first = float(np.interp(0.5 * i_peak_1, i_tail_1[::-1], t_tail_1[::-1]))

    assert t1_first == pytest.approx(10.0, rel=0.01)
    assert t2_first == pytest.approx(370.757, rel=1e-3)

    # 2. Subsequent negative 0.25/100 us (I = 100 kA)
    t_front_2 = np.linspace(0.0, 2.0, 200_000)
    i_front_2, _, _ = LEMPEngine.evaluate_heidler_current(
        t_front_2, "subsequent_negative_025_100", 100.0
    )
    peak_idx_2 = int(np.argmax(i_front_2))
    i_peak_2 = float(i_front_2[peak_idx_2])
    t_rise_2 = t_front_2[: peak_idx_2 + 1]
    i_rise_2 = i_front_2[: peak_idx_2 + 1]
    t10_2 = float(np.interp(0.1 * i_peak_2, i_rise_2, t_rise_2))
    t90_2 = float(np.interp(0.9 * i_peak_2, i_rise_2, t_rise_2))
    t1_sub = 1.25 * (t90_2 - t10_2)

    t_tail_2 = np.linspace(t_front_2[peak_idx_2], 200.0, 200_000)
    i_tail_2, _, _ = LEMPEngine.evaluate_heidler_current(
        t_tail_2, "subsequent_negative_025_100", 100.0
    )
    t2_sub = float(np.interp(0.5 * i_peak_2, i_tail_2[::-1], t_tail_2[::-1]))

    assert t1_sub == pytest.approx(0.25, rel=0.01)
    assert t2_sub == pytest.approx(100.159, rel=1e-3)
