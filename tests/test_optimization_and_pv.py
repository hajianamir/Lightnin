import pytest
from aegislps_engine.optimization import DesignOptimizationEngine, OptimizationInput, ProtectedTarget
from aegislps_engine.pv_module import PVEngineeringModule, PVArraySpecification
from aegislps_engine.cad_export import GLTF3DExporter
from aegislps_domain.integrity import ProjectIntegrityEngine

@pytest.mark.xfail(strict=True, reason="C1 physics: ground-referenced single-rod protection at roof z=15 m with R=20 m is <= 0.635 m; no roof coverage is reached by the 1..5 m rods in the current search space. Known open finding; see docs/KNOWN_ISSUES.md H7 / optimizer redesign (step 3.3).")
def test_design_optimization_coverage_improvement():
    engine = DesignOptimizationEngine()
    inp = OptimizationInput(
        lps_class="I",
        building_bounds=(-15.0, -10.0, 15.0, 10.0),
        roof_height_m=15.0,
        targets_to_protect=[
            ProtectedTarget(id="t1", x=-13.0, y=-8.0, z=15.0),
            ProtectedTarget(id="t2", x=13.0, y=-8.0, z=15.0),
            ProtectedTarget(id="t3", x=13.0, y=8.0, z=15.0),
            ProtectedTarget(id="t4", x=-13.0, y=8.0, z=15.0),
            ProtectedTarget(id="t5", x=0.0, y=0.0, z=16.5),
        ],
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
    
    # Case 1: Adequate physical clearance (1.5m > 0.792m req for Table 13 n=2, kc=0.66) -> Isolated PASS
    pv_isolated = PVArraySpecification(
        lps_class="I",
        down_conductor_length_l_m=15.0,
        separation_to_lps_m=1.5,
        insulation_medium="air",
        down_conductor_count=2,
        earth_resistances_within_factor_2=True,
    )
    res_iso = pv_engine.evaluate_pv_installation(pv_isolated)
    assert res_iso.kc_used == 0.66
    assert res_iso.is_isolated_lps_sufficient is True
    assert res_iso.requires_equipotential_bonding is False
    assert res_iso.status == "ISOLATED_PASS"

    # Case 2: Inadequate physical clearance (0.3m < 0.792m req) -> Bonding Mandatory
    pv_close = PVArraySpecification(
        lps_class="I",
        down_conductor_length_l_m=15.0,
        separation_to_lps_m=0.3,
        insulation_medium="air",
        down_conductor_count=2,
        earth_resistances_within_factor_2=True,
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
