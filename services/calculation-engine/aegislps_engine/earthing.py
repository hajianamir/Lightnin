import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

RING_METHOD_LABEL = (
    "Sunde equivalent-radius form (approximate; primary-source confirmation pending)"
)

STRIP_MODEL_BOUNDARY_NOTE = (
    "round-conductor equivalent (k = 2 - ln 2); flat-strip model not implemented"
)

MULTI_ROD_METHOD_LABEL = (
    "Dwight self-resistance + pairwise mutual "
    "(uniform-leakage, equal-current; primary-source confirmation pending)"
)


def single_vertical_rod_resistance(rho: float, L: float, a: float) -> float:
    """Single vertical rod resistance R1 = (rho / (2*pi*L)) * [ln(4*L/a) - 1]."""
    if (
        isinstance(rho, bool)
        or isinstance(L, bool)
        or isinstance(a, bool)
        or not (np.isfinite(rho) and np.isfinite(L) and np.isfinite(a))
        or rho <= 0.0
        or L <= 0.0
        or a <= 0.0
    ):
        raise ValueError(
            f"rho, L, and a must be finite and > 0, got rho={rho!r}, L={L!r}, a={a!r}."
        )
    return float((rho / (2.0 * np.pi * L)) * (np.log((4.0 * L) / a) - 1.0))


def mutual_resistance_rods(rho: float, L: float, s: float) -> float:
    """
    Pairwise mutual resistance between two identical vertical rods of length L at spacing s
    under uniform current leakage:
        R_m(s) = (rho / (pi * L^2)) * [L * asinh(L / s) - sqrt(L^2 + s^2) + s]
    """
    if (
        isinstance(rho, bool)
        or isinstance(L, bool)
        or isinstance(s, bool)
        or not (np.isfinite(rho) and np.isfinite(L) and np.isfinite(s))
        or rho <= 0.0
        or L <= 0.0
        or s <= 0.0
    ):
        raise ValueError(
            f"rho, L, and s must be finite and > 0, got rho={rho!r}, L={L!r}, s={s!r}."
        )
    rho_f = float(rho)
    l_f = float(L)
    s_f = float(s)
    return float(
        (rho_f / (np.pi * l_f * l_f))
        * (l_f * np.arcsinh(l_f / s_f) - np.sqrt(l_f * l_f + s_f * s_f) + s_f)
    )


