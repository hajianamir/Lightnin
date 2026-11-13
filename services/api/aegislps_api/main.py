import hmac
import math
import os
from typing import Optional

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Request, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from aegislps_domain.models import Project, SeparationCalculationResult
from aegislps_domain.integrity import IntegrityKeyNotConfigured, ProjectIntegrityEngine
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_engine.nodal import NodalCurrentSolver, NodeIn, SegmentIn
from aegislps_engine.risk import RiskManagementEngine, RiskAssessmentInput
from aegislps_engine.earthing import EarthingEngine, EarthingAssessmentInput
from aegislps_engine.touch_step import TouchStepEngine, TouchStepAssessmentInput
from aegislps_engine.spd_coordination import SPDCoordinationEngine, SPDEntry, EquipmentWithstand
from aegislps_engine.optimization import DesignOptimizationEngine, OptimizationInput
from aegislps_engine.pv_module import PVEngineeringModule, PVArraySpecification
from aegislps_engine.uq_engine import UncertaintyQuantificationEngine, UQSimulationConfig
from aegislps_engine.peec_thermal import PEECThermalEngine, ConductorThermalProperties
from aegislps_geometry.mesh_rolling_sphere import ArbitraryMeshRollingSphereEngine, MeshRollingSphereInput
from aegislps_engine.comprehensive_risk import ComprehensiveRisk2024Engine, ComprehensiveRiskInput
from aegislps_geometry.mesh_method import MeshMethodEngine, MeshMethodInput
from aegislps_engine.hvi_conductor import HVIConductorAssistant, HVIConductorSelectionInput
from aegislps_engine.earth_pit import EarthPitEngine, EarthPitSizingInput
from aegislps_engine.earth_rod_sizing import EarthRodSizingEngine, EarthRodSizingInput
from aegislps_engine.bom_engine import BOMAndLifecycleEngine, ProjectBOMResult
from aegislps_engine.lemp_engine import LEMPEngine, LEMPWaveformSpecification, ShieldingGrid, InternalCableLoop
from aegislps_engine.cad_export import GLTF3DExporter
from aegislps_geometry.protective_angle import ProtectiveAngleEngine
from aegislps_geometry.rolling_sphere import (
    ROLLING_SPHERE_RADIUS_M_BY_CLASS,
    RollingSphereEngine,
)
from aegislps_engine.dxf_exporter import DXFExporter
from aegislps_engine.ifc_importer import IFCImporter
from aegislps_standards.repository import StandardsRepository
from aegislps_reporting.report_renderer import ReportRenderer
from aegislps_reporting.docx_renderer import DOCXReportRenderer

app = FastAPI(
    title="AegisLPS Advanced Engineering API",
    version="1.0.0-alpha.1",
    description="AegisLPS Lightning Protection Engineering Suite Professional REST API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "tauri://localhost",
        "http://tauri.localhost",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

SIDECAR_TOKEN_ENV_VAR = "AEGISLPS_SIDECAR_TOKEN"


def verify_sidecar_bearer_token(request: Request) -> None:
    """Enforce `Authorization: Bearer <token>` on `/api/v1/*` when `AEGISLPS_SIDECAR_TOKEN` is set."""
    expected_token = os.environ.get(SIDECAR_TOKEN_ENV_VAR)
    if expected_token is None or expected_token == "":
        return

    auth_header = request.headers.get("Authorization", "")
    scheme, sep, provided_token = auth_header.partition(" ")
    if (
        not sep
        or scheme.lower() != "bearer"
        or not provided_token
        or not hmac.compare_digest(
            provided_token.encode("utf-8"), expected_token.encode("utf-8")
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized.",
            headers={"WWW-Authenticate": "Bearer"},
        )


api_v1_router = APIRouter(dependencies=[Depends(verify_sidecar_bearer_token)])


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(IntegrityKeyNotConfigured)
async def integrity_key_not_configured_handler(
    request: Request, exc: IntegrityKeyNotConfigured
):
    return JSONResponse(
        status_code=503,
        content={"detail": "Integrity key is not configured on the server."},
    )


class RollingSphereRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    lps_class: Optional[str] = None
    sphere_radius_m: Optional[float] = None
    point_x: float
    point_y: float
    point_z: float
    rod_x: float
    rod_y: float
    rod_height_m: float

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v):
        if v is None:
            return None
        if not isinstance(v, str) or v not in ROLLING_SPHERE_RADIUS_M_BY_CLASS:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {tuple(ROLLING_SPHERE_RADIUS_M_BY_CLASS)}."
            )
        return v

    @field_validator(
        "sphere_radius_m",
        "point_x",
        "point_y",
        "point_z",
        "rod_x",
        "rod_y",
        "rod_height_m",
        mode="before",
    )
    @classmethod
    def _validate_scalars(cls, v, info):
        if v is None and info.field_name == "sphere_radius_m":
            return None
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(
                f"{info.field_name} must be a finite number, not bool; got {v!r}."
            )
        val = float(v)
        if not math.isfinite(val):
            raise ValueError(f"{info.field_name} must be finite, got {v!r}.")
        if info.field_name == "sphere_radius_m" and val <= 0.0:
            raise ValueError(f"sphere_radius_m must be > 0, got {v!r}.")
        return val

    @model_validator(mode="after")
    def _resolve_xor_radius(self) -> "RollingSphereRequest":
        has_class = self.lps_class is not None
        has_radius = self.sphere_radius_m is not None
        if has_class == has_radius:
            raise ValueError(
                "Exactly one of 'lps_class' or 'sphere_radius_m' must be provided."
            )
        if has_class:
            assert self.lps_class is not None
            self.sphere_radius_m = float(
                ROLLING_SPHERE_RADIUS_M_BY_CLASS[self.lps_class]
            )
        return self


class NodalKCRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    nodes: list[NodeIn]
    segments: list[SegmentIn]
    injection_node: str
    earth_nodes: list[str]
    total_injection_current_a: float
    # experimental single-frequency heuristic; not in IEC 62305-3:2024 Annex C
    equivalent_frequency_khz: float = 250.0

    @field_validator("injection_node", mode="before")
    @classmethod
    def _validate_injection_node(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"injection_node must be a non-empty string, got {v!r}.")
        return v

    @field_validator("earth_nodes", mode="before")
    @classmethod
    def _validate_earth_nodes(cls, v):
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError("earth_nodes must be a non-empty list of node IDs.")
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    f"earth_nodes items must be non-empty strings, got {item!r}."
                )
        return v

    @field_validator("total_injection_current_a", "equivalent_frequency_khz", mode="before")
    @classmethod
    def _validate_positive_scalars(cls, v, info):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(
                f"{info.field_name} must be a finite number > 0, not bool; got {v!r}."
            )
        val = float(v)
        if not math.isfinite(val) or val <= 0.0:
            raise ValueError(f"{info.field_name} must be finite and > 0, got {v!r}.")
        return val


class GenerateBOMRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    project_name: str
    lps_class: str
    building_length_m: float = Field(
        validation_alias=AliasChoices("building_length_m", "length_m")
    )
    building_width_m: float = Field(
        validation_alias=AliasChoices("building_width_m", "width_m")
    )
    building_height_m: float = Field(
        validation_alias=AliasChoices("building_height_m", "height_m")
    )
    rod_count: int
    down_conductor_count: int

    @field_validator("project_name", mode="before")
    @classmethod
    def _validate_project_name(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"project_name must be a non-empty string, got {v!r}.")
        return v

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v):
        if not isinstance(v, str) or v not in ROLLING_SPHERE_RADIUS_M_BY_CLASS:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {tuple(ROLLING_SPHERE_RADIUS_M_BY_CLASS)}."
            )
        return v

    @field_validator(
        "building_length_m", "building_width_m", "building_height_m", mode="before"
    )
    @classmethod
    def _validate_dims(cls, v, info):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(
                f"{info.field_name} must be a finite number > 0, not bool; got {v!r}."
            )
        val = float(v)
        if not math.isfinite(val) or val <= 0.0:
            raise ValueError(f"{info.field_name} must be finite and > 0, got {v!r}.")
        return val

    @field_validator("rod_count", "down_conductor_count", mode="before")
    @classmethod
    def _validate_counts(cls, v, info):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(
                f"{info.field_name} must be a strict int >= 1, not bool; got {v!r}."
            )
        if v < 1:
            raise ValueError(f"{info.field_name} must be >= 1, got {v!r}.")
        return v


class PEECThermalRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    props: ConductorThermalProperties
    lps_class: str
    parallel_conductor_spacing_m: float

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v):
        if not isinstance(v, str) or v not in ROLLING_SPHERE_RADIUS_M_BY_CLASS:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {tuple(ROLLING_SPHERE_RADIUS_M_BY_CLASS)}."
            )
        return v

    @field_validator("parallel_conductor_spacing_m", mode="before")
    @classmethod
    def _validate_spacing(cls, v):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(
                f"parallel_conductor_spacing_m must be a finite number > 0, not bool; got {v!r}."
            )
        val = float(v)
        if not math.isfinite(val) or val <= 0.0:
            raise ValueError(
                f"parallel_conductor_spacing_m must be finite and > 0, got {v!r}."
            )
        return val


