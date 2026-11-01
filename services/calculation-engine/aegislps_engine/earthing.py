import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

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
    - Dwight & Sunde analytical formulations for rods, rings, and foundation meshes
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
        IEC 62305-3 Figure 3 minimum length l1 as a function of soil resistivity and LPS Class.
        """
        if lps_class == "I":
            return float(min(20.0, max(5.0, 20.0 * (rho / 800.0)))) if rho >= 100.0 else 5.0
        elif lps_class == "II":
            return float(min(15.0, max(5.0, 15.0 * (rho / 800.0)))) if rho >= 100.0 else 5.0
        else:
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
            # Dwight's exact formulation for buried circular ring electrode:
            # R = (rho / (2 * pi^2 * D)) * [ ln(8 * D / r) + ln(4 * D / h) ]
            d_ring = 2.0 * r_ring
            term1 = np.log((8.0 * d_ring) / r_cond)
            term2 = np.log((4.0 * d_ring) / h_depth)
            r_dc = float((rho / (2.0 * (np.pi ** 2) * d_ring)) * (term1 + term2))
            trace = f"Type B Ring (R_ring={r_ring}m, depth={h_depth}m, Dwight formula): R_stat={r_dc:.2f} ohm"

        elif inp.electrode_type == "type_a_vertical":
            l_rod = max(0.5, inp.vertical_rod_length_m)
            n_rods = max(1, inp.vertical_rod_count)
            s_spacing = max(0.5, inp.vertical_rod_spacing_m)
            effective_len = float(n_rods * l_rod)

            # Dwight's single vertical rod resistance:
            # R_1 = (rho / (2 * pi * L)) * [ ln(4 * L / r) - 1 ]
            r_single = (rho / (2.0 * np.pi * l_rod)) * (np.log(4.0 * l_rod / r_cond) - 1.0)

            # Mutual coupling array efficiency factor eta (IEEE 80 / Tagg model)
            # eta ~ (1 + alpha * (L / s)) / N
            if n_rods > 1:
                coupling_factor = (l_rod / (2.0 * np.pi * s_spacing)) * np.log(1.0 + (s_spacing / l_rod))
                r_dc = float((r_single / n_rods) * (1.0 + (n_rods - 1) * coupling_factor))
            else:
                r_dc = float(r_single)
            trace = f"Type A Vertical ({n_rods} rods x {l_rod}m, spacing={s_spacing}m, Dwight + Mutual Coupling): R_stat={r_dc:.2f} ohm"

        elif inp.electrode_type == "type_a_horizontal":
            l_strip = max(1.0, inp.ring_radius_m * 2.0)
            effective_len = float(l_strip)
            # Sunde formula for horizontal strip electrode buried at depth h:
            # R = (rho / (pi * L)) * [ ln(2 * L / sqrt(2 * r * h)) - 1 ]
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

        return EarthingAssessmentResult(
            lps_class=inp.lps_class,
            effective_soil_resistivity_ohm_m=round(float(rho), 2),
            minimum_length_l1_m=round(float(l1), 2),
            actual_effective_length_m=round(float(effective_len), 2),
            stationary_resistance_r_ohm=round(float(r_dc), 2),
            impulse_impedance_z_ohm=round(float(z_impulse), 2),
            impulse_efficiency_factor=round(float(impulse_factor), 3),
            meets_iec_l1_requirement=meets_l1,
            meets_recommended_10_ohm=meets_10,
            status=status,
            method_details=trace,
            warnings=warnings
        )
