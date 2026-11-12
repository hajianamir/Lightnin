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

_VALID_SERVICE_TYPES = ("aerial_power", "buried_power", "telecom")
_VALID_INPUT_LPS_CLASSES = ("none", "I", "II", "III", "IV")


class IncomingServiceLine(BaseModel):
    """Incoming HV/LV power or telecom service line specification.

    ``line_length_m`` defaults to ``1000.0`` m (1 km) per IEC 62305-2:2024
    Clause A.4 (p. 50) when section length information is not available.
    """

    model_config = ConfigDict(allow_inf_nan=False)

    id: str = "power-line-1"
    service_type: str = "aerial_power"  # aerial_power, buried_power, telecom
    line_length_m: float = 1000.0  # IEC 62305-2:2024 Clause A.4 (p. 50): assume L_L = 1000 m (1 km) when unknown
    transformer_present: bool = True
    shielded: bool = False

    @field_validator("line_length_m", mode="before")
    @classmethod
    def _reject_bool_length(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for line_length_m.")
        return v

    @field_validator("transformer_present", "shielded", mode="before")
    @classmethod
    def _require_strict_bool(cls, v):
        if not isinstance(v, bool):
            raise ValueError(f"Expected boolean value, got {v!r}.")
        return v

    @model_validator(mode="after")
    def _validate_line(self) -> "IncomingServiceLine":
        if not isinstance(self.service_type, str) or self.service_type not in _VALID_SERVICE_TYPES:
            raise ValueError(
                f"Unknown service_type {self.service_type!r}; expected one of {_VALID_SERVICE_TYPES}."
            )
        if not math.isfinite(self.line_length_m) or self.line_length_m <= 0.0:
            raise ValueError(
                f"line_length_m must be finite and > 0, got {self.line_length_m!r}."
            )
        return self


def _validate_comprehensive_inputs(inp: "ComprehensiveRiskInput") -> None:
    for name in (
        "structure_length_m",
        "structure_width_m",
        "structure_height_m",
        "ng_flashes_per_km2_year",
        "environmental_cd",
    ):
        val = getattr(inp, name)
        if isinstance(val, bool) or not math.isfinite(val) or val <= 0.0:
            raise ValueError(f"{name} must be finite and > 0, got {val!r}.")

    hrs = inp.time_in_structure_hours_per_year
    if isinstance(hrs, bool) or not math.isfinite(hrs) or hrs < 0.0 or hrs > 8760.0:
        raise ValueError(
            f"time_in_structure_hours_per_year must be finite and in [0, 8760], got {hrs!r}."
        )

    if isinstance(inp.occupants_count, bool) or inp.occupants_count < 0:
        raise ValueError(f"occupants_count must be >= 0, got {inp.occupants_count!r}.")

    for line in inp.incoming_lines:
        if not isinstance(line.service_type, str) or line.service_type not in _VALID_SERVICE_TYPES:
            raise ValueError(
                f"Unknown service_type {line.service_type!r}; expected one of {_VALID_SERVICE_TYPES}."
            )
        if (
            isinstance(line.line_length_m, bool)
            or not math.isfinite(line.line_length_m)
            or line.line_length_m <= 0.0
        ):
            raise ValueError(
                f"line_length_m must be finite and > 0, got {line.line_length_m!r}."
            )

    if not isinstance(inp.lps_class, str) or inp.lps_class not in _VALID_INPUT_LPS_CLASSES:
        raise ValueError(
            f"lps_class must be one of {_VALID_INPUT_LPS_CLASSES}, got {inp.lps_class!r}."
        )

    p_s(inp.structure_type)
    p_lps(inp.lps_class, inp.protection_variant)
    r_p(inp.provisions)

    if inp.fire_risk_level is None and inp.fire_risk_rf is None:
        raise ValueError(
            "Either fire_risk_level or fire_risk_rf must be provided (IEC 62305-2:2024 Table B.6)."
        )
    if inp.fire_risk_level is not None and inp.fire_risk_rf is not None:
        rf_from_level = r_f(inp.fire_risk_level)
        mapped_level = map_fire_risk_rf(inp.fire_risk_rf)
        if rf_from_level != r_f(mapped_level):
            raise ValueError(
                f"Conflicting fire_risk_level={inp.fire_risk_level!r} and fire_risk_rf={inp.fire_risk_rf!r}."
            )
    elif inp.fire_risk_level is not None:
        r_f(inp.fire_risk_level)
    else:
        assert inp.fire_risk_rf is not None
        map_fire_risk_rf(inp.fire_risk_rf)

    for src in ("S1", "S2", "S3", "S4"):
        p_spd(inp.lps_class, inp.has_coordinated_spd, inp.has_coordinated_spd, source=src)
    loss(inp.loss_category)


class ComprehensiveRiskInput(BaseModel):
    """Input model for full 8-component IEC 62305-2:2024 risk assessment.

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
    occupants_count : int
        Unused in current R1 component formulas; retained for schema compatibility.
    time_in_structure_hours_per_year : float
        Annual occupancy hours ``t_z`` in ``[0, 8760]`` for ``t_occ = hours / 8760`` (Clause B.11, Eq. B.14, NOTE 1, p. 70, default ``8760.0``).
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
    has_coordinated_spd: bool
    has_tws_early_warning: bool  # Thunderstorm Warning System (C_TWS)
    incoming_lines: List[IncomingServiceLine] = Field(default_factory=list)
    fire_risk_rf: Optional[float] = None
    fire_risk_level: Optional[str] = None
    occupants_count: int = 120  # Unused in current R1 component formulas; retained for schema compatibility
    time_in_structure_hours_per_year: float = 8760.0  # IEC 62305-2:2024 Clause B.11 Eq. (B.14) NOTE 1 (p. 70): t_z / 8760 = 1 when unknown

    @field_validator(
        "structure_length_m",
        "structure_width_m",
        "structure_height_m",
        "ng_flashes_per_km2_year",
        "environmental_cd",
        "fire_risk_rf",
        "occupants_count",
        "time_in_structure_hours_per_year",
        mode="before",
    )
    @classmethod
    def _reject_bool_for_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric risk input.")
        return v

    @field_validator("has_coordinated_spd", "has_tws_early_warning", mode="before")
    @classmethod
    def _require_strict_bool(cls, v):
        if not isinstance(v, bool):
            raise ValueError(f"Expected boolean value, got {v!r}.")
        return v

    @model_validator(mode="after")
    def _validate_all(self) -> "ComprehensiveRiskInput":
        _validate_comprehensive_inputs(self)
        return self


class Risk8Components(BaseModel):
    r_a_touch_step: float
    r_b_physical_damage: float
    r_c_internal_surges: float
    r_m_magnetic_pulse: float
    r_u_touch_voltage_service: float
    r_v_physical_damage_service: float
    r_w_internal_surges_service: float
    r_z_incoming_telecom: float
    total_risk_r1: float
    tolerable_risk_rt: float = 1e-5
    is_r1_acceptable: bool


class ComprehensiveRiskResult(BaseModel):
    collection_area_ad_structure_m2: float
    collection_area_al_services_m2: float
    annual_strikes_nd_direct: float
    annual_strikes_nl_services: float
    risk_components: Risk8Components
    status: str
    mitigations_required: List[str] = Field(default_factory=list)


class ComprehensiveRisk2024Engine:
    """
    Full IEC 62305-2:2024 Multi-Component Risk Management Engine.

    Implements all 8 risk components:
    - Direct strikes to structure: R_A, R_B, R_C
    - Strikes near structure: R_M
    - Direct strikes to incoming service lines: R_U, R_V, R_W
    - Strikes near incoming service lines: R_Z
    - Shared Annex B / Annex C factors via ``risk_factors.py`` (Tables B.3–B.7, C.2).
    """

    def evaluate_risk(self, inp: ComprehensiveRiskInput) -> ComprehensiveRiskResult:
        _validate_comprehensive_inputs(inp)

        l, w, h = inp.structure_length_m, inp.structure_width_m, inp.structure_height_m

        # Structure Collection Area Ad
        ad = (l * w) + 6.0 * h * (l + w) + 9.0 * np.pi * (h ** 2)
        nd = inp.ng_flashes_per_km2_year * ad * inp.environmental_cd * 1e-6

        # Incoming Lines Collection Area Al
        al_total = 0.0
        for line in inp.incoming_lines:
            width_factor = 40.0 if line.service_type == "aerial_power" else 8.0
            al_total += width_factor * line.line_length_m

        nl = inp.ng_flashes_per_km2_year * al_total * inp.environmental_cd * 1e-6

        # P_A kept unchanged per Step 2.5 scope
        p_a = (
            0.01
            if inp.lps_class == "I"
            else (0.05 if inp.lps_class in ["II", "III", "IV"] else 1.0)
        )

        # Shared IEC 62305-2:2024 factors from risk_factors.py
        assert inp.fire_risk_level is not None or inp.fire_risk_rf is not None
        fire_level = (
            inp.fire_risk_level
            if inp.fire_risk_level is not None
            else map_fire_risk_rf(inp.fire_risk_rf)  # type: ignore[arg-type]
        )
        pb_val = p_b(
            lps_class=inp.lps_class,
            fire_risk_level=fire_level,
            structure_type=inp.structure_type,
            protection_variant=inp.protection_variant,
            provisions=inp.provisions,
        )
        pspd_s1 = p_spd(
            lps_class=inp.lps_class,
            spd_present=inp.has_coordinated_spd,
            spd_coordinated=inp.has_coordinated_spd,
            source="S1",
        )
        pspd_s2 = p_spd(
            lps_class=inp.lps_class,
            spd_present=inp.has_coordinated_spd,
            spd_coordinated=inp.has_coordinated_spd,
            source="S2",
        )
        pspd_s3 = p_spd(
            lps_class=inp.lps_class,
            spd_present=inp.has_coordinated_spd,
            spd_coordinated=inp.has_coordinated_spd,
            source="S3",
        )
        pspd_s4 = p_spd(
            lps_class=inp.lps_class,
            spd_present=inp.has_coordinated_spd,
            spd_coordinated=inp.has_coordinated_spd,
            source="S4",
        )

        # C_TWS Thunderstorm Warning System factor (kept unchanged per Step 2.5 scope)
        c_tws = 0.2 if inp.has_tws_early_warning else 1.0
        t_occupancy = inp.time_in_structure_hours_per_year / 8760.0
        loss_vals = loss(inp.loss_category)

        # Consequence loss fractions
        l_a = 1e-2 * c_tws
        l_b = loss_vals.l_f1 * t_occupancy
        l_c = loss_vals.l_o1 * t_occupancy

        # Compute all 8 components (other R_M/R_U/R_V/R_W/R_Z constants kept unchanged per Step 2.5 scope)
        r_a = float(nd * p_a * l_a)
        r_b = float(nd * pb_val * l_b)
        r_c = float(nd * pspd_s1 * l_c)
        r_m = float(nd * 0.1 * pspd_s2 * l_c)

        r_u = float(nl * p_a * l_a * 0.5)
        r_v = float(nl * pb_val * l_b * 0.5)
        r_w = float(nl * pspd_s3 * l_c * 0.5)
        r_z = float(nl * 0.2 * pspd_s4 * l_c * 0.5)

        total_r1 = float(r_a + r_b + r_c + r_m + r_u + r_v + r_w + r_z)
        rt = 1e-5
        acceptable = total_r1 <= rt

        mitigations = []
        if not acceptable:
            if (r_b + r_v) > 0.4 * rt:
                mitigations.append("Upgrade structural LPS to Class I and install automated extinguishing systems.")
            if (r_c + r_w + r_m + r_z) > 0.4 * rt:
                mitigations.append("Install coordinated Type 1 + Type 2 SPDs at line entrance and distribution boards.")
            if (r_a + r_u) > 0.2 * rt:
                mitigations.append("Apply 5cm asphalt or gravel surface layer around down conductors.")

        comp = Risk8Components(
            r_a_touch_step=r_a,
            r_b_physical_damage=r_b,
            r_c_internal_surges=r_c,
            r_m_magnetic_pulse=r_m,
            r_u_touch_voltage_service=r_u,
            r_v_physical_damage_service=r_v,
            r_w_internal_surges_service=r_w,
            r_z_incoming_telecom=r_z,
            total_risk_r1=total_r1,
            tolerable_risk_rt=rt,
            is_r1_acceptable=acceptable,
        )

        return ComprehensiveRiskResult(
            collection_area_ad_structure_m2=round(float(ad), 1),
            collection_area_al_services_m2=round(float(al_total), 1),
            annual_strikes_nd_direct=float(nd),
            annual_strikes_nl_services=float(nl),
            risk_components=comp,
            status="ACCEPTABLE (R1 <= RT)" if acceptable else "NON_COMPLIANT (R1 > RT)",
            mitigations_required=mitigations,
        )
