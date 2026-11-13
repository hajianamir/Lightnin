"""Multi-stage SPD coordination engine per IEC 62305-4:2024 Annex C.2.3 & C.2.5."""

import math
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_VALID_SPD_CLASSES = ("Type 1", "Type 2", "Type 3")
_VALID_TECHNOLOGIES = ("spark_gap", "varistor_mov", "hybrid")
_VALID_EQUIPMENT_CATEGORIES = ("Cat I", "Cat II", "Cat III", "Cat IV")

# IEC 62305-4:2024 Clause C.2.3.3 Eq. (C.4) (p. 90): ΔU = 0.1 * I_SPD [kV/m]
_EQ_C4_KV_PER_KA_M: float = 0.1
# IEC 62305-4:2024 Clause C.2.5 (pp. 92–93): connecting lead length should not be greater than 0,5 m
_DEFAULT_CONNECTING_LEAD_M: float = 0.5
# IEC 62305-4:2024 Clause C.2.3.1.2 (p. 88): U_p should not exceed 80 % of U_w when the equipment is <= 10 m
# from the entrance SPD. Clause C.2.3.1.4 (p. 89): for > 10 m, one-port SPD at the origin: U_p <= 50 % of U_w.
# The code applies the stricter 0.5 * U_w bound to all cases as a conservative screen (conservative screening bound (C.2.3.1.4)).
_RULE1_UW_FACTOR: float = 0.5


class SPDEntry(BaseModel):
    """Single SPD stage entry for LPZ boundary coordination.

    Metadata fields retaining documented defaults (do not enter the Annex C.2.3
    ``U_p/f`` / ``U_w`` equations):
    - ``uc_volts`` (default ``275.0`` V): maximum continuous operating voltage label;
      validated ``> 0`` if provided.
    - ``installed_lpz_boundary`` (default ``"LPZ 0B / 1"``): installation zone label.
    """

    model_config = ConfigDict(allow_inf_nan=False)

    id: str
    spd_class: str  # Type 1, Type 2, Type 3
    technology: str  # spark_gap, varistor_mov, hybrid (required)
    uc_volts: Optional[float] = 275.0
    i_imp_ka: Optional[float] = None  # 10/350 µs; required for Type 1 (Clause C.2.3.2 NOTE 2)
    i_n_ka: Optional[float] = None  # 8/20 µs; required for Type 2 and Type 3
    up_kv: float  # Required voltage protection level U_p [kV] (> 0)
    installed_lpz_boundary: str = "LPZ 0B / 1"
    cable_length_to_downstream_m: Optional[float] = None  # Required for Type 1 spark_gap [m]
    lead_length_m: Optional[float] = None  # Connecting lead length L = L1 + L2 + L3 [m] (Figure C.3)

    @field_validator(
        "uc_volts",
        "i_imp_ka",
        "i_n_ka",
        "up_kv",
        "cable_length_to_downstream_m",
        "lead_length_m",
        mode="before",
    )
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric SPD parameter.")
        return v

    @model_validator(mode="after")
    def _validate_spd(self) -> "SPDEntry":
        if not isinstance(self.spd_class, str) or self.spd_class not in _VALID_SPD_CLASSES:
            raise ValueError(
                f"Unknown spd_class {self.spd_class!r}; expected one of {_VALID_SPD_CLASSES}."
            )
        if not isinstance(self.technology, str) or self.technology not in _VALID_TECHNOLOGIES:
            raise ValueError(
                f"Unknown technology {self.technology!r}; expected one of {_VALID_TECHNOLOGIES}."
            )
        if not math.isfinite(self.up_kv) or self.up_kv <= 0.0:
            raise ValueError(f"up_kv must be finite and > 0, got {self.up_kv!r}.")
        if self.uc_volts is not None:
            if not math.isfinite(self.uc_volts) or self.uc_volts <= 0.0:
                raise ValueError(f"uc_volts must be finite and > 0, got {self.uc_volts!r}.")

        if self.i_imp_ka is not None:
            if not math.isfinite(self.i_imp_ka) or self.i_imp_ka <= 0.0:
                raise ValueError(f"i_imp_ka must be finite and > 0, got {self.i_imp_ka!r}.")
        if self.spd_class == "Type 1" and self.i_imp_ka is None:
            raise ValueError("i_imp_ka is required when spd_class == 'Type 1'.")

        if self.i_n_ka is not None:
            if not math.isfinite(self.i_n_ka) or self.i_n_ka <= 0.0:
                raise ValueError(f"i_n_ka must be finite and > 0, got {self.i_n_ka!r}.")
        if self.spd_class in ("Type 2", "Type 3") and self.i_n_ka is None:
            raise ValueError(
                f"i_n_ka is required when spd_class is {self.spd_class!r}."
            )

        if self.cable_length_to_downstream_m is not None:
            if (
                not math.isfinite(self.cable_length_to_downstream_m)
                or self.cable_length_to_downstream_m < 0.0
            ):
                raise ValueError(
                    f"cable_length_to_downstream_m must be finite and >= 0, got {self.cable_length_to_downstream_m!r}."
                )
        if (
            self.spd_class == "Type 1"
            and self.technology == "spark_gap"
            and self.cable_length_to_downstream_m is None
        ):
            raise ValueError(
                "cable_length_to_downstream_m is required when spd_class == 'Type 1' and technology == 'spark_gap'."
            )

        if self.lead_length_m is not None:
            if not math.isfinite(self.lead_length_m) or self.lead_length_m < 0.0:
                raise ValueError(
                    f"lead_length_m must be finite and >= 0, got {self.lead_length_m!r}."
                )
        return self


