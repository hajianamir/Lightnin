from enum import Enum
import math
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
import uuid

from aegislps_standards.repository import StandardsRepository

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")
# Allowed ConductorNode.node_type values already used across the codebase.
_VALID_NODE_TYPES = ("air_termination", "down_conductor", "earth_point", "bonding")
# Allowed ConductorSegment.material values (IEC 62305-3:2024 Table 6 / Table 7).
_VALID_CONDUCTOR_MATERIALS = ("copper", "aluminium", "steel")
# Allowed Building.roof_type values already used across the codebase (models.py / ProjectWizard.tsx).
_VALID_ROOF_TYPES = ("flat", "gable", "hip")
# Allowed SeparationPoint.insulation_medium keys mapped to StandardsRepository km_<medium>.
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


def _check_nonnegative_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val < 0.0:
        raise ValueError(f"{name} must be >= 0, got {v!r}.")
    return val


def _check_positive_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val <= 0.0:
        raise ValueError(f"{name} must be > 0, got {v!r}.")
    return val


class CalculationStatus(str, Enum):
    NOT_CALCULATED = "NOT_CALCULATED"
    CALCULATED = "CALCULATED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    UNVERIFIED = "UNVERIFIED"
    VERIFIED_AGAINST_REF = "VERIFIED_AGAINST_REF"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED_BY_INPUT = "INVALIDATED_BY_INPUT"
    INVALIDATED_BY_STANDARDS = "INVALIDATED_BY_STANDARDS"
    INVALIDATED_BY_ENGINE = "INVALIDATED_BY_ENGINE"


