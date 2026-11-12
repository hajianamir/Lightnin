import math
import numpy as np
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")
_VALID_THERMAL_MATERIALS = (
    "copper",
    "aluminum",
    "aluminium",
    "steel",
    "stainless_steel",
)

_ALUMINIUM_CONSTANTS: Dict[str, float] = {
    "rho_0": 2.82e-8,
    "alpha": 4.03e-3,
    "gamma": 2700.0,
    "c_w": 900.0,
    "max_temp": 200.0,
}


def _check_finite_float(name: str, v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float, np.number)):
        raise ValueError(f"{name} must be a finite number, not bool; got {v!r}.")
    val = float(v)
    if not math.isfinite(val):
        raise ValueError(f"{name} must be finite, got {v!r}.")
    return val


def _check_positive_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val <= 0.0:
        raise ValueError(f"{name} must be > 0, got {v!r}.")
    return val


def _validate_point3(name: str, v: Any) -> Tuple[float, float, float]:
    if isinstance(v, (str, bytes)) or not isinstance(v, (list, tuple, np.ndarray)):
        raise ValueError(f"{name} must be a 3-element (x, y, z) sequence, got {v!r}.")
    if len(v) != 3:
        raise ValueError(f"{name} must have length 3, got {len(v)}.")
    return (
        _check_finite_float(f"{name}[0]", v[0]),
        _check_finite_float(f"{name}[1]", v[1]),
        _check_finite_float(f"{name}[2]", v[2]),
    )


