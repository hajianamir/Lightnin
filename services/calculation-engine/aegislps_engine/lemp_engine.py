import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel, Field

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
        Evaluates current i(t) in kA and derivative di/dt in kA/us.
        Parameters calibrated to IEC 62305-1 Table A.1.
        """
        if stroke_type == "subsequent_negative_025_100":
            # 0.25 / 100 us subsequent stroke
            tau1 = 0.254 # us
            tau2 = 143.0 # us
            eta = 0.993
            n = 10.0
        else:
            # 10 / 350 us first positive stroke
            tau1 = 10.0 # us
            tau2 = 350.0 # us
            eta = 0.93
            n = 10.0

        t = np.maximum(1e-6, t_us)
        t_ratio = (t / tau1) ** n
        current_shape = (i_peak_ka / eta) * (t_ratio / (1.0 + t_ratio)) * np.exp(-t / tau2)
        current_ka = np.where(t_us <= 0, 0.0, current_shape)

        # Numerical gradient di/dt (kA / us)
        dt = float(t_us[1] - t_us[0]) if len(t_us) > 1 else 1e-3
        di_dt = np.gradient(current_ka, dt)
        max_di_dt = float(np.max(np.abs(di_dt)))

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
