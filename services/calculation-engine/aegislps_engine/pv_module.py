import math
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from aegislps_standards.repository import StandardsRepository

STANDARD_KEY = "IEC 62305-3:2024"
_VALID_LPS_CLASSES = ("I", "II", "III", "IV")
_VALID_INSULATION_MEDIA = ("air", "solid", "insulating_standoff")

_STANDARDS_REPO: Optional[StandardsRepository] = None


def _get_standards_repo() -> StandardsRepository:
    global _STANDARDS_REPO
    if _STANDARDS_REPO is None:
        _STANDARDS_REPO = StandardsRepository()
    return _STANDARDS_REPO


def _check_finite_float(name: str, v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name} must be a finite number, not bool; got {v!r}.")
    val = float(v)
    if not math.isfinite(val):
        raise ValueError(f"{name} must be finite, got {v!r}.")
    return val


def _check_positive_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val <= 0.0:
        raise ValueError(f"{name} must be > 0, got {v!r}.")
    return val


def _check_nonnegative_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val < 0.0:
        raise ValueError(f"{name} must be >= 0, got {v!r}.")
    return val


class PVArraySpecification(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str = "pv-array-1"
    tilt_angle_deg: float
    panel_count: int
    array_length_m: float
    array_width_m: float
    metallic_frame_bonded: bool = True  # unused in evaluate_pv_installation
    separation_to_lps_m: float
    lps_class: str
    down_conductor_length_l_m: float
    insulation_medium: str  # validated against StandardsRepository km keys

    @field_validator("tilt_angle_deg", mode="before")
    @classmethod
    def _validate_tilt(cls, v: Any) -> float:
        val = _check_finite_float("tilt_angle_deg", v)
        if val < 0.0 or val > 90.0:
            raise ValueError(
                f"tilt_angle_deg must satisfy 0 <= tilt_angle_deg <= 90, got {v!r}."
            )
        return val

    @field_validator("panel_count", mode="before")
    @classmethod
    def _validate_panel_count(cls, v: Any) -> int:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(
                f"panel_count must be a strict int >= 1, not bool; got {v!r}."
            )
        if v < 1:
            raise ValueError(f"panel_count must be >= 1, got {v!r}.")
        return v

    @field_validator(
        "array_length_m", "array_width_m", "down_conductor_length_l_m", mode="before"
    )
    @classmethod
    def _validate_positive_lengths(cls, v: Any, info) -> float:
        return _check_positive_finite_float(info.field_name, v)

    @field_validator("separation_to_lps_m", mode="before")
    @classmethod
    def _validate_separation(cls, v: Any) -> float:
        return _check_nonnegative_finite_float("separation_to_lps_m", v)

    @field_validator("metallic_frame_bonded", mode="before")
    @classmethod
    def _validate_bonded_bool(cls, v: Any) -> bool:
        if not isinstance(v, bool):
            raise ValueError(
                f"metallic_frame_bonded must be a strict boolean, got {v!r}."
            )
        return v

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        return v

    @field_validator("insulation_medium", mode="before")
    @classmethod
    def _validate_insulation_medium(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_INSULATION_MEDIA:
            raise ValueError(
                f"Unknown insulation_medium {v!r}; expected one of {_VALID_INSULATION_MEDIA}."
            )
        param = _get_standards_repo().get_parameter(STANDARD_KEY, f"km_{v}")
        if param is None:
            raise ValueError(
                f"Missing km parameter 'km_{v}' in StandardsRepository for {STANDARD_KEY!r}."
            )
        return v


class PVClearanceResult(BaseModel):
    required_separation_s_m: float
    actual_clearance_m: float
    is_isolated_lps_sufficient: bool
    requires_equipotential_bonding: bool
    loop_area_risk: str
    status: str
    engineering_recommendations: List[str] = Field(default_factory=list)


class PVEngineeringModule:
    """
    Advanced PV Rooftop Engineering Module (IEC 62305-3 Supplement 5 & CLC/TS 50539-12).

    Evaluates:
    - Separation distance s to metallic solar module support frameworks
    - Direct flashover hazard vs. isolated LPS requirements
    - Inductive surge loop area minimization rules for DC string cabling
    """

    def __init__(self, standards_repo: Optional[StandardsRepository] = None):
        self.standards_repo = standards_repo or _get_standards_repo()

    def _resolve_ki(self, lps_class: str) -> float:
        if not isinstance(lps_class, str) or lps_class not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        if lps_class == "I":
            param_id = "ki_class_I"
        elif lps_class == "II":
            param_id = "ki_class_II"
        else:
            param_id = "ki_class_III_IV"
        param = self.standards_repo.get_parameter(STANDARD_KEY, param_id)
        if param is None:
            raise ValueError(
                f"Missing parameter {param_id!r} in StandardsRepository for {STANDARD_KEY!r}."
            )
        return float(param.value)

    def _resolve_km(self, medium: str) -> float:
        if not isinstance(medium, str) or medium not in _VALID_INSULATION_MEDIA:
            raise ValueError(
                f"Unknown insulation_medium {medium!r}; expected one of {_VALID_INSULATION_MEDIA}."
            )
        param = self.standards_repo.get_parameter(STANDARD_KEY, f"km_{medium}")
        if param is None:
            raise ValueError(
                f"Missing parameter 'km_{medium}' in StandardsRepository for {STANDARD_KEY!r}."
            )
        return float(param.value)

    def evaluate_pv_installation(self, pv: PVArraySpecification) -> PVClearanceResult:
        tilt = _check_finite_float("tilt_angle_deg", pv.tilt_angle_deg)
        if tilt < 0.0 or tilt > 90.0:
            raise ValueError(
                f"tilt_angle_deg must satisfy 0 <= tilt_angle_deg <= 90, got {pv.tilt_angle_deg!r}."
            )
        if isinstance(pv.panel_count, bool) or not isinstance(pv.panel_count, int) or pv.panel_count < 1:
            raise ValueError(
                f"panel_count must be a strict int >= 1, not bool; got {pv.panel_count!r}."
            )
        _check_positive_finite_float("array_length_m", pv.array_length_m)
        _check_positive_finite_float("array_width_m", pv.array_width_m)
        sep_m = _check_nonnegative_finite_float("separation_to_lps_m", pv.separation_to_lps_m)
        l_m = _check_positive_finite_float(
            "down_conductor_length_l_m", pv.down_conductor_length_l_m
        )

        ki = self._resolve_ki(pv.lps_class)
        km = self._resolve_km(pv.insulation_medium)
        kc = 0.5  # Dual path down-conductor assumption

        # s = ki * (kc / km) * l
        s_req = float(ki * (kc / km) * l_m)
        is_isolated = sep_m >= s_req

        recommendations = []
        if is_isolated:
            recommendations.append(
                "Isolated LPS achieved: No direct lightning current will enter PV framework."
            )
            recommendations.append(
                "Bond module frames to local equipotential earthing bar with 6 mm2 Cu."
            )
            requires_bonding_to_lps = False
        else:
            recommendations.append(
                f"Separation distance violated (Actual: {sep_m:.2f}m < Req: {s_req:.2f}m). "
                "Must directly bond PV metallic frame to external LPS conductor using 16 mm2 Cu conductor."
            )
            recommendations.append(
                "Install Type 1 (Class I) DC SPDs at inverter DC inputs due to direct flashover risk."
            )
            requires_bonding_to_lps = True

        # Inductive loop area advisory
        recommendations.append(
            "Route DC+ and DC- string cables in direct physical contact to minimize inductive loop area."
        )

        return PVClearanceResult(
            required_separation_s_m=round(s_req, 3),
            actual_clearance_m=round(sep_m, 3),
            is_isolated_lps_sufficient=is_isolated,
            requires_equipotential_bonding=requires_bonding_to_lps,
            loop_area_risk="LOW" if is_isolated else "HIGH",
            status="ISOLATED_PASS" if is_isolated else "BONDING_MANDATORY",
            engineering_recommendations=recommendations,
        )
