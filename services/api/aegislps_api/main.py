from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aegislps_domain.models import Project, SeparationCalculationResult
from aegislps_domain.integrity import ProjectIntegrityEngine
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_engine.nodal import NodalCurrentSolver
from aegislps_engine.risk import RiskManagementEngine, RiskAssessmentInput
from aegislps_engine.earthing import EarthingEngine, EarthingAssessmentInput
from aegislps_engine.touch_step import TouchStepEngine, TouchStepAssessmentInput
from aegislps_engine.spd_coordination import SPDCoordinationEngine, SPDEntry
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
from aegislps_geometry.rolling_sphere import RollingSphereEngine
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

standards_repo = StandardsRepository()
calc_engine = SeparationDistanceEngine(standards_repo)
nodal_solver = NodalCurrentSolver()
rolling_sphere_engine = RollingSphereEngine()
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

@app.post("/api/v1/calculations/separation-distance", response_model=list[SeparationCalculationResult])
def calculate_separation_distance(project: Project):
    return calc_engine.calculate_project(project)

@app.post("/api/v1/calculations/nodal-kc")
def calculate_nodal_kc(nodes: list[dict], segments: list[dict], injection_node: str, earth_nodes: list[str]):
    nodal_solver.build_network(nodes, segments)
    return nodal_solver.calculate_current_sharing(injection_node, earth_nodes)

@app.post("/api/v1/calculations/rolling-sphere")
def calculate_rolling_sphere(point_x: float, point_y: float, point_z: float, rod_x: float, rod_y: float, rod_height_m: float):
    return rolling_sphere_engine.check_surface_exposure(point_x, point_y, point_z, rod_x, rod_y, rod_height_m)

@app.post("/api/v1/calculations/protective-angle")
def calculate_protective_angle(lps_class: str, rod_tip_x: float, rod_tip_y: float, rod_tip_z: float, ref_plane_z: float, object_x: float, object_y: float, object_z: float):
    return protective_angle_engine.check_object_in_cone(lps_class, rod_tip_x, rod_tip_y, rod_tip_z, ref_plane_z, object_x, object_y, object_z)

@app.post("/api/v1/calculations/earthing")
def calculate_earthing(inputs: EarthingAssessmentInput):
    return earthing_engine.evaluate_earthing_system(inputs)

@app.post("/api/v1/calculations/touch-step")
def calculate_touch_step(inputs: TouchStepAssessmentInput):
    return touch_step_engine.evaluate(inputs)

@app.post("/api/v1/calculations/spd-coordination")
def calculate_spd_coordination(spds: list[SPDEntry]):
    return spd_engine.evaluate_coordination(spds)

@app.post("/api/v1/calculations/risk")
def calculate_risk(inputs: RiskAssessmentInput):
    return risk_engine.evaluate_r1_risk(inputs)

@app.post("/api/v1/calculations/pv-clearance")
def calculate_pv_clearance(pv_spec: PVArraySpecification):
    return pv_engine.evaluate_pv_installation(pv_spec)

@app.post("/api/v1/calculations/earth-pit-sizing")
def calculate_earth_pit_sizing(inputs: EarthPitSizingInput):
    return earth_pit_engine.evaluate_earth_pit_and_backfill(inputs)

@app.post("/api/v1/calculations/earth-rod-sizing")
def calculate_earth_rod_sizing(inputs: EarthRodSizingInput):
    return earth_rod_sizing_engine.size_earth_rod_system(inputs)

@app.post("/api/v1/calculations/mesh-method")
def calculate_mesh_method(inputs: MeshMethodInput):
    return mesh_method_engine.validate_mesh_design(inputs)

@app.post("/api/v1/calculations/hvi-selection")
def calculate_hvi_selection(inputs: HVIConductorSelectionInput):
    return hvi_assistant.evaluate_hvi_selection(inputs)

@app.post("/api/v1/projects/generate-bom")
def generate_project_bom(project_name: str, lps_class: str, length_m: float, width_m: float, height_m: float):
    return bom_engine.generate_project_bom(project_name, lps_class, length_m, width_m, height_m)

@app.post("/api/v1/calculations/peec-thermal")
def calculate_peec_thermal(props: ConductorThermalProperties, lps_class: str = "I"):
    return peec_engine.evaluate_thermal_and_electrodynamic_stress(props, lps_class)

@app.post("/api/v1/calculations/mesh-rolling-sphere")
def calculate_mesh_rolling_sphere(inputs: MeshRollingSphereInput):
    return mesh_rs_engine.evaluate_mesh_protection(inputs)

@app.post("/api/v1/calculations/comprehensive-risk-2024")
def calculate_comprehensive_risk_2024(inputs: ComprehensiveRiskInput):
    return comp_risk_engine.evaluate_risk(inputs)

@app.post("/api/v1/calculations/lemp-induced-voltage")
def calculate_lemp_induced_voltage(waveform: LEMPWaveformSpecification, shield: ShieldingGrid, loop: InternalCableLoop):
    return lemp_engine.calculate_lemp_induction(waveform, shield, loop)

@app.post("/api/v1/calculations/uq-monte-carlo")
def calculate_uq_monte_carlo(config: UQSimulationConfig):
    return uq_engine.run_monte_carlo(config)

@app.post("/api/v1/optimization/optimize-rods")
def optimize_air_terminations(inputs: OptimizationInput):
    return optimization_engine.optimize_air_terminations(inputs)

@app.post("/api/v1/exports/gltf")
def export_gltf_3d(project: Project):
    gltf_str = GLTF3DExporter.export_gltf_scene(
        project.building.length_m,
        project.building.width_m,
        project.building.height_m,
        [n.model_dump() for n in project.nodes]
    )
    return Response(content=gltf_str, media_type="model/gltf+json", headers={
        "Content-Disposition": f"attachment; filename=AegisLPS_Scene_{project.project_id[:8]}.gltf"
    })

@app.post("/api/v1/exports/dxf")
def export_dxf_plan(project: Project):
    dxf_bytes = DXFExporter.export_2d_plan(
        project.building.length_m,
        project.building.width_m,
        [n.model_dump() for n in project.nodes]
    )
    return Response(content=dxf_bytes, media_type="application/dxf", headers={
        "Content-Disposition": f"attachment; filename=AegisLPS_2D_Plan_{project.project_id[:8]}.dxf"
    })

@app.post("/api/v1/imports/ifc")
async def import_ifc_model(file: UploadFile = File(...)):
    content = await file.read()
    return IFCImporter.parse_ifc_building_elements(content)

@app.post("/api/v1/projects/compute-checksum")
def compute_checksum(project: Project):
    checksum = ProjectIntegrityEngine.compute_project_checksum(project.model_dump())
    return {"project_id": project.project_id, "checksum": checksum}

@app.post("/api/v1/reports/docx")
def generate_docx_report(project: Project):
    results = calc_engine.calculate_project(project)
    docx_bytes = DOCXReportRenderer.render_docx_report(project, results)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=AegisLPS_Report_{project.project_id[:8]}.docx"
        }
    )

@app.post("/api/v1/reports/pdf")
def generate_pdf_report(project: Project):
    results = calc_engine.calculate_project(project)
    pdf_bytes = ReportRenderer.render_pdf_report(project, results)

    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=AegisLPS_Report_{project.project_id[:8]}.pdf"
    })