class ConductorNode(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    x: float
    y: float
    z: float
    # Validated in {"air_termination", "down_conductor", "earth_point", "bonding"}.
    node_type: str

    @field_validator("x", "y", mode="before")
    @classmethod
    def _validate_xy(cls, v: Any, info) -> float:
        return _check_finite_float(info.field_name, v)

    @field_validator("z", mode="before")
    @classmethod
    def _validate_z(cls, v: Any) -> float:
        return _check_nonnegative_finite_float("z", v)

    @field_validator("node_type", mode="before")
    @classmethod
    def _validate_node_type(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_NODE_TYPES:
            raise ValueError(
                f"Unknown node_type {v!r}; expected one of {_VALID_NODE_TYPES}."
            )
        return v


class ConductorSegment(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_node_id: str
    end_node_id: str
    # Validated in {"copper", "aluminium", "steel"}.
    material: str
    cross_section_mm2: float
    # Unused as an explicit kc input in SeparationDistanceEngine._resolve_kc.
    # Default 1.0 retained per IEC 62305-3:2024 Clause 6.3.2, Table 13 (docs/62305-3-2024.md):
    # "If the earth resistances of single earth electrodes differ by more than a
    # factor of 2, kc = 1 shall be assumed."
    kc_factor: float = 1.0

    @field_validator("material", mode="before")
    @classmethod
    def _validate_material(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_CONDUCTOR_MATERIALS:
            raise ValueError(
                f"Unknown conductor material {v!r}; expected one of {_VALID_CONDUCTOR_MATERIALS}."
            )
        return v

    @field_validator("cross_section_mm2", mode="before")
    @classmethod
    def _validate_cross_section(cls, v: Any) -> float:
        return _check_positive_finite_float("cross_section_mm2", v)

    @field_validator("kc_factor", mode="before")
    @classmethod
    def _validate_kc_factor(cls, v: Any) -> float:
        val = _check_positive_finite_float("kc_factor", v)
        if val > 1.0:
            raise ValueError(f"kc_factor must satisfy 0 < kc_factor <= 1.0, got {v!r}.")
        return val


class SeparationPoint(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    x: float
    y: float
    z: float
    associated_node_id: str
    # Validated against StandardsRepository km lookup ("air", "solid", "insulating_standoff").
    insulation_medium: str
    physical_distance_m: float
    route_length_to_bonding_m: Optional[float] = None

    @field_validator("x", "y", mode="before")
    @classmethod
    def _validate_xy(cls, v: Any, info) -> float:
        return _check_finite_float(info.field_name, v)

    @field_validator("z", mode="before")
    @classmethod
    def _validate_z(cls, v: Any) -> float:
        return _check_nonnegative_finite_float("z", v)

    @field_validator("insulation_medium", mode="before")
    @classmethod
    def _validate_insulation_medium(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_INSULATION_MEDIA:
            raise ValueError(
                f"Unknown insulation medium {v!r}. Expected one of {_VALID_INSULATION_MEDIA} "
                "(IEC 62305-3:2024 Table 12)."
            )
        param = _get_standards_repo().get_parameter("IEC 62305-3:2024", f"km_{v}")
        if param is None:
            raise ValueError(
                f"Missing km parameter 'km_{v}' in StandardsRepository for 'IEC 62305-3:2024'."
            )
        return v

    @field_validator("physical_distance_m", mode="before")
    @classmethod
    def _validate_physical_distance(cls, v: Any) -> float:
        return _check_nonnegative_finite_float("physical_distance_m", v)

    @field_validator("route_length_to_bonding_m", mode="before")
    @classmethod
    def _validate_route_length_to_bonding_m(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(
                "route_length_to_bonding_m must be a finite number > 0, not bool."
            )
        val = float(v)
        if not math.isfinite(val) or val <= 0.0:
            raise ValueError(
                f"route_length_to_bonding_m must be finite and > 0, got {v!r}."
            )
        return val


class Building(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    length_m: float
    width_m: float
    height_m: float
    # Validated in {"flat", "gable", "hip"}.
    roof_type: str

    @field_validator("length_m", "width_m", "height_m", mode="before")
    @classmethod
    def _validate_dimensions(cls, v: Any, info) -> float:
        return _check_positive_finite_float(info.field_name, v)

    @field_validator("roof_type", mode="before")
    @classmethod
    def _validate_roof_type(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_ROOF_TYPES:
            raise ValueError(
                f"Unknown roof_type {v!r}; expected one of {_VALID_ROOF_TYPES}."
            )
        return v


class SeparationCalculationResult(BaseModel):
    separation_point_id: str
    required_distance_s_m: float
    actual_distance_m: float
    pass_compliance: bool
    safety_margin_m: float
    lps_class: str
    ki_used: float
    kc_used: float
    km_used: float
    length_l_m: float
    formula_trace: str
    status: CalculationStatus = CalculationStatus.CALCULATED


class Project(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New AegisLPS Project"
    lps_class: str
    down_conductor_count: Optional[int] = None
    earth_resistances_within_factor_2: Optional[bool] = None
    building: Building
    nodes: List[ConductorNode] = Field(default_factory=list)
    segments: List[ConductorSegment] = Field(default_factory=list)
    separation_points: List[SeparationPoint] = Field(default_factory=list)
    results: List[SeparationCalculationResult] = Field(default_factory=list)
    schema_version: str = "1.0.0"

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {v!r}. Expected one of {_VALID_LPS_CLASSES} "
                "(IEC 62305-3:2024 Table 11)."
            )
        return v

    @field_validator("down_conductor_count", mode="before")
    @classmethod
    def _validate_down_conductor_count(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(
                "down_conductor_count must be a positive int, not bool."
            )
        if v <= 0:
            raise ValueError(
                f"down_conductor_count must be a positive int (> 0), got {v}."
            )
        return v

    @field_validator("earth_resistances_within_factor_2", mode="before")
    @classmethod
    def _validate_earth_resistances_within_factor_2(cls, v: Any) -> Optional[bool]:
        if v is None:
            return None
        if not isinstance(v, bool):
            raise ValueError(
                "earth_resistances_within_factor_2 must be a bool or None."
            )
        return v
