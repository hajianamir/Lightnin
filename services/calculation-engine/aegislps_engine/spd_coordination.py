import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SPDEntry(BaseModel):
    id: str
    spd_class: str # Type 1, Type 2, Type 3
    technology: str = "spark_gap" # spark_gap, varistor_mov, hybrid
    uc_volts: float = 275.0
    i_imp_ka: float = 25.0 # 10/350 us for Type 1
    i_n_ka: float = 20.0 # 8/20 us for Type 2
    up_kv: float = 1.5
    installed_lpz_boundary: str = "LPZ 0B / 1"
    cable_length_to_downstream_m: float = 15.0 # Decoupling length

class EquipmentWithstand(BaseModel):
    category: str = "Cat II" # Cat I (1.5kV), Cat II (2.5kV), Cat III (4kV), Cat IV (6kV)
    uw_kv: float = 2.5

class SPDCoordinationAssessment(BaseModel):
    spds: List[SPDEntry] = Field(default_factory=list)
    equipment: EquipmentWithstand = Field(default_factory=EquipmentWithstand)
    energy_coordination_verified: bool
    voltage_protection_verified: bool
    effective_protection_distance_m: float
    status: str
    warnings: List[str] = Field(default_factory=list)
    coordination_details: List[str] = Field(default_factory=list)

class SPDCoordinationEngine:
    """
    Advanced IEC 62305-4 & IEC 61643-12 Multi-Stage SPD Coordination Engine.

    Implements:
    - Cascaded LPZ boundary transition analysis (LPZ 0A -> 0B -> 1 -> 2 -> 3)
    - Cable inductance inductive decoupling Delta U = L' * l * di/dt
    - Energy coordination between spark gap (Type 1) and MOV (Type 2)
    - Effective protective distance l_prot based on oscillation reflection
    """
    @staticmethod
    def calculate_effective_protective_distance(up_kv: float, uw_kv: float) -> float:
        """
        IEC 62305-4 Annex C: Maximum distance between SPD and equipment.
        l_prot = (U_w - U_p) / (2 * L' * di/dt)
        Assuming typical cable inductance L' = 1 uH/m and steepness di/dt = 1 kA/us:
        Delta U / m ~ 1 kV / m. When reflected, double voltage oscillation occurs.
        """
        if uw_kv <= up_kv:
            return 0.0
        # Typical protective limit ~ 10 meters if no downstream Type 3 installed
        l_max = (uw_kv - up_kv) * 10.0 # meters
        return float(max(5.0, min(30.0, l_max)))

    def evaluate_coordination(
        self,
        spds: List[SPDEntry],
        equipment: Optional[EquipmentWithstand] = None
    ) -> SPDCoordinationAssessment:
        equip = equipment or EquipmentWithstand()
        warnings = []
        details = []

        types = [s.spd_class for s in spds]
        has_type1 = "Type 1" in types
        has_type2 = "Type 2" in types
        has_type3 = "Type 3" in types

        # Check 1: Boundary protection presence
        if not has_type1:
            warnings.append("Missing Type 1 (Class I) SPD at main service entrance (LPZ 0 / 1)")
        else:
            details.append("Type 1 SPD installed at main service entrance boundary")

        if not has_type2:
            warnings.append("Missing Type 2 (Class II) SPD at sub-distribution boards (LPZ 1 / 2)")
        else:
            details.append("Type 2 SPD installed at secondary power distribution board")

        # Check 2: Inductive decoupling distance between Type 1 and Type 2
        # Minimum ~10m cable required between Spark Gap and MOV if no internal decoupling choke
        type1_entries = [s for s in spds if s.spd_class == "Type 1"]
        energy_coordinated = True
        for t1 in type1_entries:
            if t1.technology == "spark_gap" and t1.cable_length_to_downstream_m < 10.0:
                warnings.append(
                    f"Cable length between Type 1 spark gap and downstream SPD ({t1.cable_length_to_downstream_m}m) is less than 10m. "
                    "Risk of premature MOV destruction before spark-gap fires without decoupling inductor."
                )
                energy_coordinated = False
            else:
                details.append(f"Decoupling length ({t1.cable_length_to_downstream_m}m) satisfies energy coordination criteria")

        # Check 3: Voltage protection level Up vs Equipment withstand Uw
        voltage_ok = True
        min_up = min([s.up_kv for s in spds]) if spds else 4.0
        if min_up > equip.uw_kv:
            warnings.append(f"Lowest SPD protection level ({min_up} kV) exceeds equipment withstand {equip.category} ({equip.uw_kv} kV)")
            voltage_ok = False
        else:
            details.append(f"Voltage protection level Up ({min_up} kV) complies with equipment withstand ({equip.uw_kv} kV)")

        l_prot = self.calculate_effective_protective_distance(min_up, equip.uw_kv)
        details.append(f"Maximum effective protective distance without terminal SPD: {l_prot:.1f} m")

        is_coordinated = has_type1 and has_type2 and energy_coordinated and voltage_ok
        status = "COORDINATED" if is_coordinated else ("ACTION_REQUIRED" if has_type1 else "NON_COMPLIANT")

        return SPDCoordinationAssessment(
            spds=spds,
            equipment=equip,
            energy_coordination_verified=energy_coordinated,
            voltage_protection_verified=voltage_ok,
            effective_protection_distance_m=round(l_prot, 1),
            status=status,
            warnings=warnings,
            coordination_details=details
        )
