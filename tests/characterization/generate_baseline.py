"""Characterization snapshot generator (Step 0.1).

Records the CURRENT numerical behaviour of the calculation engines for fixed
inputs. This is a regression snapshot, NOT a validation: some recorded values
are known to be wrong (see docs/KNOWN_ISSUES.md once created). Regenerate only
in a step that explicitly allows it.

Usage:  python tests/characterization/generate_baseline.py
"""
import json
import math
import os
import sys

import numpy as np

from aegislps_domain.models import Project, Building, ConductorNode, SeparationPoint, ConductorSegment
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_engine.earthing import EarthingEngine, EarthingAssessmentInput, SoilLayerModel
from aegislps_engine.touch_step import TouchStepEngine, TouchStepAssessmentInput
from aegislps_engine.spd_coordination import SPDCoordinationEngine, SPDEntry
from aegislps_engine.risk import RiskManagementEngine, RiskAssessmentInput
from aegislps_engine.comprehensive_risk import (
    ComprehensiveRisk2024Engine, ComprehensiveRiskInput, IncomingServiceLine,
)
from aegislps_engine.lemp_engine import (
    LEMPEngine, LEMPWaveformSpecification, ShieldingGrid, InternalCableLoop,
)
from aegislps_engine.earth_rod_sizing import EarthRodSizingEngine, EarthRodSizingInput
from aegislps_engine.earth_pit import EarthPitEngine, EarthPitSizingInput
from aegislps_engine.pv_module import PVEngineeringModule, PVArraySpecification
from aegislps_engine.hvi_conductor import HVIConductorAssistant, HVIConductorSelectionInput
from aegislps_engine.bom_engine import BOMAndLifecycleEngine
from aegislps_engine.peec_thermal import PEECThermalEngine, ConductorThermalProperties
from aegislps_engine.nodal import NodalCurrentSolver
from aegislps_engine.uq_engine import UncertaintyQuantificationEngine, UQSimulationConfig
from aegislps_engine.optimization import DesignOptimizationEngine, OptimizationInput
from aegislps_geometry.protective_angle import ProtectiveAngleEngine
from aegislps_geometry.rolling_sphere import RollingSphereEngine
from aegislps_geometry.mesh_method import MeshMethodEngine, MeshMethodInput
from aegislps_geometry.mesh_rolling_sphere import (
    ArbitraryMeshRollingSphereEngine, MeshRollingSphereInput, TriangleFace,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "baseline")