class EquipmentWithstand(BaseModel):
    """Protected equipment impulse withstand and loop parameters (IEC 62305-4:2024 Clause C.2.3).

    Parameters
    ----------
    category : str
        Overvoltage category label (IEC 62305-4:2024 Table A.1 / Table C.1:
        one of ``{"Cat I", "Cat II", "Cat III", "Cat IV"}``, default ``"Cat II"``;
        label metadata only — ``uw_kv`` carries the impulse withstand value).
    uw_kv : float
        Required rated impulse withstand voltage ``U_w`` in kV (``> 0``; no silent default).
    induced_voltage_kv : float
        Required loop induced overvoltage ``U_i`` in kV (Clause C.2.3.5; no silent default).
    reflection_coefficient_kr : float
        Reflection coefficient ``k_r`` in ``[1.0, 2.0]`` (Clause C.2.3.2 Eq. C.1, worst-case default ``2.0``).
    """

    model_config = ConfigDict(allow_inf_nan=False)

    category: str = "Cat II"  # Cat I, Cat II, Cat III, Cat IV (Table A.1 / Table C.1 metadata)
    uw_kv: float
    induced_voltage_kv: float
    reflection_coefficient_kr: float = 2.0

    @field_validator("uw_kv", "induced_voltage_kv", "reflection_coefficient_kr", mode="before")
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric equipment parameter.")
        if v is None:
            raise ValueError("Required numeric equipment parameter cannot be None.")
        return v

    @model_validator(mode="after")
    def _validate_equipment(self) -> "EquipmentWithstand":
        if (
            not isinstance(self.category, str)
            or self.category not in _VALID_EQUIPMENT_CATEGORIES
        ):
            raise ValueError(
                f"Unknown equipment category {self.category!r}; expected one of {_VALID_EQUIPMENT_CATEGORIES}."
            )
        if not math.isfinite(self.uw_kv) or self.uw_kv <= 0.0:
            raise ValueError(f"uw_kv must be finite and > 0, got {self.uw_kv!r}.")
        if not math.isfinite(self.induced_voltage_kv) or self.induced_voltage_kv < 0.0:
            raise ValueError(
                f"induced_voltage_kv must be finite and >= 0, got {self.induced_voltage_kv!r}."
            )
        if (
            not math.isfinite(self.reflection_coefficient_kr)
            or self.reflection_coefficient_kr < 1.0
            or self.reflection_coefficient_kr > 2.0
        ):
            raise ValueError(
                f"reflection_coefficient_kr must be in [1.0, 2.0], got {self.reflection_coefficient_kr!r}."
            )
        return self


