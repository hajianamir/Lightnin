from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
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
    insulation_medium: str = "air" # air, solid
    physical_distance_m: float

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
    building: Building = Field(default_factory=Building)
    nodes: List[ConductorNode] = Field(default_factory=list)
    segments: List[ConductorSegment] = Field(default_factory=list)
    separation_points: List[SeparationPoint] = Field(default_factory=list)
    results: List[SeparationCalculationResult] = Field(default_factory=list)
    schema_version: str = "1.0.0"
