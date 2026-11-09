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

K_MS_SOURCE: str = "UNVERIFIED"
_INTERNAL_PEAK_GRID_POINTS: int = 20_000
_MAX_EFFECTIVE_MESH_WIDTH_M: float = 5.0


def _resolve_shielding_factor(shield: "ShieldingGrid") -> Tuple[float, str, List[str]]:
    """Resolve K_MS, source flag, and mesh-width warnings without unverified credits."""
    warnings: List[str] = []
    if shield.is_shielded and shield.mesh_width_w_m > _MAX_EFFECTIVE_MESH_WIDTH_M:
        warnings.append(
            f"Spatial shield mesh width w = {shield.mesh_width_w_m:.2f} m exceeds "
            f"{_MAX_EFFECTIVE_MESH_WIDTH_M:.1f} m; spatial grid shields wider than "
            "~5 m provide little magnetic-field attenuation (IEC 62305-4 Annex A)."
        )

    if not shield.is_shielded:
        kms = 1.0
    elif shield.shielding_factor_override is not None:
        kms = float(shield.shielding_factor_override)
    else:
        # Conservative default (no shielding credit) when no primary IEC 62305-4
        # Annex A formula is available in-repo and no explicit override is supplied.
        kms = 1.0

    return kms, K_MS_SOURCE, warnings


class ShieldingGrid(BaseModel):
    is_shielded: bool = True
    mesh_width_w_m: float = 5.0 # Spatial grid shield width (e.g., 5m mesh)
    relative_permeability_mur: float = 1.0 # Retained for schema compatibility; no permeability credit applied
    shielding_factor_override: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        allow_inf_nan=False,
    )

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
    kms_source: str = K_MS_SOURCE
    peak_induced_voltage_kv: float
    equipment_withstand_uw_kv: float
    equipment_protected: bool
    status: str
    time_series_us: List[float]
    current_waveform_ka: List[float]
    induced_voltage_waveform_kv: List[float]
    warnings: List[str] = Field(default_factory=list)
    engineering_insights: List[str] = Field(default_factory=list)

    @property
    def K_MS_SOURCE(self) -> str:
        return self.kms_source