class ConductorThermalProperties(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    material: str  # copper, aluminum, aluminium, steel, stainless_steel
    cross_section_mm2: float
    # Default 20.0 °C retained per IEC 62305-1:2024 Annex D, Clause D.4.1.2,
    # Equation (D.7) & Table D.2 (pp. 54–55, docs/62305-1-2024.md):
    # "ρ_0 is the specific ohmic resistance of the conductor at ambient temperature (Ωm)"
    # (conventional 20 °C reference ambient temperature for the tabulated resistivities).
    initial_temperature_c: float = 20.0

    @field_validator("material", mode="before")
    @classmethod
    def _validate_material(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_THERMAL_MATERIALS:
            raise ValueError(
                f"Unknown conductor material {v!r}; expected one of {_VALID_THERMAL_MATERIALS}."
            )
        return v

    @field_validator("cross_section_mm2", mode="before")
    @classmethod
    def _validate_cross_section(cls, v: Any) -> float:
        return _check_positive_finite_float("cross_section_mm2", v)

    @field_validator("initial_temperature_c", mode="before")
    @classmethod
    def _validate_initial_temp(cls, v: Any) -> float:
        val = _check_finite_float("initial_temperature_c", v)
        if val <= -273.15:
            raise ValueError(
                f"initial_temperature_c must be > -273.15 °C, got {v!r}."
            )
        return val


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
    model_config = ConfigDict(allow_inf_nan=False)

    start: Tuple[float, float, float]
    end: Tuple[float, float, float]

    @field_validator("start", "end", mode="before")
    @classmethod
    def _validate_endpoints(cls, v: Any, info) -> Tuple[float, float, float]:
        return _validate_point3(info.field_name, v)


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

    # Material constants ("aluminum" and "aluminium" mapped explicitly to identical constants)
    MATERIAL_CONSTANTS: Dict[str, Dict[str, float]] = {
        "copper": {
            "rho_0": 1.78e-8,  # Resistivity ohm.m at 20C
            "alpha": 3.92e-3,  # Temp coefficient 1/K
            "gamma": 8920.0,  # Density kg/m3
            "c_w": 385.0,  # Specific heat J/(kg.K)
            "max_temp": 300.0,  # Max allowed temperature C
        },
        "aluminum": _ALUMINIUM_CONSTANTS,
        "aluminium": _ALUMINIUM_CONSTANTS,
        "steel": {
            "rho_0": 1.50e-7,
            "alpha": 4.50e-3,
            "gamma": 7800.0,
            "c_w": 460.0,
            "max_temp": 400.0,
        },
        "stainless_steel": {
            "rho_0": 7.00e-7,
            "alpha": 1.00e-3,
            "gamma": 7900.0,
            "c_w": 500.0,
            "max_temp": 500.0,
        },
    }

    W_OVER_R_TABLE: Dict[str, float] = {
        "I": 10.0e6,
        "II": 5.6e6,
        "III": 2.5e6,
        "IV": 2.5e6,
    }
    I_PEAK_TABLE: Dict[str, float] = {
        "I": 200e3,
        "II": 150e3,
        "III": 100e3,
        "IV": 100e3,
    }

    @classmethod
    def calculate_mutual_inductance_neumann(
        cls,
        seg_i: SkewSegment3D,
        seg_j: SkewSegment3D,
        num_gauss_points: int = 10,
    ) -> float:
        """
        Calculates mutual inductance M_ij (Henry) between two arbitrary 3D linear conductor segments
        using Gaussian quadrature discretization of Neumann's double integral.
        """
        if isinstance(num_gauss_points, bool) or not isinstance(
            num_gauss_points, (int, np.integer)
        ):
            raise ValueError(
                f"num_gauss_points must be a strict int >= 1, not bool; got {num_gauss_points!r}."
            )
        n_gauss = int(num_gauss_points)
        if n_gauss < 1:
            raise ValueError(f"num_gauss_points must be >= 1, got {num_gauss_points!r}.")

        p1 = np.array(_validate_point3("seg_i.start", seg_i.start), dtype=np.float64)
        p2 = np.array(_validate_point3("seg_i.end", seg_i.end), dtype=np.float64)
        q1 = np.array(_validate_point3("seg_j.start", seg_j.start), dtype=np.float64)
        q2 = np.array(_validate_point3("seg_j.end", seg_j.end), dtype=np.float64)

        vec_i = p2 - p1
        vec_j = q2 - q1
        len_i = float(np.linalg.norm(vec_i))
        len_j = float(np.linalg.norm(vec_j))

        if not math.isfinite(len_i) or not math.isfinite(len_j) or len_i <= 0.0 or len_j <= 0.0:
            raise ValueError(
                "Zero-length conductor segment is invalid for Neumann mutual inductance."
            )

        u_i = vec_i / len_i
        u_j = vec_j / len_j
        dot_product = float(np.dot(u_i, u_j))

        # Gauss-Legendre quadrature points in [0, 1]
        nodes, weights = np.polynomial.legendre.leggauss(n_gauss)
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
        lps_class: str,
        parallel_conductor_spacing_m: float,
    ) -> ConductorStressResult:
        """
        Calculates adiabatic temperature rise and Lorentz peak magnetic forces under lightning impulse.
        """
        if not isinstance(props.material, str) or props.material not in cls.MATERIAL_CONSTANTS:
            raise ValueError(
                f"Unknown conductor material {props.material!r}; expected one of {_VALID_THERMAL_MATERIALS}."
            )
        area_mm2 = _check_positive_finite_float(
            "cross_section_mm2", props.cross_section_mm2
        )
        init_temp_c = _check_finite_float(
            "initial_temperature_c", props.initial_temperature_c
        )
        if init_temp_c <= -273.15:
            raise ValueError(
                f"initial_temperature_c must be > -273.15 °C, got {props.initial_temperature_c!r}."
            )
        if not isinstance(lps_class, str) or lps_class not in cls.W_OVER_R_TABLE:
            raise ValueError(
                f"Unknown LPS class {lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        d_m = _check_positive_finite_float(
            "parallel_conductor_spacing_m", parallel_conductor_spacing_m
        )

        mat = cls.MATERIAL_CONSTANTS[props.material]
        w_over_r = cls.W_OVER_R_TABLE[lps_class]
        i_peak = cls.I_PEAK_TABLE[lps_class]
        q_m2 = area_mm2 * 1e-6  # Conductor cross-section in m2

        # Adiabatic exponential formulation from IEC 62305-1 Annex D Eq. (D.7)
        exponent = (w_over_r * mat["alpha"] * mat["rho_0"]) / (
            (q_m2**2) * mat["gamma"] * mat["c_w"]
        )
        delta_theta = float((1.0 / mat["alpha"]) * (np.exp(exponent) - 1.0))
        final_temp = float(init_temp_c + delta_theta)
        is_safe = final_temp <= mat["max_temp"]

        # Electrodynamic repulsion force F/L = (mu_0 / 2pi) * (i_1 * i_2 / d)
        # Assuming current divides into parallel paths i1 = i2 = i_peak / 2
        i_branch = i_peak / 2.0
        f_per_m = float((cls.MU_0 / (2.0 * np.pi)) * (i_branch**2) / d_m)

        # Fastener spacing pitch ensuring holder anchor holds under dynamic load (typically <= 500 N per clip)
        max_holder_force_n = 500.0
        fastener_pitch_m = float(
            min(1.0, max(0.2, max_holder_force_n / max(1.0, f_per_m)))
        )

        status = "COMPLIANT_SAFE" if is_safe else "THERMAL_OVERHEATING_HAZARD"

        insights = [
            f"Action integral W/R: {w_over_r*1e-6:.2f} MJ/ohm for LPS Class {lps_class}.",
            f"Adiabatic heating: Delta_theta = +{delta_theta:.1f} K -> Final Temp = {final_temp:.1f} °C (Permitted limit: {mat['max_temp']:.0f} °C).",
            f"Peak electrodynamic repulsion force: {f_per_m:.1f} N/m at spacing {d_m*100:.1f} cm.",
            f"Recommended mechanical support clip spacing: <= {fastener_pitch_m:.2f} m to withstand electrodynamic surge forces.",
        ]

        return ConductorStressResult(
            material=props.material,
            cross_section_mm2=area_mm2,
            action_integral_w_over_r_mj_per_ohm=round(w_over_r * 1e-6, 2),
            adiabatic_temp_rise_delta_theta_k=round(delta_theta, 1),
            final_temperature_c=round(final_temp, 1),
            max_permitted_temp_c=mat["max_temp"],
            thermal_stress_safe=is_safe,
            peak_repulsive_force_n_per_m=round(f_per_m, 1),
            recommended_fastener_spacing_m=round(fastener_pitch_m, 2),
            status=status,
            engineering_insights=insights,
        )
