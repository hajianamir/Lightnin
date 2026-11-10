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
        # IEC 62305-3:2024, Clause 6.3 separation-distance parameters
        # (Tables 11, 12, and 13 verified against IEC 62305-3:2024 text)
        iec_3 = StandardPart(
            standard_id="IEC 62305-3",
            edition="2024",
            parameters={
                "ki_class_I": StandardParameter(
                    parameter_id="ki_class_I",
                    value=0.08,
                    unit="dimensionless",
                    description="ki coefficient for LPS Class I (Table 11)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "ki_class_II": StandardParameter(
                    parameter_id="ki_class_II",
                    value=0.06,
                    unit="dimensionless",
                    description="ki coefficient for LPS Class II (Table 11)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "ki_class_III_IV": StandardParameter(
                    parameter_id="ki_class_III_IV",
                    value=0.04,
                    unit="dimensionless",
                    description="ki coefficient for LPS Class III and IV (Table 11)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "km_air": StandardParameter(
                    parameter_id="km_air",
                    value=1.0,
                    unit="dimensionless",
                    description="km coefficient for air insulation (Table 12)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "km_solid": StandardParameter(
                    parameter_id="km_solid",
                    value=0.5,
                    unit="dimensionless",
                    description="km coefficient for concrete, bricks, wood (Table 12)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "km_insulating_standoff": StandardParameter(
                    parameter_id="km_insulating_standoff",
                    value=0.7,
                    unit="dimensionless",
                    description="km coefficient for FRP, PE or PVC insulating stand-off with minimum length 0.5 m (Table 12 NOTE 1)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "kc_n_1_isolated": StandardParameter(
                    parameter_id="kc_n_1_isolated",
                    value=1.0,
                    unit="dimensionless",
                    description="Approximated kc for n = 1 down conductor, only in the case of an isolated LPS (Table 13)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "kc_n_2": StandardParameter(
                    parameter_id="kc_n_2",
                    value=0.66,
                    unit="dimensionless",
                    description="Approximated kc for n = 2 down conductors (Table 13)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "kc_n_3_or_more": StandardParameter(
                    parameter_id="kc_n_3_or_more",
                    value=0.44,
                    unit="dimensionless",
                    description="Approximated kc for n = 3 and more down conductors (Table 13)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
                "kc_earth_resistance_fallback": StandardParameter(
                    parameter_id="kc_earth_resistance_fallback",
                    value=1.0,
                    unit="dimensionless",
                    description="kc assumed when single earth electrode resistances differ by more than a factor of 2 (Table 13)",
                    source_clause="IEC 62305-3:2024, Clause 6.3",
                    verification_status="verified",
                ),
            },
        )
        self._parts["IEC 62305-3:2024"] = iec_3

    def get_parameter(self, standard_key: str, param_id: str) -> Optional[StandardParameter]:
        part = self._parts.get(standard_key)
        if part:
            return part.parameters.get(param_id)
        return None