class LEMPEngine:
    """
    Lightning Electromagnetic Pulse (LEMP) Transient Induction Engine.

    Implements:
    - Analytical Heidler function modeling of lightning surge currents:
      i(t) = (I / eta) * ( (t / tau1)^10 / (1 + (t / tau1)^10) ) * exp(-t / tau2)
    - Biot-Savart quasi-magnetostatic transient field induction:
      H(r, t) = i(t) / (2 * pi * r)
    - Spatial grid shield magnetic field factor K_MS:
      Conservative default K_MS = 1.0 (no unverified credit; kms_source = "UNVERIFIED")
      unless an explicit ShieldingGrid.shielding_factor_override in [0, 1] is supplied;
      no unverified relative-permeability (mu_r) reduction is applied.
    - Uniform-field Faraday law approximation over internal cabling loops (valid for b << d):
      u_i(t) = - mu_0 * K_MS * (dH / dt) * A_loop
             = - (mu_0 / (2 * pi * r)) * K_MS * A_loop * (di / dt)
    - Continuous/fine-grid peak surge stress evaluation vs. equipment withstand (U_w).
    """
    MU_0 = 4.0 * np.pi * 1e-7 # H/m permeability of free space
    K_MS_SOURCE = K_MS_SOURCE

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
        - Under the IEC 62305-1 10%-90% current front-time definition
          T1 = 1.25 * (t90 - t10), the Table A.1 parameters give
          T1 = 9.980 us (-0.20% vs nominal 10 us) for 10/350 and
          T1 = 0.2493 us (-0.27% vs nominal 0.25 us) for 0.25/100;
          tail times to 0.5 * I_peak are T2 = 370.76 us (+5.93%) and
          T2 = 100.16 us (+0.16%).
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
        """
        Evaluate transient LEMP magnetic field and open-circuit induced loop voltage.

        Notes & validity limits:
        - K_MS handling (K_MS_SOURCE = "UNVERIFIED"): The primary IEC 62305-4 Annex A
          spatial-shielding formula is not present in-repo. When shield.is_shielded is
          False, K_MS = 1.0. When shield.is_shielded is True and no explicit
          shield.shielding_factor_override is given, conservative K_MS = 1.0 (no
          shielding credit) is applied; otherwise the user override in [0, 1] is used.
          No relative_permeability_mur reduction is applied. A warning is emitted when
          shield.is_shielded is True and mesh_width_w_m > 5.0 m.
        - Peak evaluation: Peak current/H-field, max |di/dt|, and peak_induced_voltage_kv
          are evaluated on a fixed fine internal grid (_INTERNAL_PEAK_GRID_POINTS = 20000
          over [0, t_end_us] with analytic di/dt and golden-section front refinement),
          independent of waveform.num_time_steps. Serialized waveform arrays retain the
          waveform.num_time_steps discretization.
        - Faraday loop approximation (valid only when radial loop height b << d):
          u_i(t) = -(mu_0 / (2 * pi * r)) * K_MS * A_loop * (di / dt) assumes a uniform
          magnetic field over A_loop = a * b, approximating the exact rectangular-loop
          mutual inductance M = (mu_0 * a / (2 * pi)) * ln((d + b) / d) (axial length a,
          radial span b from inner edge d to d + b). Using r = d overestimates M unless
          b << d (+4.9% at b/d = 0.1, +44.3% at b/d = 1, +116.4% at b/d = 3); using loop
          center distance r = d + b/2 underestimates M when b is comparable to or larger
          than d (-0.08% at b/d = 0.1, -3.82% at b/d = 1, -13.44% at b/d = 3).
        """
        n_steps = max(1, int(waveform.num_time_steps))
        t_end_us = max(0.0, float(waveform.t_end_us))

        t_us = np.linspace(0.0, t_end_us, n_steps)
        i_ka, di_dt_ka_us, _ = self.evaluate_heidler_current(
            t_us, waveform.stroke_type, waveform.peak_current_ka
        )

        # Fine internal grid independent of num_time_steps for continuous peak evaluation
        t_fine_us = np.linspace(0.0, t_end_us, _INTERNAL_PEAK_GRID_POINTS)
        i_fine_ka, di_dt_fine_ka_us, max_di_dt = self.evaluate_heidler_current(
            t_fine_us, waveform.stroke_type, waveform.peak_current_ka
        )

        r_m = max(0.5, loop.center_distance_from_down_conductor_m)
        a_loop = max(0.01, loop.loop_area_m2)

        # Peak unattenuated magnetic field at distance r (A/m) on fine internal grid
        # H(t) = i(t) / (2 * pi * r) where i(t) in Amperes
        h_unshielded_fine_a_m = (np.abs(i_fine_ka) * 1e3) / (2.0 * np.pi * r_m)
        peak_h_unshielded = float(np.max(h_unshielded_fine_a_m))

        kms, kms_source, warnings = _resolve_shielding_factor(shield)
        peak_h_shielded = float(peak_h_unshielded * kms)

        # Faraday induced electromotive force u_i(t) (uniform-field approximation, b << d)
        # di/dt is in kA/us = 10^3 A / 10^-6 s = 10^9 A/s
        loop_coupling_v_per_ka_us = (
            self.MU_0 * kms * (a_loop / (2.0 * np.pi * r_m)) * 1e9
        )
        u_induced_kv = np.abs(loop_coupling_v_per_ka_us * di_dt_ka_us) * 1e-3

        u_fine_peak_kv = float(
            np.max(np.abs(loop_coupling_v_per_ka_us * di_dt_fine_ka_us)) * 1e-3
        )
        u_refined_peak_kv = float(abs(loop_coupling_v_per_ka_us * max_di_dt) * 1e-3)
        peak_induced_kv = max(u_fine_peak_kv, u_refined_peak_kv)

        protected = peak_induced_kv <= loop.equipment_withstand_uw_kv
        status = "COMPLIANT_WITHIN_WITHSTAND" if protected else "EXCEEDS_WITHSTAND_HAZARD"

        if not shield.is_shielded:
            kms_detail = f"K_MS = {kms:.3f}, unshielded, source={kms_source}"
        elif shield.shielding_factor_override is not None:
            kms_detail = f"K_MS = {kms:.4g}, user override, source={kms_source}"
        else:
            kms_detail = (
                f"K_MS = {kms:.3f}, source={kms_source}; conservative no-shielding "
                "credit applied without verified primary formula or override"
            )

        insights = [
            f"Heidler surge waveform '{waveform.stroke_type}': Peak current {waveform.peak_current_ka:.1f} kA, max steepness di/dt = {max_di_dt:.2f} kA/us.",
            f"Magnetic field at {r_m:.1f}m: Unattenuated {peak_h_unshielded:.1f} A/m -> Shielded {peak_h_shielded:.1f} A/m ({kms_detail}).",
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
            grid_shielding_factor_kms=float(kms),
            kms_source=kms_source,
            peak_induced_voltage_kv=round(peak_induced_kv, 3),
            equipment_withstand_uw_kv=loop.equipment_withstand_uw_kv,
            equipment_protected=protected,
            status=status,
            time_series_us=[round(float(t), 2) for t in t_us[::sample_step]],
            current_waveform_ka=[round(float(i), 2) for i in i_ka[::sample_step]],
            induced_voltage_waveform_kv=[round(float(u), 3) for u in u_induced_kv[::sample_step]],
            warnings=warnings,
            engineering_insights=insights
        )
