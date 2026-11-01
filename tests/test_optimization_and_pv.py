import pytest
from aegislps_engine.optimization import DesignOptimizationEngine, OptimizationInput, ProtectedTarget
from aegislps_engine.pv_module import PVEngineeringModule, PVArraySpecification
from aegislps_engine.cad_export import GLTF3DExporter
from aegislps_domain.integrity import ProjectIntegrityEngine

def test_design_optimization_coverage_improvement():
    engine = DesignOptimizationEngine()
    inp = OptimizationInput(
        lps_class="I",
        building_bounds=(-15.0, -10.0, 15.0, 10.0),
        roof_height_m=15.0,
        iterations=50,
        random_seed=123
    )
    res = engine.optimize_air_terminations(inp)
    assert len(res.selected_rods) >= 2
    assert res.coverage_percentage >= 50.0
    assert res.total_rod_cost > 0
    assert res.iterations_run == 50

def test_pv_rooftop_isolated_clearance():
    pv_engine = PVEngineeringModule()

    # Case 1: Adequate physical clearance (1.5m > 0.6m req) -> Isolated PASS
    pv_isolated = PVArraySpecification(
        lps_class="I",
        down_conductor_length_l_m=15.0,
        separation_to_lps_m=1.5
    )
    res_iso = pv_engine.evaluate_pv_installation(pv_isolated)
    assert res_iso.is_isolated_lps_sufficient is True
    assert res_iso.requires_equipotential_bonding is False
    assert res_iso.status == "ISOLATED_PASS"

    # Case 2: Inadequate physical clearance (0.3m < 0.6m req) -> Bonding Mandatory
    pv_close = PVArraySpecification(
        lps_class="I",
        down_conductor_length_l_m=15.0,
        separation_to_lps_m=0.3
    )
    res_close = pv_engine.evaluate_pv_installation(pv_close)
    assert res_close.is_isolated_lps_sufficient is False
    assert res_close.requires_equipotential_bonding is True
    assert res_close.status == "BONDING_MANDATORY"

def test_gltf_3d_export():
    gltf_json = GLTF3DExporter.export_gltf_scene(30.0, 20.0, 15.0, [])
    assert "asset" in gltf_json
    assert "Building_Envelope" in gltf_json
    assert "2.0" in gltf_json

def test_cryptographic_project_integrity():
    proj_data = {
        "project_id": "proj-uuid-1234",
        "name": "Substation LPS Design",
        "lps_class": "I",
        "approved": True
    }
    checksum = ProjectIntegrityEngine.compute_project_checksum(proj_data)
    assert isinstance(checksum, str)
    assert len(checksum) == 64 # SHA-256 hex string

    # Verify matching integrity
    assert ProjectIntegrityEngine.verify_project_integrity(proj_data, checksum) is True

    # Tampered data should fail integrity
    tampered_data = dict(proj_data)
    tampered_data["lps_class"] = "II"
    assert ProjectIntegrityEngine.verify_project_integrity(tampered_data, checksum) is False
