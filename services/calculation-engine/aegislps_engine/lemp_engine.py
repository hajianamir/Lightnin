import math
import numpy as np
from typing import Callable, Dict, List, Tuple, Any, Optional
from pydantic import BaseModel, Field

# IEC 62305-1 Annex A, Table A.1 Heidler current parameters (n = 10),
# per secondary literature summaries (ETEP 2002; ELEK; Heidler & Zischank, ICLP 2008).
HEIDLER_IEC_62305_1: Dict[str, Dict[str, float]] = {
    "first_positive_10_350": {
        "tau1": 19.0,
        "tau2": 485.0,
        "eta": 0.93,
        "n": 10.0,
    },
    "subsequent_negative_025_100": {
        "tau1": 0.454,
        "tau2": 143.0,
        "eta": 0.993,
        "n": 10.0,
    },
}


def _heidler_scalar_di_dt(
    t_us: float, i_peak_ka: float, tau1: float, tau2: float, eta: float, n: float
) -> float:
    """Analytic scalar di/dt [kA/us] at time t_us [us] for bounded peak refinement."""
    if t_us <= 0.0:
        return 0.0
    t_val = max(float(t_us), 1e-12)
    x = t_val / tau1
    x_n_minus_1 = x ** (n - 1.0)
    x_n = x_n_minus_1 * x
    denom = 1.0 + x_n
    return (
        (i_peak_ka / eta)
        * math.exp(-t_val / tau2)
        * (
            (n * x_n_minus_1) / (tau1 * denom * denom)
            - (1.0 / tau2) * (x_n / denom)
        )
    )


def _golden_section_max_abs(
    func: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-13,
    max_iter: int = 80,
) -> float:
    """Maximize |func(t)| on [a, b] via deterministic golden-section search."""
    if b <= a:
        return abs(func(a))
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c = b - gr * (b - a)
    d = a + gr * (b - a)
    fc = abs(func(c))
    fd = abs(func(d))
    for _ in range(max_iter):
        if (b - a) <= tol * max(1.0, abs(a) + abs(b)):
            break
        if fc > fd:
            b = d
            d = c
            fd = fc
            c = b - gr * (b - a)
            fc = abs(func(c))
        else:
            a = c
            c = d
            fc = fd
            d = a + gr * (b - a)
            fd = abs(func(d))
    mid = 0.5 * (a + b)
    return float(max(abs(func(mid)), fc, fd, abs(func(a)), abs(func(b))))

class LEMPWaveformSpecification(BaseModel):
    stroke_type: str = "first_positive_10_350" # first_positive_10_350, subsequent_negative_025_100
    peak_current_ka: float = 100.0 # I_peak in kA
    t_end_us: float = 100.0 # Simulation horizon in microseconds
    num_time_steps: int = 500

class ShieldingGrid(BaseModel):
    is_shielded: bool = True
    mesh_width_w_m: float = 5.0 # Spatial grid shield width (e.g., 5m mesh)
    relative_permeability_mur: float = 1.0 # 1.0 for copper/alu, ~200 for structural steel rebar

class InternalCableLoop(BaseModel):
    id: str = "signal-loop-1"
    loop_area_m2: float = 2.0 # Area enclosed by signal cable and ground plane
    center_distance_from_down_conductor_m: float = 3.0 # Radial offset
    equipment_withstand_uw_kv: float = 1.5 # Category I / II equipment withstand

class LEMPTransientResult(BaseModel):
    stroke_type: str
    peak_current_ka: float
    max_di_dt_ka_per_us: float
    unattenuated_peak_h_field_a_per_m: float
    shielded_peak_h_field_a_per_m: float
    grid_shielding_factor_kms: float
    peak_induced_voltage_kv: float
    equipment_withstand_uw_kv: float
    equipment_protected: bool
    status: str
    time_series_us: List[float]
    current_waveform_ka: List[float]
    induced_voltage_waveform_kv: List[float]
    engineering_insights: List[str] = Field(default_factory=list)