def array_resistance_identical_rods(
    rho: float, L: float, a: float, n: int, s: float
) -> float:
    """
    Linear array resistance of n identical vertical rods of length L and radius a at equal
    spacing s under the equal-current approximation:
        R_n = (1 / n^2) * [n * R_1 + 2 * sum_{k=1}^{n-1} (n - k) * R_m(k * s)]
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n!r}.")
    r1 = single_vertical_rod_resistance(rho, L, a)
    if n == 1:
        if isinstance(s, bool) or not np.isfinite(s) or s <= 0.0:
            raise ValueError(f"s must be finite and > 0, got {s!r}.")
        return r1
    pair_sum = sum(
        (n - k) * mutual_resistance_rods(rho, L, k * float(s))
        for k in range(1, n)
    )
    return float((n * r1 + 2.0 * pair_sum) / float(n * n))

class SoilLayerModel(BaseModel):
    is_two_layer: bool = False
    rho_upper_ohm_m: float = 100.0
    h_upper_m: float = 1.5
    rho_lower_ohm_m: float = 300.0

class EarthingAssessmentInput(BaseModel):
    lps_class: str = "I"
    soil: SoilLayerModel = Field(default_factory=SoilLayerModel)
    electrode_type: str = "type_b_ring" # type_a_vertical, type_a_horizontal, type_b_ring, foundation
    ring_radius_m: float = 15.0
    strip_length_m: Optional[float] = None
    conductor_diameter_m: float = 0.01 # 10mm round conductor
    burial_depth_m: float = 0.5
    vertical_rod_length_m: float = 3.0
    vertical_rod_count: int = 4
    vertical_rod_spacing_m: float = 5.0
    foundation_perimeter_m: float = 80.0
    foundation_area_m2: float = 400.0
    peak_impulse_current_ka: float = 100.0 # 10/350 us impulse for ionization check

class EarthingAssessmentResult(BaseModel):
    lps_class: str
    effective_soil_resistivity_ohm_m: float
    minimum_length_l1_m: float
    actual_effective_length_m: float
    stationary_resistance_r_ohm: float
    impulse_impedance_z_ohm: float
    impulse_efficiency_factor: float
    meets_iec_l1_requirement: bool
    meets_recommended_10_ohm: bool
    status: str
    method_details: str
    warnings: List[str] = Field(default_factory=list)

class EarthingEngine:
    """
    Advanced IEC 62305-3 Section 5.4 & IEEE 80 Earthing Analysis Engine.
    
    Includes:
    - Dwight vertical-rod formulation, Sunde horizontal-strip formulation,
      buried ring via Sunde equivalent-radius form (approximate; primary-source confirmation pending),
      and Laurent & Nieman foundation mesh
    - Mutual coupling and array shielding efficiency factors for multiple vertical rods
    - Two-layer soil apparent resistivity modeling via Sunde reflection coefficient
    - Non-linear soil ionization impulse impedance reduction (Z_p) under high lightning currents
    """
    @staticmethod
    def calculate_apparent_resistivity(soil: SoilLayerModel, electrode_depth_m: float) -> float:
        """
        Calculates apparent soil resistivity for two-layer stratification using reflection coefficient k.
        """
        if not soil.is_two_layer:
            return float(soil.rho_upper_ohm_m)

        rho1 = max(1.0, soil.rho_upper_ohm_m)
        rho2 = max(1.0, soil.rho_lower_ohm_m)
        h = max(0.1, soil.h_upper_m)
        
        # Reflection factor k = (rho2 - rho1) / (rho2 + rho1)
        k = (rho2 - rho1) / (rho2 + rho1)
        
        # Sunde integration approximation for shallow electrodes
        ratio = electrode_depth_m / h
        apparent_rho = rho1 * (1.0 + k * (1.0 - np.exp(-1.8 * ratio)))
        return float(apparent_rho)

    @staticmethod
    def get_iec_min_length_l1(lps_class: str, rho: float) -> float:
        """
        IEC 62305-3:2024 Clause 5.4.2.2, Figure 5 (p. 34) minimum length l1 (m)
        as a function of soil resistivity rho (ohm.m) and LPS Class.
        Graphical reading of Figure 5; tolerance ±0.5 m.
        - Figure 5 NOTE 1: Classes III and IV are independent of soil resistivity (5.0 m).
        - Figure 5 NOTE 4: Figure 5 is defined for 0 < rho <= 3000 ohm.m (no extrapolation).
        """
        if not isinstance(lps_class, str) or lps_class not in ("I", "II", "III", "IV"):
            raise ValueError(
                f"Unknown LPS class {lps_class!r}; expected one of ('I', 'II', 'III', 'IV')."
            )
        if isinstance(rho, bool) or not isinstance(rho, (int, float, np.number)):
            raise ValueError(f"Soil resistivity rho must be a finite positive number, got {rho!r}.")
        rho_f = float(rho)
        if not np.isfinite(rho_f) or rho_f <= 0.0:
            raise ValueError(f"Soil resistivity rho must be finite and > 0 ohm.m, got {rho!r}.")
        if rho_f > 3000.0:
            raise ValueError(
                f"Soil resistivity rho={rho_f} ohm.m exceeds IEC 62305-3:2024 Figure 5 domain "
                f"(rho <= 3000 ohm.m; see 5.4.2.2 NOTE 4)."
            )
        if lps_class == "I":
            return 5.0 if rho_f <= 500.0 else float(0.03 * rho_f - 10.0)
        if lps_class == "II":
            return 5.0 if rho_f <= 800.0 else float(5.0 + (rho_f - 800.0) * (43.5 / 2200.0))
        return 5.0

    def evaluate_earthing_system(self, inp: EarthingAssessmentInput) -> EarthingAssessmentResult:
        rho = self.calculate_apparent_resistivity(inp.soil, inp.burial_depth_m)
        l1 = self.get_iec_min_length_l1(inp.lps_class, rho)
        warnings = []
        r_dc = 10.0
        effective_len = 0.0
        trace = ""

        r_cond = max(1e-4, inp.conductor_diameter_m / 2.0)
        h_depth = max(0.1, inp.burial_depth_m)

        if inp.electrode_type == "type_b_ring":
            r_ring = max(1.0, inp.ring_radius_m)
            effective_len = float(2.0 * np.pi * r_ring)
            # Sunde equivalent-radius form (approximate; primary-source confirmation pending):
            # R_ring = (rho / (pi^2 * D)) * ln(4 * D / sqrt(2 * a * h))
            d_ring = 2.0 * r_ring
            equiv_radius = np.sqrt(2.0 * r_cond * h_depth)
            r_dc = float((rho / ((np.pi ** 2) * d_ring)) * np.log((4.0 * d_ring) / equiv_radius))
            trace = f"Type B Ring (R_ring={r_ring}m, depth={h_depth}m, {RING_METHOD_LABEL}): R_stat={r_dc:.4f} ohm"
            warnings.append(RING_METHOD_LABEL)

        elif inp.electrode_type == "type_a_vertical":
            l_rod = max(0.5, inp.vertical_rod_length_m)
            n_rods = max(1, int(inp.vertical_rod_count))
            s_spacing = max(0.5, inp.vertical_rod_spacing_m)
            effective_len = float(n_rods * l_rod)

            r_dc = array_resistance_identical_rods(rho, l_rod, r_cond, n_rods, s_spacing)
            method_label = (
                MULTI_ROD_METHOD_LABEL if n_rods > 1 else "Dwight + Mutual Coupling"
            )
            trace = f"Type A Vertical ({n_rods} rods x {l_rod}m, spacing={s_spacing}m, {method_label}): R_stat={r_dc:.2f} ohm"

        elif inp.electrode_type == "type_a_horizontal":
            if (
                inp.strip_length_m is None
                or isinstance(inp.strip_length_m, bool)
                or not np.isfinite(inp.strip_length_m)
                or inp.strip_length_m <= 0.0
            ):
                raise ValueError(
                    f"strip_length_m must be provided and > 0 for electrode_type='type_a_horizontal', got {inp.strip_length_m!r}."
                )
            l_strip = float(inp.strip_length_m)
            effective_len = float(l_strip)
            # Sunde form. Exactly equivalent to the round-conductor form
            #   R = rho/(2*pi*L) * [ln(2L^2/(d*h)) - (2 - ln 2)],  d = conductor_diameter_m.
            # Flat-strip (width-based, k = 1) model is NOT implemented.
            equiv_radius = np.sqrt(2.0 * r_cond * h_depth)
            r_dc = float((rho / (np.pi * l_strip)) * (np.log(2.0 * l_strip / equiv_radius) - 1.0))
            trace = f"Type A Horizontal Strip (L={l_strip}m, depth={h_depth}m, Sunde formula): R_stat={r_dc:.2f} ohm"

        else: # Foundation Earth Electrode
            perim = max(10.0, inp.foundation_perimeter_m)
            area = max(10.0, inp.foundation_area_m2)
            effective_len = float(perim)
            # Laurent & Nieman formulation for foundation mesh:
            # R = rho / (4 * r_equiv) + rho / perim where r_equiv = sqrt(Area / pi)
            r_equiv = np.sqrt(area / np.pi)
            r_dc = float((rho / (4.0 * r_equiv)) + (rho / perim))
            trace = f"Foundation Mesh (Perim={perim}m, Area={area}m2, Laurent formula): R_stat={r_dc:.2f} ohm"

        # High-Current Impulse Impedance Reduction (Soil Ionization under Lightning Impulse)
        # Corson / Bellaschi soil ionization model: Z_p = R_dc / sqrt(1 + I / I_g)
        # Critical ionization current I_g = (E_c * rho) / (2 * pi * R_dc^2) where E_c ~ 300-400 kV/m
        e_critical = 300e3 # V/m dielectric breakdown of soil
        i_peak = max(1e3, inp.peak_impulse_current_ka * 1e3)
        i_critical = max(100.0, (e_critical * rho) / (2.0 * np.pi * max(0.1, r_dc ** 2)))
        
        # Impulse coefficient A_i = Z_p / R_dc
        impulse_factor = float(1.0 / np.sqrt(1.0 + (i_peak / i_critical)))
        z_impulse = float(r_dc * impulse_factor)

        meets_l1 = effective_len >= l1
        meets_10 = r_dc <= 10.0

        if not meets_l1:
            warnings.append(f"Electrode effective length ({effective_len:.1f}m) is below mandatory IEC 62305-3 l1 requirement ({l1:.1f}m)")
        if not meets_10:
            warnings.append(f"Stationary resistance ({r_dc:.2f} ohm) exceeds standard 10 ohm recommendation")

        status = "PASS" if (meets_l1 and meets_10) else ("WARNING" if meets_l1 else "NON_COMPLIANT")
        r_stat_out = (
            float(r_dc)
            if inp.electrode_type in ("type_b_ring", "type_a_horizontal")
            else round(float(r_dc), 2)
        )

        return EarthingAssessmentResult(
            lps_class=inp.lps_class,
            effective_soil_resistivity_ohm_m=round(float(rho), 2),
            minimum_length_l1_m=round(float(l1), 2),
            actual_effective_length_m=round(float(effective_len), 2),
            stationary_resistance_r_ohm=r_stat_out,
            impulse_impedance_z_ohm=round(float(z_impulse), 2),
            impulse_efficiency_factor=round(float(impulse_factor), 3),
            meets_iec_l1_requirement=meets_l1,
            meets_recommended_10_ohm=meets_10,
            status=status,
            method_details=trace,
            warnings=warnings
        )
