import math
import numpy as np
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aegislps_engine.risk_factors import (
    loss,
    map_fire_risk_rf,
    p_b,
    p_lps,
    p_s,
    p_spd,
    r_f,
    r_p,
)

_VALID_INPUT_LPS_CLASSES = ("none", "I", "II", "III", "IV")


def _validate_risk_inputs(inputs: "RiskAssessmentInput") -> None:
    for name in (
        "structure_length_m",
        "structure_width_m",
        "structure_height_m",
        "ng_flashes_per_km2_year",
        "environmental_cd",
    ):
        val = getattr(inputs, name)
        if isinstance(val, bool) or not math.isfinite(val) or val <= 0.0:
            raise ValueError(f"{name} must be finite and > 0, got {val!r}.")

    hrs = inputs.time_in_structure_hours_per_year
    if isinstance(hrs, bool) or not math.isfinite(hrs) or hrs < 0.0 or hrs > 8760.0:
        raise ValueError(
            f"time_in_structure_hours_per_year must be finite and in [0, 8760], got {hrs!r}."
        )

    if isinstance(inputs.number_of_occupants, bool) or inputs.number_of_occupants < 0:
        raise ValueError(
            f"number_of_occupants must be >= 0, got {inputs.number_of_occupants!r}."
        )

    if not isinstance(inputs.lps_class, str) or inputs.lps_class not in _VALID_INPUT_LPS_CLASSES:
        raise ValueError(
            f"lps_class must be one of {_VALID_INPUT_LPS_CLASSES}, got {inputs.lps_class!r}."
        )

    p_s(inputs.structure_type)
    p_lps(inputs.lps_class, inputs.protection_variant)
    r_p(inputs.provisions)

    if inputs.fire_risk_level is None and inputs.fire_risk_rf is None:
        raise ValueError(
            "Either fire_risk_level or fire_risk_rf must be provided (IEC 62305-2:2024 Table B.6)."
        )
    if inputs.fire_risk_level is not None and inputs.fire_risk_rf is not None:
        rf_from_level = r_f(inputs.fire_risk_level)
        mapped_level = map_fire_risk_rf(inputs.fire_risk_rf)
        if rf_from_level != r_f(mapped_level):
            raise ValueError(
                f"Conflicting fire_risk_level={inputs.fire_risk_level!r} and fire_risk_rf={inputs.fire_risk_rf!r}."
            )
    elif inputs.fire_risk_level is not None:
        r_f(inputs.fire_risk_level)
    else:
        assert inputs.fire_risk_rf is not None
        map_fire_risk_rf(inputs.fire_risk_rf)

    p_spd(
        inputs.lps_class,
        inputs.has_coordinated_spd,
        inputs.has_coordinated_spd,
        source="S1",
    )
    loss(inputs.loss_category)