class LEMPEngine:
    """
    Advanced IEC 62305-4 Annex A Lightning Electromagnetic Pulse (LEMP) Engine.
    
    Implements:
    - Analytical Heidler function modeling of lightning surge currents:
      i(t) = (I / eta) * ( (t / tau1)^10 / (1 + (t / tau1)^10) ) * exp(-t / tau2)
    - Biot-Savart quasi-magnetostatic transient field induction:
      H(r, t) = i(t) / (2 * pi * r)
    - IEC 62305-4 spatial grid shield magnetic field attenuation:
      K_MS = 0.01 * w_m  (for spatial mesh shields)
    - Faraday-Maxwell law of induction over internal cabling loops:
      u_i(t) = - mu_0 * K_MS * (dH / dt) * A_loop
             = - (mu_0 / (2 * pi * r)) * K_MS * A_loop * (di / dt)
    - Time-domain waveform synthesis and peak surge stress analysis vs. equipment withstand (U_w).
    """
    MU_0 = 4.0 * np.pi * 1e-7 # H/m permeability of free space

    @classmethod
    def evaluate_heidler_current(
        cls,
        t_us: np.ndarray,
        stroke_type: str,
        i_peak_ka: float
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Evaluates current i(t) in kA and analytic derivative di/dt in kA/us
        using IEC 62305-1 Table A.1 Heidler parameters (HEIDLER_IEC_62305_1).

        Notes & limitations:
        - Returns positive current magnitude for all strokes (including
          "subsequent_negative_025_100"); no negative sign convention is applied.
        - Unrecognized stroke_type values fall back to "first_positive_10_350".
        - Under the 30%-90% front-time definition T1 = 1.25 * (t90 - t30),
          the IEC Table A.1 parameters give T1 = 7.250 us (-27.50% vs 10 us)
          for 10/350 and T1 = 0.1836 us (-26.57% vs 0.25 us) for 0.25/100
          (> 10% difference from nominal because IEC 62305-1 current front time
          is calibrated to the 10%-90% chord (t90 - t10) / 0.8); tail times to
          0.5 * I_peak are T2 = 370.76 us (+5.93%) and T2 = 100.16 us (+0.16%).
        """
        if stroke_type == "subsequent_negative_025_100":
            params = HEIDLER_IEC_62305_1["subsequent_negative_025_100"]
        else:
            params = HEIDLER_IEC_62305_1["first_positive_10_350"]

        tau1 = params["tau1"]
        tau2 = params["tau2"]
        eta = params["eta"]
        n = params["n"]

        t_arr = np.asarray(t_us, dtype=float)
        t_pos = np.maximum(t_arr, 1e-12)
        x = t_pos / tau1
        x_n_minus_1 = x ** (n - 1.0)
        x_n = x_n_minus_1 * x
        denom = 1.0 + x_n
        exp_decay = np.exp(-t_pos / tau2)
        scale = float(i_peak_ka) / eta

        current_shape = scale * (x_n / denom) * exp_decay
        di_dt_shape = scale * exp_decay * (
            (n * x_n_minus_1) / (tau1 * denom * denom)
            - (1.0 / tau2) * (x_n / denom)
        )

        current_ka = np.where(t_arr <= 0.0, 0.0, current_shape)
        di_dt = np.where(t_arr <= 0.0, 0.0, di_dt_shape)

        if t_arr.size == 0:
            return current_ka, di_dt, 0.0

        max_di_dt = float(np.max(np.abs(di_dt)))
        if t_arr.size > 1:
            idx = int(np.argmax(np.abs(di_dt)))
            left_idx = max(0, idx - 1)
            right_idx = min(int(t_arr.size) - 1, idx + 1)
            a_br = float(min(t_arr[left_idx], t_arr[right_idx]))
            b_br = float(max(t_arr[left_idx], t_arr[right_idx]))

            scalar_fn = lambda t_val: _heidler_scalar_di_dt(
                t_val, float(i_peak_ka), tau1, tau2, eta, n
            )
            if b_br > a_br:
                max_di_dt = max(max_di_dt, _golden_section_max_abs(scalar_fn, a_br, b_br))

            t_min = float(np.min(t_arr))
            t_max = float(np.max(t_arr))
            front_lo = max(0.0, t_min)
            front_hi = min(t_max, 2.0 * tau1)
            if front_hi > front_lo:
                max_di_dt = max(
                    max_di_dt, _golden_section_max_abs(scalar_fn, front_lo, front_hi)
                )

        return current_ka, di_dt, max_di_dt

    def calculate_lemp_induction(
        self,
        waveform: LEMPWaveformSpecification,
        shield: ShieldingGrid,
        loop: InternalCableLoop
    ) -> LEMPTransientResult:
        t_us = np.linspace(0.0, waveform.t_end_us, waveform.num_time_steps)
        i_ka, di_dt_ka_us, max_di_dt = self.evaluate_heidler_current(
            t_us, waveform.stroke_type, waveform.peak_current_ka
        )

        r_m = max(0.5, loop.center_distance_from_down_conductor_m)
        a_loop = max(0.01, loop.loop_area_m2)

        # Peak unattenuated magnetic field at distance r (A/m)
        # H(t) = i(t) / (2 * pi * r) where i(t) in Amperes
        h_unshielded_a_m = (i_ka * 1e3) / (2.0 * np.pi * r_m)
        peak_h_unshielded = float(np.max(h_unshielded_a_m))

        # Spatial grid shielding attenuation factor K_MS (IEC 62305-4 Annex A)
        # For grid shield width w (m), K_MS ~ 0.01 * w. If unshielded, K_MS = 1.0
        if shield.is_shielded:
            kms = float(min(1.0, max(0.005, 0.01 * shield.mesh_width_w_m)))
            # If magnetic material (rebar with mu_r), additional absorption attenuation
            if shield.relative_permeability_mur > 1.0:
                kms *= float(1.0 / np.sqrt(shield.relative_permeability_mur))
        else:
            kms = 1.0

        peak_h_shielded = float(peak_h_unshielded * kms)

        # Faraday induced electromotive force u_i(t)
        # u_i(t) = - mu_0 * K_MS * (dH / dt) * A_loop
        # di/dt is in kA/us = 10^3 A / 10^-6 s = 10^9 A/s
        # u_i(t) in Volts = mu_0 * K_MS * (A_loop / (2 * pi * r)) * (di_dt * 10^9)
        u_induced_v = self.MU_0 * kms * (a_loop / (2.0 * np.pi * r_m)) * (di_dt_ka_us * 1e9)
        u_induced_kv = np.abs(u_induced_v) * 1e-3
        peak_induced_kv = float(np.max(u_induced_kv))

        protected = peak_induced_kv <= loop.equipment_withstand_uw_kv
        status = "COMPLIANT_WITHIN_WITHSTAND" if protected else "EXCEEDS_WITHSTAND_HAZARD"

        insights = [
            f"Heidler surge waveform '{waveform.stroke_type}': Peak current {waveform.peak_current_ka:.1f} kA, max steepness di/dt = {max_di_dt:.2f} kA/us.",
            f"Magnetic field at {r_m:.1f}m: Unattenuated {peak_h_unshielded:.1f} A/m -> Shielded {peak_h_shielded:.1f} A/m (K_MS = {kms:.3f}).",
            f"Induced loop voltage: Peak {peak_induced_kv:.2f} kV vs Equipment withstand Uw = {loop.equipment_withstand_uw_kv:.2f} kV.",
            "Mitigation recommendation: Reduce loop area or add Type 3 fine surge protection." if not protected else "Equipment protected by existing shielding and spatial separation."
        ]

        # Downsample time series for lightweight API/UI serialization
        sample_step = max(1, len(t_us) // 50)
        return LEMPTransientResult(
            stroke_type=waveform.stroke_type,
            peak_current_ka=waveform.peak_current_ka,
            max_di_dt_ka_per_us=round(max_di_dt, 3),
            unattenuated_peak_h_field_a_per_m=round(peak_h_unshielded, 1),
            shielded_peak_h_field_a_per_m=round(peak_h_shielded, 1),
            grid_shielding_factor_kms=round(kms, 4),
            peak_induced_voltage_kv=round(peak_induced_kv, 3),
            equipment_withstand_uw_kv=loop.equipment_withstand_uw_kv,
            equipment_protected=protected,
            status=status,
            time_series_us=[round(float(t), 2) for t in t_us[::sample_step]],
            current_waveform_ka=[round(float(i), 2) for i in i_ka[::sample_step]],
            induced_voltage_waveform_kv=[round(float(u), 3) for u in u_induced_kv[::sample_step]],
            engineering_insights=insights
        )
