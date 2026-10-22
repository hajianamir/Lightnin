from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aegislps_domain.models import Project, SeparationCalculationResult
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_engine.nodal import NodalCurrentSolver
from aegislps_engine.risk import RiskManagementEngine, RiskAssessmentInput
from aegislps_engine.dxf_exporter import DXFExporter
from aegislps_engine.ifc_importer import IFCImporter
from aegislps_geometry.rolling_sphere import RollingSphereEngine
from aegislps_standards.repository import StandardsRepository
from aegislps_reporting.report_renderer import ReportRenderer

app = FastAPI(
    title="AegisLPS API Service",
    version="1.0.0-draft",
    description="Provisional AegisLPS Engineering Platform API"
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
risk_engine = RiskManagementEngine()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "AegisLPS API", "version": "1.0.0-draft"}

@app.post("/api/v1/calculations/separation-distance", response_model=list[SeparationCalculationResult])
def calculate_separation_distance(project: Project):
    return calc_engine.calculate_project(project)

@app.post("/api/v1/calculations/nodal-kc")
def calculate_nodal_kc(nodes: list[dict], segments: list[dict], injection_node: str, earth_nodes: list[str]):
    nodal_solver.build_network(nodes, segments)
    kc_factors = nodal_solver.calculate_current_sharing(injection_node, earth_nodes)
    return {"kc_factors": kc_factors}

@app.post("/api/v1/calculations/rolling-sphere")
def calculate_rolling_sphere(point_x: float, point_y: float, point_z: float, rod_x: float, rod_y: float, rod_height_m: float):
    return rolling_sphere_engine.check_surface_exposure(point_x, point_y, point_z, rod_x, rod_y, rod_height_m)

@app.post("/api/v1/calculations/risk")
def calculate_risk(inputs: RiskAssessmentInput):
    return risk_engine.evaluate_r1_risk(inputs)

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
    parsed_res = IFCImporter.parse_ifc_building_elements(content)
    return parsed_res

@app.post("/api/v1/reports/pdf")
def generate_pdf_report(project: Project):
    results = calc_engine.calculate_project(project)
    pdf_bytes = ReportRenderer.render_pdf_report(project, results)

    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=AegisLPS_Report_{project.project_id[:8]}.pdf"
    })
