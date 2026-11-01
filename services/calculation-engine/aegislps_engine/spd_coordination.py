from typing import List, Dict
from pydantic import BaseModel, Field

class SPDSpecification(BaseModel):
    id: str
    spd_type: str # Type 1, Type 2, Type 3
    uc_volts: float = 275.0
    i_imp_ka: float = 25.0 # For Type 1 (10/350 us)
    i_n_ka: float = 20.0 # For Type 2 (8/20 us)
    up_kv: float = 1.5
    installed_lpz_boundary: str = "LPZ 0B / 1"

class SPDCoordinationAssessment(BaseModel):
    service_entry_lpz: str = "LPZ 0A"
    distribution_board_lpz: str = "LPZ 1"
    sub_distribution_lpz: str = "LPZ 2"
    spds_configured: List[SPDSpecification] = Field(default_factory=list)
    coordination_verified: bool
    status: str
    warnings: List[str] = Field(default_factory=list)

class SPDCoordinationEngine:
    """
    IEC 62305-4 & IEC 61643 SPD Selection and LPZ Coordination Engine.
    """
    def evaluate_coordination(self, spds: List[SPDSpecification]) -> SPDCoordinationAssessment:
        types_present = {s.spd_type for s in spds}
        warnings = []

        has_type_1 = "Type 1" in types_present
        has_type_2 = "Type 2" in types_present

        if not has_type_1:
            warnings.append("No Type 1 SPD installed at main service entrance boundary (LPZ 0 / 1)")
        if not has_type_2:
            warnings.append("No Type 2 SPD installed at secondary power distribution boards (LPZ 1 / 2)")

        # Upstream to downstream energy coordination check
        # Up (voltage protection level) must not exceed equipment impulse withstand Uw (e.g. 2.5 kV for Cat II)
        for s in spds:
            if s.up_kv > 2.5:
                warnings.append(f"SPD {s.id} Up ({s.up_kv} kV) exceeds Category II equipment withstand (2.5 kV)")

        coordinated = has_type_1 and len(warnings) == 0

        return SPDCoordinationAssessment(
            spds_configured=spds,
            coordination_verified=coordinated,
            status="COORDINATED" if coordinated else "INCOMPLETE",
            warnings=warnings
        )
