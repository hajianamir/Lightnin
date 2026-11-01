import numpy as np
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class PVArraySpecification(BaseModel):
    id: str = "pv-array-1"
    tilt_angle_deg: float = 15.0
    panel_count: int = 24
    array_length_m: float = 12.0
    array_width_m: float = 6.0
    metallic_frame_bonded: bool = True
    separation_to_lps_m: float = 0.85
    lps_class: str = "I"
    down_conductor_length_l_m: float = 15.0
    insulation_medium: str = "air" # air or solid

class PVClearanceResult(BaseModel):
    required_separation_s_m: float
    actual_clearance_m: float
    is_isolated_lps_sufficient: bool
    requires_equipotential_bonding: bool
    loop_area_risk: str
    status: str
    engineering_recommendations: List[str] = Field(default_factory=list)

class PVEngineeringModule:
    """
    Advanced PV Rooftop Engineering Module (IEC 62305-3 Supplement 5 & CLC/TS 50539-12).

    Evaluates:
    - Separation distance s to metallic solar module support frameworks
    - Direct flashover hazard vs. isolated LPS requirements
    - Inductive surge loop area minimization rules for DC string cabling
    """
    def evaluate_pv_installation(self, pv: PVArraySpecification) -> PVClearanceResult:
        # ki per LPS Class
        ki = 0.08 if pv.lps_class == "I" else (0.06 if pv.lps_class == "II" else 0.04)
        km = 1.0 if pv.insulation_medium == "air" else 0.5
        kc = 0.5 # Dual path down-conductor assumption

        # s = ki * (kc / km) * l
        s_req = float(ki * (kc / km) * pv.down_conductor_length_l_m)
        is_isolated = pv.separation_to_lps_m >= s_req

        recommendations = []
        if is_isolated:
            recommendations.append("Isolated LPS achieved: No direct lightning current will enter PV framework.")
            recommendations.append("Bond module frames to local equipotential earthing bar with 6 mm2 Cu.")
            requires_bonding_to_lps = False
        else:
            recommendations.append(
                f"Separation distance violated (Actual: {pv.separation_to_lps_m:.2f}m < Req: {s_req:.2f}m). "
                "Must directly bond PV metallic frame to external LPS conductor using 16 mm2 Cu conductor."
            )
            recommendations.append("Install Type 1 (Class I) DC SPDs at inverter DC inputs due to direct flashover risk.")
            requires_bonding_to_lps = True

        # Inductive loop area advisory
        recommendations.append("Route DC+ and DC- string cables in direct physical contact to minimize inductive loop area.")

        return PVClearanceResult(
            required_separation_s_m=round(s_req, 3),
            actual_clearance_m=round(pv.separation_to_lps_m, 3),
            is_isolated_lps_sufficient=is_isolated,
            requires_equipotential_bonding=requires_bonding_to_lps,
            loop_area_risk="LOW" if is_isolated else "HIGH",
            status="ISOLATED_PASS" if is_isolated else "BONDING_MANDATORY",
            engineering_recommendations=recommendations
        )