def _norm(obj):
    """Convert results to plain, deterministic Python structures."""
    if hasattr(obj, "model_dump"):
        return _norm(obj.model_dump())
    if isinstance(obj, dict):
        return {str(k): _norm(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, (list, tuple)):
        return [_norm(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        if math.isnan(f) or math.isinf(f):
            return str(f)
        return float(f"{f:.9g}")
    if hasattr(obj, "value") and isinstance(getattr(obj, "value"), str):  # Enum
        return obj.value
    return obj


def build_snapshots():
    snaps = {}

    # 1. Separation distance (1 and 2 segments)
    for n_seg in (1, 2):
        segs = [ConductorSegment(id=f"s{i}", start_node_id="n1", end_node_id="n1") for i in range(n_seg)]
        proj = Project(
            name="baseline", lps_class="I", building=Building(height_m=15.0),
            nodes=[ConductorNode(id="n1", x=0, y=0, z=15.0)],
            segments=segs,
            separation_points=[SeparationPoint(id="sp1", name="P1", x=0, y=0, z=15.0,
                                               associated_node_id="n1", physical_distance_m=2.0)],
        )
        snaps[f"separation_{n_seg}seg"] = SeparationDistanceEngine().calculate_project(proj)

    # 2. Earthing
    eng = EarthingEngine()
    snaps["earthing_ring"] = eng.evaluate_earthing_system(EarthingAssessmentInput(
        electrode_type="type_b_ring", ring_radius_m=15.0, soil=SoilLayerModel(rho_upper_ohm_m=100.0)))
    snaps["earthing_vertical_1rod"] = eng.evaluate_earthing_system(EarthingAssessmentInput(
        electrode_type="type_a_vertical", vertical_rod_count=1, soil=SoilLayerModel(rho_upper_ohm_m=100.0)))
    snaps["earthing_vertical_4rods"] = eng.evaluate_earthing_system(EarthingAssessmentInput(
        electrode_type="type_a_vertical", vertical_rod_count=4, vertical_rod_spacing_m=5.0,
        soil=SoilLayerModel(rho_upper_ohm_m=100.0)))
    snaps["earthing_horizontal"] = eng.evaluate_earthing_system(EarthingAssessmentInput(
        electrode_type="type_a_horizontal", ring_radius_m=15.0, soil=SoilLayerModel(rho_upper_ohm_m=100.0)))
    snaps["earthing_foundation"] = eng.evaluate_earthing_system(EarthingAssessmentInput(
        electrode_type="foundation", soil=SoilLayerModel(rho_upper_ohm_m=100.0)))

    # 3. Touch / step
    ts = TouchStepEngine()
    snaps["touch_step_default"] = ts.evaluate(TouchStepAssessmentInput())
    snaps["touch_step_fence"] = ts.evaluate(TouchStepAssessmentInput(has_restricted_access_perimeter=True))
    snaps["touch_step_barrier"] = ts.evaluate(TouchStepAssessmentInput(has_physical_insulation_barrier=True))

    # 4. SPD coordination
    snaps["spd_coordination"] = SPDCoordinationEngine().evaluate_coordination([
        SPDEntry(id="t1", spd_class="Type 1", technology="spark_gap", cable_length_to_downstream_m=5.0),
        SPDEntry(id="t2", spd_class="Type 2", technology="varistor_mov", up_kv=1.2),
    ])

    # 5. Risk (IEC 62305-2 simplified and 2024-style)
    snaps["risk_default"] = RiskManagementEngine().evaluate_r1_risk(RiskAssessmentInput())
    crisk = ComprehensiveRisk2024Engine()
    snaps["comprehensive_risk_default"] = crisk.evaluate_risk(ComprehensiveRiskInput())
    snaps["comprehensive_risk_transformer"] = crisk.evaluate_risk(ComprehensiveRiskInput(
        incoming_lines=[IncomingServiceLine(transformer_present=True, shielded=False)]))
    snaps["comprehensive_risk_shielded"] = crisk.evaluate_risk(ComprehensiveRiskInput(
        incoming_lines=[IncomingServiceLine(transformer_present=False, shielded=True)]))

    # 6. LEMP
    lemp = LEMPEngine()
    for stroke in ("first_positive_10_350", "subsequent_negative_025_100"):
        snaps[f"lemp_{stroke}"] = lemp.calculate_lemp_induction(
            LEMPWaveformSpecification(stroke_type=stroke, peak_current_ka=100.0, t_end_us=100.0, num_time_steps=500),
            ShieldingGrid(mesh_width_w_m=5.0), InternalCableLoop())
        t = np.linspace(0.0, 100.0, 1000)
        i_ka, di_dt, mx = LEMPEngine.evaluate_heidler_current(t, stroke, 100.0)
        snaps[f"heidler_{stroke}"] = {
            "peak_ka": float(np.max(i_ka)),
            "t_peak_us": float(t[int(np.argmax(i_ka))]),
            "max_di_dt_ka_per_us": float(mx),
            "samples_ka_every_50": [float(v) for v in i_ka[::50]],
        }

    # 7. Protective angle and rolling sphere
    snaps["protective_angle_table"] = {
        cls: {str(h): ProtectiveAngleEngine.get_protective_angle_deg(cls, float(h))
              for h in (2, 5, 10, 20, 45, 60)}
        for cls in ("I", "II", "III", "IV")
    }
    pa = ProtectiveAngleEngine()
    snaps["protective_angle_protected"] = pa.check_object_in_cone("I", 0, 0, 10, 0, 2, 0, 5)
    snaps["protective_angle_exposed"] = pa.check_object_in_cone("I", 0, 0, 10, 0, 12, 0, 5)
    rs = RollingSphereEngine(20.0)
    snaps["rolling_sphere_points"] = [
        rs.check_surface_exposure(px, py, pz, 0.0, 0.0, 10.0)
        for (px, py, pz) in ((1.0, 0.0, 5.0), (5.0, 0.0, 5.0), (12.0, 0.0, 2.0))
    ]

    # 8. Mesh method
    snaps["mesh_method_default"] = MeshMethodEngine().validate_mesh_design(MeshMethodInput())

    # 9. Earth rod sizing, earth pit, PV, HVI, BOM
    snaps["earth_rod_sizing"] = EarthRodSizingEngine().size_earth_rod_system(EarthRodSizingInput())
    snaps["earth_pit"] = EarthPitEngine().evaluate_earth_pit_and_backfill(EarthPitSizingInput())
    snaps["pv_module"] = PVEngineeringModule().evaluate_pv_installation(PVArraySpecification())
    snaps["hvi_selection"] = HVIConductorAssistant().evaluate_hvi_selection(HVIConductorSelectionInput())
    snaps["bom"] = BOMAndLifecycleEngine().generate_project_bom("Test", "I", 30.0, 20.0, 15.0)

    # 10. PEEC thermal / electrodynamic
    snaps["peec_thermal"] = PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(
        ConductorThermalProperties(material="copper", cross_section_mm2=50.0, initial_temperature_c=20.0), "I")

    # 11. Nodal solver (same topology as diagnostics.py)
    nodal = NodalCurrentSolver()
    nodal.build_network(
        [{"id": "n1", "x": 0, "y": 0, "z": 10}, {"id": "n2", "x": 0, "y": 0, "z": 0}, {"id": "n3", "x": 10, "y": 0, "z": 0}],
        [{"id": "s1", "start_node_id": "n1", "end_node_id": "n2"}, {"id": "s2", "start_node_id": "n1", "end_node_id": "n3"}],
    )
    snaps["nodal_solver"] = nodal.calculate_current_sharing("n1", ["n2", "n3"])

    # 12. UQ and optimization (fixed seeds)
    snaps["uq_monte_carlo"] = UncertaintyQuantificationEngine().run_monte_carlo(UQSimulationConfig())
    snaps["optimization"] = DesignOptimizationEngine().optimize_air_terminations(OptimizationInput())

    # 13. Arbitrary mesh rolling sphere (two triangles)
    tri_under = TriangleFace(id="under", v0=(-0.5, -0.5, 2.0), v1=(0.5, -0.5, 2.0), v2=(0.0, 0.5, 2.0))
    tri_far = TriangleFace(id="far", v0=(50.0, 50.0, 2.0), v1=(51.0, 50.0, 2.0), v2=(50.0, 51.0, 2.0))
    snaps["mesh_rolling_sphere"] = ArbitraryMeshRollingSphereEngine().evaluate_mesh_protection(
        MeshRollingSphereInput(sphere_radius_m=20.0, triangles=[tri_under, tri_far],
                               air_termination_tips=[(0.0, 0.0, 10.0)]))

    return snaps


def write_all(out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    snaps = build_snapshots()
    written = []
    for name, obj in snaps.items():
        data = _norm(obj)
        path = os.path.join(out_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        written.append(path)
    return written


if __name__ == "__main__":
    paths = write_all()
    print(f"Wrote {len(paths)} snapshot files to {OUT_DIR}")
    sys.exit(0)
