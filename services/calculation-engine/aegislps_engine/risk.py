import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class RiskAssessmentInput(BaseModel):
    structure_length_m: float = 30.0
    structure_width_m: float = 20.0
    structure_height_m: float = 15.0
    ng_flashes_per_km2_year: float = 2.5 # Ground flash density Ng
    environmental_cd: float = 1.0 # 1.0 = isolated, 0.5 = suburban, 0.25 = urban
    lps_class: str = "I" # Class I, II, III, IV, or none
    fire_risk_rf: float = 0.01 # Normal risk of fire
    has_automatic_fire_system: bool = True # rp = 0.5
    has_coordinated_spd: bool = True # p_spd = 0.01 for Class I
    number_of_occupants: int = 100
    time_in_structure_hours_per_year: float = 2190.0 # 25% of year

class RiskAssessmentResult(BaseModel):
    collection_area_ad_m2: float
    annual_strikes_nd: float
    risk_ra_touch_step: float # Risk due to touch and step potential
    risk_rb_physical_damage: float # Risk due to physical fire/destruction
    risk_rc_internal_systems: float # Risk due to electronic overvoltage surges
    risk_r1_loss_of_life: float # Total R1 risk
    tolerable_risk_rt: float = 1e-5 # Tolerable threshold for loss of human life
    risk_acceptable: bool
    status: str
    mitigation_recommendations: List[str] = Field(default_factory=list)

class RiskManagementEngine:
    """
    Advanced IEC 62305-2 Risk Assessment Engine.

    Implements:
    - Equivalent collection area calculation A_d
    - Annual frequency of direct dangerous events N_D
    - Detailed loss of human life (R1) component breakdown:
      R_1 = R_A + R_B + R_C + R_M
      where:
      - R_A = N_D * P_A * L_A (Injury to living beings by touch/step potential)
      - R_B = N_D * P_B * L_B (Physical damage caused by fire/explosion)
      - R_C = N_D * P_C * L_C (Failure of internal systems from surges)
    - Quantitative evaluation against tolerable risk threshold R_T = 1.0 x 10^-5
    """
    def evaluate_r1_risk(self, inputs: RiskAssessmentInput) -> RiskAssessmentResult:
        l, w, h = inputs.structure_length_m, inputs.structure_width_m, inputs.structure_height_m

        # IEC 62305-2 Equation A.2 Collection Area Ad
        # Ad = L*W + 2*(3*H)*(L+W) + pi*(3*H)^2
        ad = (l * w) + 6.0 * h * (l + w) + 9.0 * np.pi * (h ** 2)

        # Expected direct strikes per year N_D = N_g * A_d * C_d * 10^-6
        nd = inputs.ng_flashes_per_km2_year * ad * inputs.environmental_cd * 1e-6

        # Probability factors based on protection measures
        # P_A: Touch/step protection (warning signs, asphalt, equipotentialization)
        p_a = 0.01 if inputs.lps_class == "I" else (0.05 if inputs.lps_class in ["II", "III", "IV"] else 1.0)

        # P_B: Physical damage probability (LPS Class)
        p_b_map = {"I": 0.02, "II": 0.05, "III": 0.10, "IV": 0.20}
        p_b = p_b_map.get(inputs.lps_class, 1.0)

        # P_C: Internal systems failure probability (SPD coordination)
        p_spd = 0.01 if (inputs.has_coordinated_spd and inputs.lps_class == "I") else (0.05 if inputs.has_coordinated_spd else 1.0)

        # Consequence loss factors L_A, L_B, L_C
        t_occupancy = min(1.0, inputs.time_in_structure_hours_per_year / 8760.0)
        l_t = 1e-2 * t_occupancy # Typical loss fraction for injury
        l_f = 0.1 * inputs.fire_risk_rf * (0.5 if inputs.has_automatic_fire_system else 1.0) * t_occupancy
        l_o = 1e-3 * t_occupancy # System failure consequence to life support

        # Risk components
        r_a = float(nd * p_a * l_t)
        r_b = float(nd * p_b * l_f)
        r_c = float(nd * p_spd * l_o)

        total_r1 = float(r_a + r_b + r_c)
        rt = 1e-5
        acceptable = total_r1 <= rt

        mitigations = []
        if not acceptable:
            if r_b > 0.5 * rt:
                mitigations.append("Upgrade LPS to Class I mesh and air termination rods to reduce R_B")
                mitigations.append("Install automated gas/water fire extinguishing systems to halve loss L_F")
            if r_c > 0.3 * rt:
                mitigations.append("Install coordinated Type 1 + Type 2 SPDs at LPZ 0/1/2 boundaries to minimize R_C")
            if r_a > 0.3 * rt:
                mitigations.append("Apply 5cm asphalt or gravel surface layer around down conductors to reduce R_A")

        status = "ACCEPTABLE (R1 <= RT)" if acceptable else "UNACCEPTABLE (R1 > RT)"

        return RiskAssessmentResult(
            collection_area_ad_m2=round(float(ad), 1),
            annual_strikes_nd=float(nd),
            risk_ra_touch_step=float(r_a),
            risk_rb_physical_damage=float(r_b),
            risk_rc_internal_systems=float(r_c),
            risk_r1_loss_of_life=float(total_r1),
            tolerable_risk_rt=rt,
            risk_acceptable=acceptable,
            status=status,
            mitigation_recommendations=mitigations
        )
