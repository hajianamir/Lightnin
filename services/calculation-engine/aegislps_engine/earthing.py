import numpy as np
from typing import Dict, List, Any
from pydantic import BaseModel, Field

class EarthingAssessmentInput(BaseModel):
    lps_class: str = "I"
    soil_resistivity_ohm_m: float = 100.0
    electrode_type: str = "type_b_ring" # type_a_vertical, type_a_horizontal, type_b_ring, foundation
    ring_radius_m: float = 15.0 # For Type B ring
    rod_length_m: float = 3.0 # For Type A vertical rod
    rod_count: int = 4
    burial_depth_m: float = 0.5

class EarthingAssessmentResult(BaseModel):
    lps_class: str
    minimum_length_l1_m: float
    actual_effective_length_m: float
    calculated_resistance_ohm: float
    meets_recommended_10_ohm: bool
    status: str
    formula_trace: str
    warnings: List[str] = Field(default_factory=list)

class EarthingEngine:
    """
    IEC 62305-3 Section 5.4 Earthing System Design Engine.
    Evaluates minimum electrode length l1 and estimated earthing resistance.
    """
    @staticmethod
    def get_min_length_l1(lps_class: str, rho: float) -> float:
        """
        Approximates minimum length l1 according to IEC 62305-3 Figure 3.
        Class I: l1 = 20m for rho >= 800 ohm.m, linear reduction below 800.
        Class II: l1 = 15m.
        Class III & IV: l1 = 5m.
        """
        if lps_class == "I":
            return min(20.0, max(5.0, 20.0 * (rho / 800.0)))
        elif lps_class == "II":
            return min(15.0, max(5.0, 15.0 * (rho / 800.0)))
        else:
            return 5.0

    def evaluate_earthing_system(self, inp: EarthingAssessmentInput) -> EarthingAssessmentResult:
        l1 = self.get_min_length_l1(inp.lps_class, inp.soil_resistivity_ohm_m)
        rho = inp.soil_resistivity_ohm_m
        warnings = []

        if inp.electrode_type == "type_b_ring":
            effective_len = 2.0 * np.pi * inp.ring_radius_m
            # R_ring approx = rho / (2 * pi^2 * r) * ln( (8 * r) / d )
            # Simplified engineering approximation for ring: R ~ rho / (2 * D) where D = 2*r
            equiv_diameter = 2.0 * inp.ring_radius_m
            r_earth = rho / (2.0 * equiv_diameter)
            trace = f"Type B Ring (r={inp.ring_radius_m}m): Effective Length = {effective_len:.1f}m (min l1={l1:.1f}m), R ~ rho / (2*D) = {r_earth:.2f} ohm"
        elif inp.electrode_type == "type_a_vertical":
            effective_len = inp.rod_length_m * inp.rod_count
            # Vertical rod: R = (rho / (2*pi*L)) * [ln(4L/r) - 1]
            l_rod = max(0.5, inp.rod_length_m)
            r_single = (rho / (2.0 * np.pi * l_rod)) * (np.log(4.0 * l_rod / 0.01) - 1.0)
            r_earth = r_single / max(1, inp.rod_count) # simplified parallel factor
            trace = f"Type A Vertical ({inp.rod_count} rods x {l_rod}m): Effective Length = {effective_len:.1f}m (min l1={l1:.1f}m), R = {r_earth:.2f} ohm"
        else: # foundation
            effective_len = 2.0 * (30.0 + 20.0) # Perimeter assumption
            r_earth = rho / (2.0 * np.sqrt(effective_len * 10.0))
            trace = f"Foundation Earth: Effective Length = {effective_len:.1f}m, R = {r_earth:.2f} ohm"

        if effective_len < l1:
            warnings.append(f"Electrode effective length ({effective_len:.1f}m) is below recommended minimum l1 ({l1:.1f}m)")

        meets_10 = r_earth <= 10.0
        if not meets_10:
            warnings.append(f"Calculated earthing resistance ({r_earth:.2f} ohm) exceeds conventional 10 ohm recommendation")

        return EarthingAssessmentResult(
            lps_class=inp.lps_class,
            minimum_length_l1_m=round(float(l1), 2),
            actual_effective_length_m=round(float(effective_len), 2),
            calculated_resistance_ohm=round(float(r_earth), 2),
            meets_recommended_10_ohm=meets_10,
            status="PASS" if (effective_len >= l1 and meets_10) else "WARNING",
            formula_trace=trace,
            warnings=warnings
        )