class RiskAssessmentInput(BaseModel):
    """Input model for IEC 62305-2:2024 R1 risk assessment.

    Parameters
    ----------
    structure_type : {"wood_masonry", "continuous_rc_or_metal_framework"}
        Structure construction category for ``P_S`` (Table B.4 NOTE 1, p. 57, default ``"wood_masonry"``).
    protection_variant : {"standard", "framework_natural_downconductor", "metal_roof_full_protection"}
        LPS variant for ``P_LPS`` (Table B.3, p. 56, default ``"standard"``; special variants require ``lps_class="I"``).
    provisions : {"none", "passive_or_manual", "automatic"}
        Fire-mitigation provisions for ``r_p`` in ``P_B`` (Table B.5 NOTE, p. 58, default ``"none"``).
    loss_category : {"very_high", "high", "normal", "low"}
        Required Table C.2 structure/risk-zone loss category (upper-bound default rule, Clause C.2).
    fire_risk_rf : float, optional
        Legacy numeric fire-risk factor mapped strictly to Table B.6 (``1, 1e-1, 1e-2, 1e-3, 0``).
        Either ``fire_risk_level`` or ``fire_risk_rf`` must be explicitly provided.
    fire_risk_level : str, optional
        Explicit Table B.6 fire/explosion level (required for ``explosion_zone_1_21`` and ``explosion_zone_2_22``).
    has_automatic_fire_system : bool
        Unused legacy field retained for public API compatibility; fire provisions enter solely via ``provisions`` (``r_p`` in ``P_B``).
    number_of_occupants : int
        Unused in current R1 component formulas; retained for schema compatibility.
    time_in_structure_hours_per_year : float
        Annual presence hours ``t_z`` in ``[0, 8760]`` (IEC 62305-2:2024 Clause B.11, Eq. B.14, NOTE 1, p. 70: default ``8760.0``).
    """

    model_config = ConfigDict(allow_inf_nan=False)

    structure_length_m: float
    structure_width_m: float
    structure_height_m: float
    ng_flashes_per_km2_year: float  # Ground flash density Ng (> 0)
    environmental_cd: float  # Location factor C_D (> 0; e.g. 1.0 isolated, 0.5 suburban, 0.25 urban)
    lps_class: str  # Required: one of {"none", "I", "II", "III", "IV"}
    structure_type: str = "wood_masonry"  # IEC 62305-2:2024 Table B.4 NOTE 1 (p. 57)
    protection_variant: str = "standard"  # IEC 62305-2:2024 Table B.3 (p. 56)
    provisions: str = "none"  # IEC 62305-2:2024 Table B.5 NOTE (p. 58)
    loss_category: str
    fire_risk_rf: Optional[float] = None
    fire_risk_level: Optional[str] = None
    has_automatic_fire_system: bool = True  # Unused legacy field; provisions enters via r_p in P_B only
    has_coordinated_spd: bool  # Required: coordinated SPD system installed
    number_of_occupants: int = 100  # Unused in current R1 component formulas; retained for schema compatibility
    time_in_structure_hours_per_year: float = 8760.0  # IEC 62305-2:2024 Clause B.11 Eq. (B.14) NOTE 1 (p. 70): t_z / 8760 = 1 when unknown

    @field_validator(
        "structure_length_m",
        "structure_width_m",
        "structure_height_m",
        "ng_flashes_per_km2_year",
        "environmental_cd",
        "fire_risk_rf",
        "number_of_occupants",
        "time_in_structure_hours_per_year",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric risk input.")
        return v

    @field_validator("has_automatic_fire_system", "has_coordinated_spd", mode="before")
    @classmethod
    def _require_strict_bool(cls, v):
        if not isinstance(v, bool):
            raise ValueError(f"Expected boolean value, got {v!r}.")
        return v

    @model_validator(mode="after")
    def _validate_all(self) -> "RiskAssessmentInput":
        _validate_risk_inputs(self)
        return self


class RiskAssessmentResult(BaseModel):
    collection_area_ad_m2: float
    annual_strikes_nd: float
    risk_ra_touch_step: float  # Risk due to touch and step potential
    risk_rb_physical_damage: float  # Risk due to physical fire/destruction
    risk_rc_internal_systems: float  # Risk due to electronic overvoltage surges
    risk_r1_loss_of_life: float  # Total R1 risk
    tolerable_risk_rt: float = 1e-5  # Tolerable threshold for loss of human life
    risk_acceptable: bool
    status: str
    mitigation_recommendations: List[str] = Field(default_factory=list)


class RiskManagementEngine:
    """
    IEC 62305-2:2024 Risk Assessment Engine (direct-strike R1 components).

    Implements:
    - Equivalent collection area calculation A_d
    - Annual frequency of direct dangerous events N_D
    - Loss of human life (R1) direct-strike component breakdown:
      R_1 = R_A + R_B + R_C
      where:
      - R_A = N_D * P_A * L_A
      - R_B = N_D * P_B * L_B  with P_B = P_S * P_LPS * r_p * r_f (Eq. B.4)
      - R_C = N_D * P_C * L_C  with P_SPD from Table B.7 (source S1)
      and L_F1, L_O1 from Table C.2 (upper-bound rule, Clause C.2) scaled by t_occupancy.
    - Quantitative evaluation against tolerable risk threshold R_T = 1.0 x 10^-5
    """

    def evaluate_r1_risk(self, inputs: RiskAssessmentInput) -> RiskAssessmentResult:
        _validate_risk_inputs(inputs)

        l, w, h = (
            inputs.structure_length_m,
            inputs.structure_width_m,
            inputs.structure_height_m,
        )

        # IEC 62305-2 collection area A_D = L*W + 2*(3*H)*(L+W) + pi*(3*H)^2
        ad = (l * w) + 6.0 * h * (l + w) + 9.0 * np.pi * (h ** 2)

        # Expected direct strikes per year N_D = N_g * A_D * C_D * 10^-6
        nd = inputs.ng_flashes_per_km2_year * ad * inputs.environmental_cd * 1e-6

        # P_A kept unchanged per Step 2.5 scope
        p_a = (
            0.01
            if inputs.lps_class == "I"
            else (0.05 if inputs.lps_class in ["II", "III", "IV"] else 1.0)
        )

        # Shared IEC 62305-2:2024 factors from risk_factors.py
        assert inputs.fire_risk_level is not None or inputs.fire_risk_rf is not None
        fire_level = (
            inputs.fire_risk_level
            if inputs.fire_risk_level is not None
            else map_fire_risk_rf(inputs.fire_risk_rf)  # type: ignore[arg-type]
        )
        pb_val = p_b(
            lps_class=inputs.lps_class,
            fire_risk_level=fire_level,
            structure_type=inputs.structure_type,
            protection_variant=inputs.protection_variant,
            provisions=inputs.provisions,
        )
        pspd_s1 = p_spd(
            lps_class=inputs.lps_class,
            spd_present=inputs.has_coordinated_spd,
            spd_coordinated=inputs.has_coordinated_spd,
            source="S1",
        )

        loss_vals = loss(inputs.loss_category)
        t_occupancy = inputs.time_in_structure_hours_per_year / 8760.0
        l_t = 1e-2 * t_occupancy  # L_T kept unchanged per Step 2.5 scope
        l_f = loss_vals.l_f1 * t_occupancy
        l_o = loss_vals.l_o1 * t_occupancy

        # Risk components
        r_a = float(nd * p_a * l_t)
        r_b = float(nd * pb_val * l_f)
        r_c = float(nd * pspd_s1 * l_o)

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
            mitigation_recommendations=mitigations,
        )