standards_repo = StandardsRepository()
calc_engine = SeparationDistanceEngine(standards_repo)
nodal_solver = NodalCurrentSolver()
protective_angle_engine = ProtectiveAngleEngine()
risk_engine = RiskManagementEngine()
earthing_engine = EarthingEngine()
touch_step_engine = TouchStepEngine()
spd_engine = SPDCoordinationEngine()
optimization_engine = DesignOptimizationEngine()
pv_engine = PVEngineeringModule()
uq_engine = UncertaintyQuantificationEngine()
lemp_engine = LEMPEngine()
mesh_method_engine = MeshMethodEngine()
hvi_assistant = HVIConductorAssistant()
bom_engine = BOMAndLifecycleEngine()
earth_pit_engine = EarthPitEngine()
earth_rod_sizing_engine = EarthRodSizingEngine()
peec_engine = PEECThermalEngine()
mesh_rs_engine = ArbitraryMeshRollingSphereEngine()
comp_risk_engine = ComprehensiveRisk2024Engine()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "AegisLPS API", "version": "1.0.0-alpha.1"}

@api_v1_router.post("/api/v1/calculations/separation-distance", response_model=list[SeparationCalculationResult])
def calculate_separation_distance(project: Project):
    return calc_engine.calculate_project(project)

@api_v1_router.post("/api/v1/calculations/nodal-kc")
def calculate_nodal_kc(inputs: NodalKCRequest):
    solver = NodalCurrentSolver(
        equivalent_frequency_khz=inputs.equivalent_frequency_khz
    )
    solver.build_network(inputs.nodes, inputs.segments)
    return solver.calculate_current_sharing(
        inputs.injection_node,
        inputs.earth_nodes,
        inputs.total_injection_current_a,
    )

@api_v1_router.post("/api/v1/calculations/rolling-sphere")
def calculate_rolling_sphere(
    request: Request,
    inputs: Optional[RollingSphereRequest] = Body(default=None),
):
    if inputs is None:
        if not request.query_params:
            raise ValueError(
                "Request body or query parameters required for /api/v1/calculations/rolling-sphere."
            )
        qp = dict(request.query_params)
        parsed: dict = {}
        for k, raw in qp.items():
            if k == "lps_class":
                parsed[k] = raw
            elif k in {
                "sphere_radius_m",
                "point_x",
                "point_y",
                "point_z",
                "rod_x",
                "rod_y",
                "rod_height_m",
            }:
                if raw.strip().lower() in {"true", "false"}:
                    raise ValueError(
                        f"{k} must be a finite number, not bool; got {raw!r}."
                    )
                try:
                    parsed[k] = float(raw)
                except ValueError as exc:
                    raise ValueError(
                        f"{k} must be a finite number; got {raw!r}."
                    ) from exc
            else:
                parsed[k] = raw
        try:
            inputs = RollingSphereRequest.model_validate(parsed)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
    elif request.query_params:
        raise ValueError(
            "Provide rolling-sphere inputs either as JSON body or query parameters, not both."
        )

    assert inputs.sphere_radius_m is not None
    engine = RollingSphereEngine(sphere_radius_m=inputs.sphere_radius_m)
    return engine.check_surface_exposure(
        inputs.point_x,
        inputs.point_y,
        inputs.point_z,
        inputs.rod_x,
        inputs.rod_y,
        inputs.rod_height_m,
    )

@api_v1_router.post("/api/v1/calculations/protective-angle")
def calculate_protective_angle(lps_class: str, rod_tip_x: float, rod_tip_y: float, rod_tip_z: float, ref_plane_z: float, object_x: float, object_y: float, object_z: float):
    return protective_angle_engine.check_object_in_cone(lps_class, rod_tip_x, rod_tip_y, rod_tip_z, ref_plane_z, object_x, object_y, object_z)

@api_v1_router.post("/api/v1/calculations/earthing")
def calculate_earthing(inputs: EarthingAssessmentInput):
    return earthing_engine.evaluate_earthing_system(inputs)

@api_v1_router.post("/api/v1/calculations/touch-step")
def calculate_touch_step(inputs: TouchStepAssessmentInput):
    return touch_step_engine.evaluate(inputs)

@api_v1_router.post("/api/v1/calculations/spd-coordination")
def calculate_spd_coordination(spds: list[SPDEntry], equipment: EquipmentWithstand):
    return spd_engine.evaluate_coordination(spds, equipment)

@api_v1_router.post("/api/v1/calculations/risk")
def calculate_risk(inputs: RiskAssessmentInput):
    return risk_engine.evaluate_r1_risk(inputs)

@api_v1_router.post("/api/v1/calculations/pv-clearance")
def calculate_pv_clearance(pv_spec: PVArraySpecification):
    return pv_engine.evaluate_pv_installation(pv_spec)

@api_v1_router.post("/api/v1/calculations/earth-pit-sizing")
def calculate_earth_pit_sizing(inputs: EarthPitSizingInput):
    return earth_pit_engine.evaluate_earth_pit_and_backfill(inputs)

