import math
from typing import Any, List, Optional, Tuple
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
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")

    separation_to_lps_m: float
    lps_class: str
    down_conductor_length_l_m: float
    insulation_medium: str  # validated against StandardsRepository km keys
    # IEC 62305-3:2024 Clause 6.3, Table 13 per-configuration kc selection:
    down_conductor_count: Optional[int] = None
    earth_resistances_within_factor_2: Optional[bool] = None

    @field_validator("down_conductor_length_l_m", mode="before")
    @classmethod
    def _validate_positive_lengths(cls, v: Any, info) -> float:
        return _check_positive_finite_float(info.field_name, v)

    @field_validator("separation_to_lps_m", mode="before")
    @classmethod
    def _validate_separation(cls, v: Any) -> float:
        return _check_nonnegative_finite_float("separation_to_lps_m", v)

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

    @field_validator("down_conductor_count", mode="before")
    @classmethod
    def _validate_down_conductor_count(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(
                f"down_conductor_count must be a strict int >= 1, not bool; got {v!r}."
            )
        if v < 1:
            raise ValueError(f"down_conductor_count must be >= 1, got {v!r}.")
        return v

    @field_validator("earth_resistances_within_factor_2", mode="before")
    @classmethod
    def _validate_earth_resistances_within_factor_2(cls, v: Any) -> Optional[bool]:
        if v is None:
            return None
        if not isinstance(v, bool):
            raise ValueError(
                f"earth_resistances_within_factor_2 must be a strict boolean or None, got {v!r}."
            )
        return v


class PVClearanceResult(BaseModel):
    required_separation_s_m: float
    actual_clearance_m: float
    kc_used: float
    kc_basis: str
    is_isolated_lps_sufficient: bool
    requires_equipotential_bonding: bool
    loop_area_risk: str
    status: str
    engineering_recommendations: List[str] = Field(default_factory=list)


class PVEngineeringModule:
    """
    Advanced PV Rooftop Engineering Module (IEC 62305-3:2024 Clause 6.3, Table 11–13).

    Evaluates:
    - Separation distance s = (k_i / k_m) * k_c * l to metallic solar module support frameworks
    - Direct flashover hazard vs. isolated LPS requirements
    - Inductive surge loop area minimization rules for DC string cabling
    """

    def __init__(self, standards_repo: Optional[StandardsRepository] = None):
        self.standards_repo = standards_repo or _get_standards_repo()

    def _require_parameter(self, param_id: str) -> float:
        param = self.standards_repo.get_parameter(STANDARD_KEY, param_id)
        if param is None:
            raise ValueError(
                f"Missing parameter {param_id!r} in StandardsRepository for {STANDARD_KEY!r}."
            )
        return float(param.value)

    def _resolve_ki(self, lps_class: str) -> float:
        if not isinstance(lps_class, str) or lps_class not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        if lps_class == "I":
            return self._require_parameter("ki_class_I")
        if lps_class == "II":
            return self._require_parameter("ki_class_II")
        return self._require_parameter("ki_class_III_IV")

    def _resolve_km(self, medium: str) -> float:
        if not isinstance(medium, str) or medium not in _VALID_INSULATION_MEDIA:
            raise ValueError(
                f"Unknown insulation_medium {medium!r}; expected one of {_VALID_INSULATION_MEDIA}."
            )
        return self._require_parameter(f"km_{medium}")

    def _resolve_kc(self, pv: PVArraySpecification) -> Tuple[float, str]:
        n = pv.down_conductor_count
        within_factor_2 = pv.earth_resistances_within_factor_2
        if n is None or within_factor_2 is None or within_factor_2 is False:
            return (
                self._require_parameter("kc_earth_resistance_fallback"),
                "IEC 62305-3:2024 Table 13 fallback (kc=1.0)",
            )
        if n == 1:
            return (
                self._require_parameter("kc_n_1_isolated"),
                "IEC 62305-3:2024 Table 13 (n=1, isolated LPS)",
            )
        if n == 2:
            return (
                self._require_parameter("kc_n_2"),
                "IEC 62305-3:2024 Table 13 (n=2)",
            )
        return (
            self._require_parameter("kc_n_3_or_more"),
            f"IEC 62305-3:2024 Table 13 (n={n}, 3 and more)",
        )

    def evaluate_pv_installation(self, pv: PVArraySpecification) -> PVClearanceResult:
        sep_m = _check_nonnegative_finite_float(
            "separation_to_lps_m", pv.separation_to_lps_m
        )
        l_m = _check_positive_finite_float(
            "down_conductor_length_l_m", pv.down_conductor_length_l_m
        )
        if pv.down_conductor_count is not None:
            if (
                isinstance(pv.down_conductor_count, bool)
                or not isinstance(pv.down_conductor_count, int)
                or pv.down_conductor_count < 1
            ):
                raise ValueError(
                    f"down_conductor_count must be a strict int >= 1, not bool; got {pv.down_conductor_count!r}."
                )
        if pv.earth_resistances_within_factor_2 is not None and not isinstance(
            pv.earth_resistances_within_factor_2, bool
        ):
            raise ValueError(
                "earth_resistances_within_factor_2 must be a strict boolean or None, "
                f"got {pv.earth_resistances_within_factor_2!r}."
            )

        ki = self._resolve_ki(pv.lps_class)
        km = self._resolve_km(pv.insulation_medium)
        kc, kc_basis = self._resolve_kc(pv)

        # IEC 62305-3:2024 Clause 6.3.2 Eq. (6): s = (ki / km) * kc * l
        s_req = float((ki / km) * kc * l_m)
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

        recommendations.append(
            "Route DC+ and DC- string cables in direct physical contact to minimize inductive loop area."
        )

        return PVClearanceResult(
            required_separation_s_m=round(s_req, 3),
            actual_clearance_m=round(sep_m, 3),
            kc_used=kc,
            kc_basis=kc_basis,
            is_isolated_lps_sufficient=is_isolated,
            requires_equipotential_bonding=requires_bonding_to_lps,
            loop_area_risk="LOW" if is_isolated else "HIGH",
            status="ISOLATED_PASS" if is_isolated else "BONDING_MANDATORY",
            engineering_recommendations=recommendations,
        )
