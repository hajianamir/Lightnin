from enum import Enum
import math
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
import uuid

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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    x: float
    y: float
    z: float
    node_type: str = "air_termination" # air_termination, down_conductor, earth_point, bonding

class ConductorSegment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_node_id: str
    end_node_id: str
    material: str = "copper"
    cross_section_mm2: float = 50.0
    kc_factor: float = 1.0

class SeparationPoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    x: float
    y: float
    z: float
    associated_node_id: str
    insulation_medium: str = "air" # air, solid, insulating_standoff
    physical_distance_m: float
    route_length_to_bonding_m: Optional[float] = None

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
    length_m: float = 20.0
    width_m: float = 10.0
    height_m: float = 15.0
    roof_type: str = "flat"

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
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New AegisLPS Project"
    lps_class: str = "I"
    down_conductor_count: Optional[int] = None
    earth_resistances_within_factor_2: Optional[bool] = None
    building: Building = Field(default_factory=Building)
    nodes: List[ConductorNode] = Field(default_factory=list)
    segments: List[ConductorSegment] = Field(default_factory=list)
    separation_points: List[SeparationPoint] = Field(default_factory=list)
    results: List[SeparationCalculationResult] = Field(default_factory=list)
    schema_version: str = "1.0.0"

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
