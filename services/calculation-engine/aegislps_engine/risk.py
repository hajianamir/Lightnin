from pydantic import BaseModel

class RiskAssessmentInput(BaseModel):
    structure_length_m: float
    structure_width_m: float
    structure_height_m: float
    ng_flashes_per_km2_year: float = 2.5 # Lightning ground flash density
    environmental_factor: float = 1.0 # Suburban / Urban / Isolated
    lps_class: str = "I"

class RiskAssessmentResult(BaseModel):
    collection_area_ad_m2: float
    annual_flashes_nd: float
    tolerable_risk_rt: float = 1e-5 # 10^-5 for Loss of Human Life (R1)
    calculated_risk_r1: float
    risk_acceptable: bool

class RiskManagementEngine:
    def evaluate_r1_risk(self, inputs: RiskAssessmentInput) -> RiskAssessmentResult:
        # Ad = L*W + 6*H*(L+W) + 9*pi*H^2
        l, w, h = inputs.structure_length_m, inputs.structure_width_m, inputs.structure_height_m
        ad = (l * w) + 6 * h * (l + w) + 9 * 3.14159 * (h ** 2)
        nd = ad * inputs.ng_flashes_per_km2_year * inputs.environmental_factor * 1e-6

        # Simplified R1 risk component estimation
        p_a = 0.01 if inputs.lps_class == "I" else 0.05
        l_u = 0.01 # Loss fraction
        r1 = nd * p_a * l_u

        rt = 1e-5
        return RiskAssessmentResult(
            collection_area_ad_m2=round(ad, 2),
            annual_flashes_nd=round(nd, 5),
            tolerable_risk_rt=rt,
            calculated_risk_r1=r1,
            risk_acceptable=r1 <= rt
        )