@api_v1_router.post("/api/v1/calculations/earth-rod-sizing")
def calculate_earth_rod_sizing(inputs: EarthRodSizingInput):
    return earth_rod_sizing_engine.size_earth_rod_system(inputs)

@api_v1_router.post("/api/v1/calculations/mesh-method")
def calculate_mesh_method(inputs: MeshMethodInput):
    return mesh_method_engine.validate_mesh_design(inputs)

@api_v1_router.post("/api/v1/calculations/hvi-selection")
def calculate_hvi_selection(inputs: HVIConductorSelectionInput):
    return hvi_assistant.evaluate_hvi_selection(inputs)

@api_v1_router.post("/api/v1/projects/generate-bom")
def generate_project_bom(inputs: GenerateBOMRequest):
    return bom_engine.generate_project_bom(
        inputs.project_name,
        inputs.lps_class,
        inputs.building_length_m,
        inputs.building_width_m,
        inputs.building_height_m,
        inputs.rod_count,
        inputs.down_conductor_count,
    )

@api_v1_router.post("/api/v1/calculations/peec-thermal")
def calculate_peec_thermal(inputs: PEECThermalRequest):
    return peec_engine.evaluate_thermal_and_electrodynamic_stress(
        inputs.props,
        inputs.lps_class,
        inputs.parallel_conductor_spacing_m,
    )

@api_v1_router.post("/api/v1/calculations/mesh-rolling-sphere")
def calculate_mesh_rolling_sphere(inputs: MeshRollingSphereInput):
    return mesh_rs_engine.evaluate_mesh_protection(inputs)

@api_v1_router.post("/api/v1/calculations/comprehensive-risk-2024")
def calculate_comprehensive_risk_2024(inputs: ComprehensiveRiskInput):
    return comp_risk_engine.evaluate_risk(inputs)

@api_v1_router.post("/api/v1/calculations/lemp-induced-voltage")
def calculate_lemp_induced_voltage(waveform: LEMPWaveformSpecification, shield: ShieldingGrid, loop: InternalCableLoop):
    return lemp_engine.calculate_lemp_induction(waveform, shield, loop)

@api_v1_router.post("/api/v1/calculations/uq-monte-carlo")
def calculate_uq_monte_carlo(config: UQSimulationConfig):
    return uq_engine.run_monte_carlo(config)

@api_v1_router.post("/api/v1/optimization/optimize-rods")
def optimize_air_terminations(inputs: OptimizationInput):
    return optimization_engine.optimize_air_terminations(inputs)

@api_v1_router.post("/api/v1/exports/gltf")
def export_gltf_3d(project: Project):
    gltf_str = GLTF3DExporter.export_gltf_scene(
        project.building.length_m,
        project.building.width_m,
        project.building.height_m,
        [n.model_dump() for n in project.nodes],
        [s.model_dump() for s in project.segments] if project.segments else None,
    )
    return Response(content=gltf_str, media_type="model/gltf+json", headers={
        "Content-Disposition": f"attachment; filename=AegisLPS_Scene_{project.project_id[:8]}.gltf"
    })

@api_v1_router.post("/api/v1/exports/dxf")
def export_dxf_plan(project: Project):
    dxf_bytes = DXFExporter.export_2d_plan(
        project.building.length_m,
        project.building.width_m,
        [n.model_dump() for n in project.nodes],
        [s.model_dump() for s in project.segments] if project.segments else None,
    )
    return Response(content=dxf_bytes, media_type="application/dxf", headers={
        "Content-Disposition": f"attachment; filename=AegisLPS_2D_Plan_{project.project_id[:8]}.dxf"
    })

@api_v1_router.post("/api/v1/imports/ifc")
async def import_ifc_model(file: UploadFile = File(...)):
    content = await file.read()
    return IFCImporter.parse_ifc_building_elements(content)

@api_v1_router.post("/api/v1/projects/compute-checksum")
def compute_checksum(project: Project):
    checksum = ProjectIntegrityEngine.compute_project_checksum(project.model_dump())
    return {"project_id": project.project_id, "checksum": checksum}

@api_v1_router.post("/api/v1/reports/docx")
def generate_docx_report(project: Project):
    results = calc_engine.calculate_project(project)
    try:
        computed_checksum: Optional[str] = compute_checksum(project)["checksum"]
    except IntegrityKeyNotConfigured:
        computed_checksum = None
    docx_bytes = DOCXReportRenderer.render_docx_report(
        project, results, checksum=computed_checksum
    )
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=AegisLPS_Report_{project.project_id[:8]}.docx"
        }
    )

@api_v1_router.post("/api/v1/reports/pdf")
def generate_pdf_report(project: Project):
    results = calc_engine.calculate_project(project)
    pdf_bytes = ReportRenderer.render_pdf_report(project, results)

    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=AegisLPS_Report_{project.project_id[:8]}.pdf"
    })

app.include_router(api_v1_router)
