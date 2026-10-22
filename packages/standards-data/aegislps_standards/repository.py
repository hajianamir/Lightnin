from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class StandardParameter(BaseModel):
    parameter_id: str
    value: float
    unit: str
    description: str
    source_clause: str
    verification_status: str = "pending"

class StandardPart(BaseModel):
    standard_id: str
    edition: str
    corrigenda: List[str] = Field(default_factory=list)
    parameters: Dict[str, StandardParameter] = Field(default_factory=dict)
    verification_status: str = "pending"

class StandardsRepository:
    def __init__(self):
        self._parts: Dict[str, StandardPart] = {}
        self._load_baseline()

    def _load_baseline(self):
        # Baseline IEC 62305:2024 structured data registration
        iec_3 = StandardPart(
            standard_id="IEC 62305-3",
            edition="2024",
            parameters={
                "ki_class_I": StandardParameter(
                    parameter_id="ki_class_I",
                    value=0.08,
                    unit="dimensionless",
                    description="ki coefficient for LPS Class I",
                    source_clause="IEC 62305-3:2024 Table 10",
                    verification_status="pending"
                ),
                "ki_class_II": StandardParameter(
                    parameter_id="ki_class_II",
                    value=0.06,
                    unit="dimensionless",
                    description="ki coefficient for LPS Class II",
                    source_clause="IEC 62305-3:2024 Table 10",
                    verification_status="pending"
                ),
                "ki_class_III_IV": StandardParameter(
                    parameter_id="ki_class_III_IV",
                    value=0.04,
                    unit="dimensionless",
                    description="ki coefficient for LPS Class III and IV",
                    source_clause="IEC 62305-3:2024 Table 10",
                    verification_status="pending"
                ),
                "km_air": StandardParameter(
                    parameter_id="km_air",
                    value=1.0,
                    unit="dimensionless",
                    description="km coefficient for air medium",
                    source_clause="IEC 62305-3:2024 Table 11",
                    verification_status="pending"
                ),
                "km_solid": StandardParameter(
                    parameter_id="km_solid",
                    value=0.5,
                    unit="dimensionless",
                    description="km coefficient for solid concrete/brick medium",
                    source_clause="IEC 62305-3:2024 Table 11",
                    verification_status="pending"
                )
            }
        )
        self._parts["IEC 62305-3:2024"] = iec_3

    def get_parameter(self, standard_key: str, param_id: str) -> Optional[StandardParameter]:
        part = self._parts.get(standard_key)
        if part:
            return part.parameters.get(param_id)
        return None
