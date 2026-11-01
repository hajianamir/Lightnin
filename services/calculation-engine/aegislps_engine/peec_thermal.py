import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel, Field

class ConductorThermalProperties(BaseModel):
    material: str = "copper" # copper, aluminum, steel, stainless_steel
    cross_section_mm2: float = 50.0
    initial_temperature_c: float = 20.0

class ConductorStressResult(BaseModel):
    material: str
    cross_section_mm2: float
    action_integral_w_over_r_mj_per_ohm: float
    adiabatic_temp_rise_delta_theta_k: float
    final_temperature_c: float
    max_permitted_temp_c: float
    thermal_stress_safe: bool
    peak_repulsive_force_n_per_m: float
    recommended_fastener_spacing_m: float
    status: str
    engineering_insights: List[str] = Field(default_factory=list)

class SkewSegment3D(BaseModel):
    start: Tuple[float, float, float]
    end: Tuple[float, float, float]

class PEECThermalEngine:
    """
    Advanced PEEC Mutual Inductance, Conductor Thermal Heating, and Electrodynamic Force Engine.

    Implements:
    - Neumann's double integral formulation for mutual inductance M_ij between 3D skew segments:
      M_ij = (mu_0 / 4pi) * oint oint (dl_i . dl_j) / r_ij
    - IEC 62305-1 Annex D adiabatic conductor heating:
      theta_f = theta_0 + (1 / alpha) * [ exp( (W/R) * (alpha * rho_0 / (q^2 * gamma * C_w)) ) - 1 ]
    - Peak electrodynamic Lorentz repulsion / attraction forces:
      F = (mu_0 / 2pi) * (i_1 * i_2) / d
    - Dynamic fastener pitch calculation preventing conductor mechanical detachment under short-circuit impulse forces.
    """
    MU_0 = 4.0 * np.pi * 1e-7

    # IEC 62305-1 Table D.1 material constants
    MATERIAL_CONSTANTS = {
        "copper": {
            "rho_0": 1.78e-8,      # Resistivity ohm.m at 20C
            "alpha": 3.92e-3,      # Temp coefficient 1/K
            "gamma": 8920.0,       # Density kg/m3
            "c_w": 385.0,          # Specific heat J/(kg.K)
            "max_temp": 300.0      # Max allowed temperature C
        },
        "aluminum": {
            "rho_0": 2.82e-8,
            "alpha": 4.03e-3,
            "gamma": 2700.0,
            "c_w": 900.0,
            "max_temp": 200.0
        },
        "steel": {
            "rho_0": 1.50e-7,
            "alpha": 4.50e-3,
            "gamma": 7800.0,
            "c_w": 460.0,
            "max_temp": 400.0
        },
        "stainless_steel": {
            "rho_0": 7.00e-7,
            "alpha": 1.00e-3,
            "gamma": 7900.0,
            "c_w": 500.0,
            "max_temp": 500.0
        }
    }

    @classmethod
    def calculate_mutual_inductance_neumann(
        cls,
        seg_i: SkewSegment3D,
        seg_j: SkewSegment3D,
        num_gauss_points: int = 10
    ) -> float:
        """
        Calculates mutual inductance M_ij (Henry) between two arbitrary 3D linear conductor segments
        using Gaussian quadrature discretization of Neumann's double integral.
        """
        p1 = np.array(seg_i.start, dtype=np.float64)
        p2 = np.array(seg_i.end, dtype=np.float64)
        q1 = np.array(seg_j.start, dtype=np.float64)
        q2 = np.array(seg_j.end, dtype=np.float64)

        vec_i = p2 - p1
        vec_j = q2 - q1
        len_i = np.linalg.norm(vec_i)
        len_j = np.linalg.norm(vec_j)

        if len_i < 1e-4 or len_j < 1e-4:
            return 0.0

        u_i = vec_i / len_i
        u_j = vec_j / len_j
        dot_product = float(np.dot(u_i, u_j))

        # Gauss-Legendre quadrature points in [0, 1]
        nodes, weights = np.polynomial.legendre.leggauss(num_gauss_points)
        s_vals = 0.5 * (nodes + 1.0)
        w_vals = 0.5 * weights

        integral = 0.0
        for s, ws in zip(s_vals, w_vals):
            pos_i = p1 + s * vec_i
            for t, wt in zip(s_vals, w_vals):
                pos_j = q1 + t * vec_j
                dist = max(1e-3, float(np.linalg.norm(pos_i - pos_j)))
                integral += (ws * wt) / dist

        m_ij = (cls.MU_0 / (4.0 * np.pi)) * dot_product * len_i * len_j * integral
        return float(m_ij)

    @classmethod
    def evaluate_thermal_and_electrodynamic_stress(
        cls,
        props: ConductorThermalProperties,
        lps_class: str = "I",
        parallel_conductor_spacing_m: float = 0.1 # 10 cm parallel cable distance
    ) -> ConductorStressResult:
        """
        Calculates adiabatic temperature rise and Lorentz peak magnetic forces under lightning impulse.
        """
        mat = cls.MATERIAL_CONSTANTS.get(props.material, cls.MATERIAL_CONSTANTS["copper"])

        # IEC 62305-1 Table 1 Specific Energy (W/R) per LPS Class
        # Class I: W/R = 10.0 MJ/ohm (10^7 A^2.s), I_peak = 200 kA
        # Class II: W/R = 5.6 MJ/ohm, I_peak = 150 kA
        # Class III/IV: W/R = 2.5 MJ/ohm, I_peak = 100 kA
        w_over_r_table = {
            "I": 10.0e6,
            "II": 5.6e6,
            "III": 2.5e6,
            "IV": 2.5e6
        }
        i_peak_table = {
            "I": 200e3,
            "II": 150e3,
            "III": 100e3,
            "IV": 100e3
        }

        w_over_r = w_over_r_table.get(lps_class, 10.0e6)
        i_peak = i_peak_table.get(lps_class, 200e3)
        q_m2 = props.cross_section_mm2 * 1e-6 # Conductor cross-section in m2

        # Adiabatic exponential formulation from IEC 62305-1 Equation D.1
        exponent = (w_over_r * mat["alpha"] * mat["rho_0"]) / ((q_m2 ** 2) * mat["gamma"] * mat["c_w"])
        delta_theta = float((1.0 / mat["alpha"]) * (np.exp(exponent) - 1.0))
        final_temp = float(props.initial_temperature_c + delta_theta)
        is_safe = final_temp <= mat["max_temp"]

        # Electrodynamic repulsion force F/L = (mu_0 / 2pi) * (i_1 * i_2 / d)
        # Assuming current divides into parallel paths i1 = i2 = i_peak / 2
        d_m = max(0.01, parallel_conductor_spacing_m)
        i_branch = i_peak / 2.0
        f_per_m = float((cls.MU_0 / (2.0 * np.pi)) * (i_branch ** 2) / d_m)

        # Fastener spacing pitch ensuring holder anchor holds under dynamic load (typically <= 500 N per clip)
        max_holder_force_n = 500.0
        fastener_pitch_m = float(min(1.0, max(0.2, max_holder_force_n / max(1.0, f_per_m))))

        status = "COMPLIANT_SAFE" if is_safe else "THERMAL_OVERHEATING_HAZARD"

        insights = [
            f"Action integral W/R: {w_over_r*1e-6:.2f} MJ/ohm for LPS Class {lps_class}.",
            f"Adiabatic heating: Delta_theta = +{delta_theta:.1f} K -> Final Temp = {final_temp:.1f} °C (Permitted limit: {mat['max_temp']:.0f} °C).",
            f"Peak electrodynamic repulsion force: {f_per_m:.1f} N/m at spacing {d_m*100:.1f} cm.",
            f"Recommended mechanical support clip spacing: <= {fastener_pitch_m:.2f} m to withstand electrodynamic surge forces."
        ]

        return ConductorStressResult(
            material=props.material,
            cross_section_mm2=props.cross_section_mm2,
            action_integral_w_over_r_mj_per_ohm=round(w_over_r * 1e-6, 2),
            adiabatic_temp_rise_delta_theta_k=round(delta_theta, 1),
            final_temperature_c=round(final_temp, 1),
            max_permitted_temp_c=mat["max_temp"],
            thermal_stress_safe=is_safe,
            peak_repulsive_force_n_per_m=round(f_per_m, 1),
            recommended_fastener_spacing_m=round(fastener_pitch_m, 2),
            status=status,
            engineering_insights=insights
        )
