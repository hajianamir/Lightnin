import pytest
from aegislps_engine.nodal import NodalCurrentSolver
from aegislps_geometry.rolling_sphere import RollingSphereEngine
from aegislps_engine.risk import RiskManagementEngine, RiskAssessmentInput
from aegislps_engine.dxf_exporter import DXFExporter
from aegislps_engine.ifc_importer import IFCImporter

def test_nodal_solver_current_sharing():
    solver = NodalCurrentSolver()
    nodes = [
        {"id": "n1", "x": 0, "y": 0, "z": 15, "node_type": "conductor"},
        {"id": "n2", "x": 10, "y": 0, "z": 0, "node_type": "conductor"},
        {"id": "n3", "x": -10, "y": 0, "z": 0, "node_type": "conductor"}
    ]
    segments = [
        {"id": "s1", "start_node_id": "n1", "end_node_id": "n2", "cross_section_mm2": 50, "resistivity_ohm_m": 1.72e-8},
        {"id": "s2", "start_node_id": "n1", "end_node_id": "n3", "cross_section_mm2": 50, "resistivity_ohm_m": 1.72e-8}
    ]
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(
        injection_node="n1",
        earth_nodes=["n2", "n3"],
        total_injection_current_a=100000.0,
    )
    kc_factors = res["kc_factors"]

    assert "s1" in kc_factors
    assert "s2" in kc_factors
    assert pytest.approx(kc_factors["s1"], 0.05) == 0.5
    assert pytest.approx(kc_factors["s2"], 0.05) == 0.5

def test_rolling_sphere_protection():
    rs_engine = RollingSphereEngine(sphere_radius_m=20.0) # Class I
    res_protected = rs_engine.check_surface_exposure(
        point_x=1.0, point_y=0.0, point_z=10.0,
        rod_x=0.0, rod_y=0.0, rod_height_m=15.0
    )
    assert res_protected["protected"] is True

    res_near_tip_exposed = rs_engine.check_surface_exposure(
        point_x=1.0, point_y=0.0, point_z=14.0,
        rod_x=0.0, rod_y=0.0, rod_height_m=15.0
    )
    assert res_near_tip_exposed["protected"] is False

    res_exposed = rs_engine.check_surface_exposure(
        point_x=22.0, point_y=0.0, point_z=14.0,
        rod_x=0.0, rod_y=0.0, rod_height_m=15.0
    )
    assert res_exposed["protected"] is False

def test_risk_management_engine():
    risk_eng = RiskManagementEngine()
    inp = RiskAssessmentInput(
        structure_length_m=30.0,
        structure_width_m=20.0,
        structure_height_m=15.0,
        ng_flashes_per_km2_year=2.5,
        environmental_cd=1.0,
        lps_class="I",
        fire_risk_rf=0.01,
        has_coordinated_spd=True,
        time_in_structure_hours_per_year=2190.0,
        loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
    )
    res = risk_eng.evaluate_r1_risk(inp)
    assert res.collection_area_ad_m2 > 0
    assert res.annual_strikes_nd > 0
    assert isinstance(res.risk_acceptable, bool)

def test_dxf_exporter():
    dxf_bytes = DXFExporter.export_2d_plan(20.0, 10.0, [{"x": 0, "y": 0}])
    assert isinstance(dxf_bytes, bytes)
    assert len(dxf_bytes) > 100

def test_ifc_importer_interface_stub():
    res = IFCImporter.parse_ifc_building_elements(
        b"ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\nENDSEC;\nEND-ISO-10303-21;\n"
    )
    assert res["parsed"] is True
    assert res["detected_building"]["length_m"] == 25.0