class SPDCoordinationAssessment(BaseModel):
    """Assessment result for multi-stage SPD energy and Annex C.2.3 voltage coordination.

    ``max_connecting_lead_length_m`` is the maximum total SPD connecting-conductor length
    ``L = L_1 + L_2 + L_3`` (Figure C.3) for the equipment-side SPD computed from
    IEC 62305-4:2024 Equations (C.1)–(C.4), rounded to ``0.001 m``.
    """

    spds: List[SPDEntry] = Field(default_factory=list)
    equipment: EquipmentWithstand
    energy_coordination_verified: bool
    voltage_protection_verified: bool
    max_connecting_lead_length_m: float
    status: str
    warnings: List[str] = Field(default_factory=list)
    coordination_details: List[str] = Field(default_factory=list)


class SPDCoordinationEngine:
    """
    IEC 62305-4:2024 Annex C.2.3 & IEC 61643-12 Multi-Stage SPD Coordination Engine.

    Implements:
    - LPZ boundary presence & 10 m Type 1 spark-gap decoupling screening (IEC 61643-12)
    - Simplified Rule 1 check ``U_p <= 0.5 * U_w`` (IEC 62305-4:2024 Clause C.2.3.1.2 (p. 88):
      U_p should not exceed 80 % of U_w when the equipment is <= 10 m from the entrance SPD;
      Clause C.2.3.1.4 (p. 89): for > 10 m, one-port SPD at the origin: U_p <= 50 % of U_w;
      the code applies the stricter 0.5 * U_w bound to all cases as a conservative screen —
      conservative screening bound (C.2.3.1.4))
    - Detailed Rule 2 effective protection level ``U_req = (U_w - U_i) / k_r`` (Clause C.2.3.2, Eq. C.1)
    - Connecting-lead inductive drop ``ΔU = 0.1 * I_SPD * L`` (Clause C.2.3.3, Eq. C.4)
    - ``U_p/f`` for voltage-limiting / hybrid (Eq. C.2) and voltage-switching (Eq. C.3) SPDs
    - Oscillation bound ``U_p/f <= U_w`` (Clause C.2.3.4, Eq. C.5) and maximum connecting-lead length ``L_max``
    """

    @staticmethod
    def check_rule1_up(up_kv: float, uw_kv: float) -> bool:
        """IEC 62305-4:2024 Clause C.2.3.1.2 (p. 88): U_p should not exceed 80 % of U_w when the equipment is <= 10 m from the entrance SPD. Clause C.2.3.1.4 (p. 89): for > 10 m, one-port SPD at the origin: U_p <= 50 % of U_w. The code applies the stricter 0.5 * U_w bound to all cases as a conservative screen (conservative screening bound (C.2.3.1.4))."""
        return up_kv <= _RULE1_UW_FACTOR * uw_kv

    @staticmethod
    def calculate_required_upf_c1(
        uw_kv: float,
        induced_voltage_kv: float,
        reflection_coefficient_kr: float = 2.0,
    ) -> float:
        """IEC 62305-4:2024 Clause C.2.3.2 Eq. (C.1) (p. 89): ``U_p/f = (U_w - U_i) / k_r``."""
        if (
            isinstance(reflection_coefficient_kr, bool)
            or not math.isfinite(reflection_coefficient_kr)
            or reflection_coefficient_kr < 1.0
            or reflection_coefficient_kr > 2.0
        ):
            raise ValueError(
                f"reflection_coefficient_kr must be in [1.0, 2.0], got {reflection_coefficient_kr!r}."
            )
        if isinstance(uw_kv, bool) or not math.isfinite(uw_kv) or uw_kv <= 0.0:
            raise ValueError(f"uw_kv must be finite and > 0, got {uw_kv!r}.")
        if (
            isinstance(induced_voltage_kv, bool)
            or not math.isfinite(induced_voltage_kv)
            or induced_voltage_kv < 0.0
        ):
            raise ValueError(
                f"induced_voltage_kv must be finite and >= 0, got {induced_voltage_kv!r}."
            )
        return float((uw_kv - induced_voltage_kv) / reflection_coefficient_kr)

    @staticmethod
    def calculate_lead_voltage_drop_c4(i_spd_ka: float, lead_length_m: float) -> float:
        """IEC 62305-4:2024 Clause C.2.3.3 Eq. (C.4) (p. 90): ``ΔU = 0.1 * I_SPD * L`` [kV]."""
        if isinstance(i_spd_ka, bool) or not math.isfinite(i_spd_ka) or i_spd_ka <= 0.0:
            raise ValueError(f"i_spd_ka must be finite and > 0, got {i_spd_ka!r}.")
        if isinstance(lead_length_m, bool) or not math.isfinite(lead_length_m) or lead_length_m < 0.0:
            raise ValueError(f"lead_length_m must be finite and >= 0, got {lead_length_m!r}.")
        return float(_EQ_C4_KV_PER_KA_M * i_spd_ka * lead_length_m)

    @staticmethod
    def calculate_effective_protection_level_upf(
        up_kv: float,
        delta_u_kv: float,
        technology: str,
    ) -> float:
        """IEC 62305-4:2024 Clause C.2.3.3 Eq. (C.2) & Eq. (C.3) (p. 90)."""
        if not isinstance(technology, str) or technology not in _VALID_TECHNOLOGIES:
            raise ValueError(
                f"Unknown technology {technology!r}; expected one of {_VALID_TECHNOLOGIES}."
            )
        if technology in ("varistor_mov", "hybrid"):
            # Eq. (C.2): U_p/f = U_p + ΔU (hybrid treated conservatively as voltage-limiting)
            return float(up_kv + delta_u_kv)
        # Eq. (C.3): U_p/f = max(U_p, ΔU) for voltage-switching SPDs (spark_gap)
        return float(max(up_kv, delta_u_kv))

    @staticmethod
    def check_oscillation_c5(up_f_kv: float, uw_kv: float) -> bool:
        """IEC 62305-4:2024 Clause C.2.3.4 Eq. (C.5) (p. 92): ``U_p/f <= U_w``."""
        return up_f_kv <= uw_kv

    @staticmethod
    def get_spd_test_current_ka(spd: SPDEntry) -> float:
        """Return ``I_SPD`` in kA: ``i_imp_ka`` for Type 1, ``i_n_ka`` for Type 2 and Type 3."""
        if spd.spd_class == "Type 1":
            if spd.i_imp_ka is None or not math.isfinite(spd.i_imp_ka) or spd.i_imp_ka <= 0.0:
                raise ValueError("i_imp_ka must be finite and > 0 for Type 1 SPD.")
            return float(spd.i_imp_ka)
        if spd.spd_class in ("Type 2", "Type 3"):
            if spd.i_n_ka is None or not math.isfinite(spd.i_n_ka) or spd.i_n_ka <= 0.0:
                raise ValueError(f"i_n_ka must be finite and > 0 for {spd.spd_class} SPD.")
            return float(spd.i_n_ka)
        raise ValueError(
            f"Unknown spd_class {spd.spd_class!r}; expected one of {_VALID_SPD_CLASSES}."
        )

    @classmethod
    def calculate_max_connecting_lead_length_m(
        cls,
        up_kv: float,
        i_spd_ka: float,
        technology: str,
        u_req_kv: float,
    ) -> float:
        """Compute maximum SPD connecting-lead length ``L_max`` [m] from Eq. (C.1)–(C.4)."""
        if not isinstance(technology, str) or technology not in _VALID_TECHNOLOGIES:
            raise ValueError(
                f"Unknown technology {technology!r}; expected one of {_VALID_TECHNOLOGIES}."
            )
        denom_kv_per_m = _EQ_C4_KV_PER_KA_M * i_spd_ka
        if technology in ("varistor_mov", "hybrid"):
            numerator_kv = u_req_kv - up_kv
            if numerator_kv <= 0.0:
                return 0.0
            return float(numerator_kv / denom_kv_per_m)

        # Voltage-switching (spark_gap): require U_p <= U_req and positive U_req
        if u_req_kv <= 0.0 or up_kv > u_req_kv:
            return 0.0
        return float(u_req_kv / denom_kv_per_m)

    def evaluate_coordination(
        self,
        spds: List[SPDEntry],
        equipment: EquipmentWithstand,
    ) -> SPDCoordinationAssessment:
        if equipment is None or not isinstance(equipment, EquipmentWithstand):
            raise ValueError(
                "equipment (EquipmentWithstand with explicit uw_kv and induced_voltage_kv) is required."
            )
        equipment._validate_equipment()
        for spd in spds:
            spd._validate_spd()

        equip = equipment
        warnings: List[str] = []
        details: List[str] = []

        if "reflection_coefficient_kr" not in equip.model_fields_set:
            warnings.append(
                "reflection_coefficient_kr not specified; using worst-case default k_r = 2.0 "
                "per IEC 62305-4:2024 Clause C.2.3.2."
            )

        types = [s.spd_class for s in spds]
        has_type1 = "Type 1" in types
        has_type2 = "Type 2" in types

        # Check 1: Boundary protection presence
        if not has_type1:
            warnings.append("Missing Type 1 (Class I) SPD at main service entrance (LPZ 0 / 1)")
        else:
            details.append("Type 1 SPD installed at main service entrance boundary")

        if not has_type2:
            warnings.append("Missing Type 2 (Class II) SPD at sub-distribution boards (LPZ 1 / 2)")
        else:
            details.append("Type 2 SPD installed at secondary power distribution board")

        # Check 2: Inductive decoupling distance between Type 1 and Type 2 (kept unchanged per Step 2.6)
        type1_entries = [s for s in spds if s.spd_class == "Type 1"]
        energy_coordinated = True
        for t1 in type1_entries:
            if t1.technology == "spark_gap":
                assert t1.cable_length_to_downstream_m is not None
                if t1.cable_length_to_downstream_m < 10.0:
                    warnings.append(
                        f"Cable length between Type 1 spark gap and downstream SPD ({t1.cable_length_to_downstream_m}m) is less than 10m. "
                        "Risk of premature MOV destruction before spark-gap fires without decoupling inductor."
                    )
                    energy_coordinated = False
                else:
                    details.append(
                        f"Decoupling length ({t1.cable_length_to_downstream_m}m) satisfies energy coordination criteria"
                    )
            else:
                if t1.cable_length_to_downstream_m is not None:
                    details.append(
                        f"Decoupling length ({t1.cable_length_to_downstream_m}m) satisfies energy coordination criteria"
                    )
                else:
                    details.append(
                        f"Type 1 {t1.technology} SPD '{t1.id}' satisfies energy coordination criteria"
                    )

        # Check 3: Rule 1 (U_p <= 0.5 * U_w) on Type 1 SPDs — conservative screening bound (C.2.3.1.4)
        rule1_limit_kv = _RULE1_UW_FACTOR * equip.uw_kv
        type1_rule1_ok = True
        for t1 in type1_entries:
            if not self.check_rule1_up(t1.up_kv, equip.uw_kv):
                type1_rule1_ok = False
                warnings.append(
                    f"Type 1 SPD '{t1.id}' U_p ({t1.up_kv:.3f} kV) exceeds Rule 1 limit "
                    f"0.5 * U_w ({rule1_limit_kv:.3f} kV) for {equip.category} (U_w={equip.uw_kv:.3f} kV)."
                )

        # Check 4: Equipment-side SPD stage (smallest-U_p Type 2 or Type 3 SPD per Section 4.3)
        u_req_kv = self.calculate_required_upf_c1(
            equip.uw_kv,
            equip.induced_voltage_kv,
            equip.reflection_coefficient_kr,
        )
        equip_stage_candidates = [s for s in spds if s.spd_class in ("Type 2", "Type 3")]

        if not equip_stage_candidates:
            voltage_ok = False
            l_max_rounded = 0.0
            warnings.append(
                f"No Type 2 or Type 3 equipment-side SPD present; equipment protection not verified "
                f"(U_w={equip.uw_kv:.3f} kV, U_i={equip.induced_voltage_kv:.3f} kV, "
                f"k_r={equip.reflection_coefficient_kr:.3f}, U_req={u_req_kv:.3f} kV, L_max=0.000 m)."
            )
            details.append(
                f"IEC 62305-4:2024 C.2.3: equipment-side SPD=None, U_w={equip.uw_kv:.3f} kV, "
                f"U_i={equip.induced_voltage_kv:.3f} kV, k_r={equip.reflection_coefficient_kr:.3f}, "
                f"U_req={u_req_kv:.3f} kV, L_max=0.000 m"
            )
        else:
            equip_spd = min(equip_stage_candidates, key=lambda s: s.up_kv)
            if equip_spd.lead_length_m is None:
                lead_len_m = _DEFAULT_CONNECTING_LEAD_M
                warnings.append(
                    f"SPD '{equip_spd.id}' lead_length_m not specified; assuming "
                    f"{_DEFAULT_CONNECTING_LEAD_M} m design limit per IEC 62305-4:2024 Clause C.2.5."
                )
                details.append(
                    f"Assumed connecting lead length lead_length_m = {_DEFAULT_CONNECTING_LEAD_M} m "
                    f"for equipment-side SPD '{equip_spd.id}' (IEC 62305-4:2024 Clause C.2.5)."
                )
            else:
                lead_len_m = float(equip_spd.lead_length_m)

            i_spd_ka = self.get_spd_test_current_ka(equip_spd)
            delta_u_kv = self.calculate_lead_voltage_drop_c4(i_spd_ka, lead_len_m)
            up_f_kv = self.calculate_effective_protection_level_upf(
                equip_spd.up_kv,
                delta_u_kv,
                equip_spd.technology,
            )

            equip_rule1_ok = self.check_rule1_up(equip_spd.up_kv, equip.uw_kv)
            c1_ok = up_f_kv <= u_req_kv
            c5_ok = self.check_oscillation_c5(up_f_kv, equip.uw_kv)
            raw_l_max_m = self.calculate_max_connecting_lead_length_m(
                up_kv=equip_spd.up_kv,
                i_spd_ka=i_spd_ka,
                technology=equip_spd.technology,
                u_req_kv=u_req_kv,
            )

            numerator_positive = raw_l_max_m > 0.0
            voltage_ok = (
                type1_rule1_ok
                and equip_rule1_ok
                and numerator_positive
                and c1_ok
                and c5_ok
            )

            if not equip_rule1_ok:
                warnings.append(
                    f"Equipment-side SPD '{equip_spd.id}' U_p ({equip_spd.up_kv:.3f} kV) exceeds "
                    f"Rule 1 limit 0.5 * U_w ({rule1_limit_kv:.3f} kV)."
                )

            if not voltage_ok:
                l_max_rounded = 0.0
                warnings.append(
                    f"IEC 62305-4:2024 Annex C.2.3 voltage coordination failed for SPD '{equip_spd.id}': "
                    f"U_w={equip.uw_kv:.3f} kV, U_i={equip.induced_voltage_kv:.3f} kV, "
                    f"k_r={equip.reflection_coefficient_kr:.3f}, U_req={u_req_kv:.3f} kV, "
                    f"U_p={equip_spd.up_kv:.3f} kV, I_SPD={i_spd_ka:.3f} kA, "
                    f"lead_length={lead_len_m:.3f} m, ΔU={delta_u_kv:.3f} kV, "
                    f"U_p/f={up_f_kv:.3f} kV, L_max=0.000 m."
                )
            else:
                l_max_rounded = round(raw_l_max_m, 3)
                details.append(
                    f"Voltage protection verified: U_p/f ({up_f_kv:.3f} kV) <= U_req ({u_req_kv:.3f} kV) "
                    f"and Rule 1 U_p <= 0.5 * U_w ({rule1_limit_kv:.3f} kV)"
                )

            details.append(
                f"IEC 62305-4:2024 C.2.3 ({equip_spd.id}): "
                f"U_w={equip.uw_kv:.3f} kV, U_i={equip.induced_voltage_kv:.3f} kV, "
                f"k_r={equip.reflection_coefficient_kr:.3f}, U_p={equip_spd.up_kv:.3f} kV, "
                f"I_SPD={i_spd_ka:.3f} kA, lead_length={lead_len_m:.3f} m, "
                f"U_req={u_req_kv:.3f} kV, L_max={l_max_rounded:.3f} m"
            )

        is_coordinated = has_type1 and has_type2 and energy_coordinated and voltage_ok
        status = (
            "COORDINATED"
            if is_coordinated
            else ("ACTION_REQUIRED" if has_type1 else "NON_COMPLIANT")
        )

        return SPDCoordinationAssessment(
            spds=spds,
            equipment=equip,
            energy_coordination_verified=energy_coordinated,
            voltage_protection_verified=voltage_ok,
            max_connecting_lead_length_m=l_max_rounded,
            status=status,
            warnings=warnings,
            coordination_details=details,
        )
