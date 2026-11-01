from typing import Dict, List, Any
from pydantic import BaseModel, Field

class HVIConductorSelectionInput(BaseModel):
    lps_class: str = "I"
    required_equivalent_separation_s_air_m: float = 0.75 # Required separation distance in air
    down_conductor_route_length_m: float = 18.0
    hvi_conductor_model: str = "HVI_light_75" # HVI_light_75 (s_equiv=0.75m), HVI_standard_90 (s_equiv=0.90m)
    ambient_installation_type: str = "outdoor_façade"

class HVIConductorSelectionResult(BaseModel):
    hvi_conductor_model: str
    equivalent_separation_distance_se_m: float
    required_s_air_m: float
    is_adequate_insulation: bool
    max_permitted_route_length_m: float
    length_limit_exceeded: bool
    requires_capacitive_sealing_ground: bool
    status: str
    technical_specifications: List[str] = Field(default_factory=list)

class HVIConductorAssistant:
    """
    High-Voltage Insulated (HVI) Down-Conductor Selection & Verification Engine.

    Evaluates:
    - High-voltage impulse dielectric withstand (equivalent separation distance in solid insulation s_e)
    - Capacitive semi-conductive shield sheath grounding at sealing ends to control electric field stress
    - Maximum permissible conductor length limits under lightning impulse steepness.
    """
    HVI_SPECS = {
        "HVI_light_75": {
            "s_equiv_air": 0.75, # meters equivalent separation in air
            "s_equiv_solid": 1.50, # meters equivalent in solid
            "max_length_m": 25.0,
            "impulse_withstand_kv": 150.0
        },
        "HVI_standard_90": {
            "s_equiv_air": 0.90,
            "s_equiv_solid": 1.80,
            "max_length_m": 35.0,
            "impulse_withstand_kv": 200.0
        }
    }

    def evaluate_hvi_selection(self, inp: HVIConductorSelectionInput) -> HVIConductorSelectionResult:
        spec = self.HVI_SPECS.get(inp.hvi_conductor_model, self.HVI_SPECS["HVI_light_75"])

        is_adequate = spec["s_equiv_air"] >= inp.required_equivalent_separation_s_air_m
        len_exceeded = inp.down_conductor_route_length_m > spec["max_length_m"]

        specs = [
            f"Rated equivalent separation distance in air: s_e = {spec['s_equiv_air']} m.",
            f"Rated impulse withstand voltage: {spec['impulse_withstand_kv']} kV (1.2/50 us waveform).",
            f"Maximum permissible continuous route length: {spec['max_length_m']} m.",
            "Mandatory capacitive control: Outer semi-conductive sheath must be bonded to equipotential bar at sealing end."
        ]

        if not is_adequate:
            specs.append(f"WARNING: Required separation distance ({inp.required_equivalent_separation_s_air_m:.2f}m) exceeds HVI rated s_e ({spec['s_equiv_air']}m). Upgrade to HVI_standard_90 or parallel paths.")
        if len_exceeded:
            specs.append(f"WARNING: Route length ({inp.down_conductor_route_length_m}m) exceeds manufacturer max length ({spec['max_length_m']}m).")

        status = "COMPLIANT_APPROVED" if (is_adequate and not len_exceeded) else "NON_COMPLIANT_HAZARD"

        return HVIConductorSelectionResult(
            hvi_conductor_model=inp.hvi_conductor_model,
            equivalent_separation_distance_se_m=spec["s_equiv_air"],
            required_s_air_m=inp.required_equivalent_separation_s_air_m,
            is_adequate_insulation=is_adequate,
            max_permitted_route_length_m=spec["max_length_m"],
            length_limit_exceeded=len_exceeded,
            requires_capacitive_sealing_ground=True,
            status=status,
            technical_specifications=specs
        )
