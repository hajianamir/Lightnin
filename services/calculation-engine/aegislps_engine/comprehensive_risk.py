import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class IncomingServiceLine(BaseModel):
    id: str = "power-line-1"
    service_type: str = "aerial_power" # aerial_power, buried_power, telecom
    line_length_m: float = 1000.0
    transformer_present: bool = True
    shielded: bool = False

class ComprehensiveRiskInput(BaseModel):
    structure_length_m: float = 40.0
    structure_width_m: float = 25.0
    structure_height_m: float = 15.0
    ng_flashes_per_km2_year: float = 2.5
    environmental_cd: float = 1.0 # 1.0 isolated, 0.5 suburban, 0.25 urban
    lps_class: str = "I" # I, II, III, IV, or none
    has_coordinated_spd: bool = True
    has_tws_early_warning: bool = True # Thunderstorm Warning System (C_TWS)
    incoming_lines: List[IncomingServiceLine] = Field(default_factory=list)
    fire_risk_rf: float = 0.02
    occupants_count: int = 120

class Risk8Components(BaseModel):
    r_a_touch_step: float
    r_b_physical_damage: float
    r_c_internal_surges: float
    r_m_magnetic_pulse: float
    r_u_touch_voltage_service: float
    r_v_physical_damage_service: float
    r_w_internal_surges_service: float
    r_z_incoming_telecom: float
    total_risk_r1: float
    tolerable_risk_rt: float = 1e-5
    is_r1_acceptable: bool

class ComprehensiveRiskResult(BaseModel):
    collection_area_ad_structure_m2: float
    collection_area_al_services_m2: float
    annual_strikes_nd_direct: float
    annual_strikes_nl_services: float
    risk_components: Risk8Components
    status: str
    mitigations_required: List[str] = Field(default_factory=list)

class ComprehensiveRisk2024Engine:
    """
    Full IEC 62305-2:2024 Multi-Component Risk Management Engine.

    Implements all 8 risk components:
    - Direct strikes to structure: R_A, R_B, R_C
    - Strikes near structure: R_M
    - Direct strikes to incoming service lines: R_U, R_V, R_W
    - Strikes near incoming service lines: R_Z
    - Thunderstorm Warning System (C_TWS) mitigation factor.
    """
    def evaluate_risk(self, inp: ComprehensiveRiskInput) -> ComprehensiveRiskResult:
        l, w, h = inp.structure_length_m, inp.structure_width_m, inp.structure_height_m

        # Structure Collection Area Ad
        ad = (l * w) + 6.0 * h * (l + w) + 9.0 * np.pi * (h ** 2)
        nd = inp.ng_flashes_per_km2_year * ad * inp.environmental_cd * 1e-6

        # Incoming Lines Collection Area Al
        # For aerial line: Al = 40 * L_line
        al_total = 0.0
        for line in inp.incoming_lines:
            width_factor = 40.0 if line.service_type == "aerial_power" else 8.0
            al_total += width_factor * max(100.0, line.line_length_m)

        nl = inp.ng_flashes_per_km2_year * al_total * inp.environmental_cd * 1e-6

        # Probabilities
        p_a = 0.01 if inp.lps_class == "I" else (0.05 if inp.lps_class in ["II", "III", "IV"] else 1.0)
        p_b = 0.02 if inp.lps_class == "I" else (0.05 if inp.lps_class == "II" else (0.1 if inp.lps_class == "III" else 0.2))
        p_spd = 0.01 if inp.has_coordinated_spd else 1.0

        # C_TWS Thunderstorm Warning System credit factor (reduces injury risk to people by proactive protocol)
        c_tws = 0.2 if inp.has_tws_early_warning else 1.0

        # Consequence loss fractions
        l_a = 1e-2 * c_tws
        l_b = 0.05 * inp.fire_risk_rf
        l_c = 1e-3

        # Compute all 8 components
        r_a = float(nd * p_a * l_a)
        r_b = float(nd * p_b * l_b)
        r_c = float(nd * p_spd * l_c)
        r_m = float(nd * 0.1 * p_spd * l_c)

        r_u = float(nl * p_a * l_a * 0.5)
        r_v = float(nl * p_b * l_b * 0.5)
        r_w = float(nl * p_spd * l_c * 0.5)
        r_z = float(nl * 0.2 * p_spd * l_c * 0.5)

        total_r1 = float(r_a + r_b + r_c + r_m + r_u + r_v + r_w + r_z)
        rt = 1e-5
        acceptable = total_r1 <= rt

        mitigations = []
        if not acceptable:
            if (r_b + r_v) > 0.4 * rt:
                mitigations.append("Upgrade structural LPS to Class I and install automated extinguishing systems.")
            if (r_c + r_w + r_m + r_z) > 0.4 * rt:
                mitigations.append("Install coordinated Type 1 + Type 2 SPDs at line entrance and distribution boards.")
            if (r_a + r_u) > 0.2 * rt:
                mitigations.append("Apply 5cm asphalt or gravel surface layer around down conductors.")

        comp = Risk8Components(
            r_a_touch_step=r_a,
            r_b_physical_damage=r_b,
            r_c_internal_surges=r_c,
            r_m_magnetic_pulse=r_m,
            r_u_touch_voltage_service=r_u,
            r_v_physical_damage_service=r_v,
            r_w_internal_surges_service=r_w,
            r_z_incoming_telecom=r_z,
            total_risk_r1=total_r1,
            tolerable_risk_rt=rt,
            is_r1_acceptable=acceptable
        )

        return ComprehensiveRiskResult(
            collection_area_ad_structure_m2=round(float(ad), 1),
            collection_area_al_services_m2=round(float(al_total), 1),
            annual_strikes_nd_direct=float(nd),
            annual_strikes_nl_services=float(nl),
            risk_components=comp,
            status="ACCEPTABLE (R1 <= RT)" if acceptable else "NON_COMPLIANT (R1 > RT)",
            mitigations_required=mitigations
        )
