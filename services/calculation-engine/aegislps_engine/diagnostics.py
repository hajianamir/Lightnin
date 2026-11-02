import sys
import os
import numpy as np
from typing import Dict, List, Any

from aegislps_standards.repository import StandardsRepository
from aegislps_domain.models import Project, Building, ConductorNode, SeparationPoint
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_engine.nodal import NodalCurrentSolver
from aegislps_engine.earthing import EarthingEngine, EarthingAssessmentInput
from aegislps_engine.touch_step import TouchStepEngine, TouchStepAssessmentInput
from aegislps_engine.spd_coordination import SPDCoordinationEngine, SPDEntry
from aegislps_geometry.rolling_sphere import RollingSphereEngine
from aegislps_geometry.protective_angle import ProtectiveAngleEngine

class SystemDiagnostics:
    """
    Automated Field & Laboratory Self-Test Diagnostics for AegisLPS.
    Verifies calculation numerical stability, standards availability, and runtime readiness.
    """
    @classmethod
    def run_self_test(cls) -> Dict[str, Any]:
        results = {}

        # 1. Standards Store Check
        repo = StandardsRepository()
        p1 = repo.get_parameter("IEC 62305-3:2024", "ki_class_I")
        results["standards_store"] = {
            "status": "PASS" if p1 and p1.value == 0.08 else "FAIL",
            "message": "Standards parameter repository loaded correctly."
        }

        # 2. Separation Distance Calculation
        engine = SeparationDistanceEngine(repo)
        proj = Project(
            name="Diag Proj",
            lps_class="I",
            building=Building(height_m=15.0),
            nodes=[ConductorNode(id="n1", x=0, y=0, z=15.0)],
            separation_points=[SeparationPoint(id="sp1", name="P1", x=0, y=0, z=15.0, associated_node_id="n1", physical_distance_m=1.5)]
        )
        sep_res = engine.calculate_project(proj)
        results["separation_engine"] = {
            "status": "PASS" if len(sep_res) == 1 and abs(sep_res[0].required_distance_s_m - 1.2) < 1e-3 else "FAIL",
            "message": f"Solved s = {sep_res[0].required_distance_s_m:.3f} m (Target: 1.200 m)"
        }

        # 3. Nodal Admittance Solver
        nodal = NodalCurrentSolver()
        nodal.build_network(
            [{"id": "n1", "x": 0, "y": 0, "z": 10}, {"id": "n2", "x": 0, "y": 0, "z": 0}, {"id": "n3", "x": 10, "y": 0, "z": 0}],
            [{"id": "s1", "start_node_id": "n1", "end_node_id": "n2"}, {"id": "s2", "start_node_id": "n1", "end_node_id": "n3"}]
        )
        n_res = nodal.calculate_current_sharing("n1", ["n2", "n3"])
        results["nodal_solver"] = {
            "status": "PASS" if n_res["converged"] else "FAIL",
            "message": f"Current conservation relative residual: {n_res['relative_residual']*100:.2f}%"
        }

        # 4. Earthing Dwight Formula
        earth = EarthingEngine()
        e_res = earth.evaluate_earthing_system(EarthingAssessmentInput(lps_class="I", ring_radius_m=15.0))
        results["earthing_engine"] = {
            "status": "PASS" if e_res.stationary_resistance_r_ohm > 0 else "FAIL",
            "message": f"Type B ring resistance: {e_res.stationary_resistance_r_ohm:.2f} ohm"
        }

        all_passed = all(r["status"] == "PASS" for r in results.values())
        return {
            "system_status": "OPERATIONAL" if all_passed else "DEGRADED",
            "tests": results
        }
