from typing import List
from pydantic import BaseModel, Field

class TouchStepAssessmentInput(BaseModel):
    lps_class: str = "I"
    soil_surface_type: str = "bare_soil" # bare_soil, asphalt_5cm, gravel_5cm, concrete
    conductor_accessible: bool = True
    has_insulation_barrier: bool = False
    physical_distance_to_conductor_m: float = 0.5

class TouchStepAssessmentResult(BaseModel):
    permissible_touch_voltage_v: float
    expected_touch_voltage_kv: float
    touch_hazard_controlled: bool
    step_hazard_controlled: bool
    recommended_mitigations: List[str] = Field(default_factory=list)
    status: str

class TouchStepEngine:
    """
    IEC 62305-3 Section 8 Protection against touch and step voltages.
    """
    def evaluate(self, inp: TouchStepAssessmentInput) -> TouchStepAssessmentResult:
        # Surface layer contact resistance
        surface_res = {
            "bare_soil": 100.0,
            "gravel_5cm": 1000.0,
            "asphalt_5cm": 10000.0,
            "concrete": 500.0
        }.get(inp.soil_surface_type, 100.0)

        # Body resistance 1000 ohm, foot contact resistance 3 * rho_s
        # Tolerable touch voltage Ut = 50V AC / 120V DC continuous, or impulse withstand ~ 25 kV with 100 kA
        permissible_v = 1000.0 + 1.5 * surface_res

        # If barrier or high-voltage insulation present (3m height clearance or 100kV impulse insulation)
        touch_controlled = inp.has_insulation_barrier or not inp.conductor_accessible or (surface_res >= 10000.0)
        step_controlled = surface_res >= 1000.0 or not inp.conductor_accessible

        mitigations = []
        if not touch_controlled:
            mitigations.append("Apply 5cm asphalt layer (resistivity >= 10 kOhm.m) within 3m of down-conductor")
            mitigations.append("Encase down-conductor in cross-linked polyethylene insulating conduit (withstand >= 100 kV, 1.2/50 us)")
        if not step_controlled:
            mitigations.append("Lay 5cm gravel layer (resistivity >= 1 kOhm.m) surrounding earth electrode termination")

        status = "COMPLIANT" if (touch_controlled and step_controlled) else "ACTION_REQUIRED"

        return TouchStepAssessmentResult(
            permissible_touch_voltage_v=round(float(permissible_v), 1),
            expected_touch_voltage_kv=50.0 if not touch_controlled else 0.5,
            touch_hazard_controlled=touch_controlled,
            step_hazard_controlled=step_controlled,
            recommended_mitigations=mitigations,
            status=status
        )
