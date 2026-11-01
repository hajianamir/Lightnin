import pytest
from aegislps_geometry.mesh_method import MeshMethodEngine, MeshMethodInput, RoofProtrusion
from aegislps_engine.hvi_conductor import HVIConductorAssistant, HVIConductorSelectionInput
from aegislps_engine.bom_engine import BOMAndLifecycleEngine

def test_mesh_method_dimensions_class_I():
    engine = MeshMethodEngine()

    # Compliant 5x5m mesh on flat roof with perimeter conductor
    inp_ok = MeshMethodInput(
        lps_class="I",
        mesh_grid_dx_m=5.0,
        mesh_grid_dy_m=5.0,
        has_perimeter_conductor=True,
        protrusions=[]
    )
    res_ok = engine.validate_mesh_design(inp_ok)
    assert res_ok.mesh_size_compliant is True
    assert res_ok.perimeter_conductor_compliant is True
    assert res_ok.is_fully_compliant is True
    assert res_ok.status == "COMPLIANT"

    # Non-compliant 10x10m mesh for Class I (max 5x5m)
    inp_bad = MeshMethodInput(
        lps_class="I",
        mesh_grid_dx_m=10.0,
        mesh_grid_dy_m=10.0,
        has_perimeter_conductor=True,
        protrusions=[RoofProtrusion(id="chimney", x=10, y=10, z=15, height_above_roof_m=1.2)]
    )
    res_bad = engine.validate_mesh_design(inp_bad)
    assert res_bad.mesh_size_compliant is False
    assert res_bad.unprotected_protrusions_count == 1
    assert res_bad.is_fully_compliant is False
    assert res_bad.status == "NON_COMPLIANT_VIOLATION"

def test_hvi_conductor_selection_and_clearance():
    hvi_assistant = HVIConductorAssistant()

    # Adequate model: HVI_standard_90 (s_equiv=0.9m) for required s=0.75m
    inp_good = HVIConductorSelectionInput(
        lps_class="I",
        required_equivalent_separation_s_air_m=0.75,
        down_conductor_route_length_m=20.0,
        hvi_conductor_model="HVI_standard_90"
    )
    res_good = hvi_assistant.evaluate_hvi_selection(inp_good)
    assert res_good.is_adequate_insulation is True
    assert res_good.length_limit_exceeded is False
    assert res_good.status == "COMPLIANT_APPROVED"
    assert res_good.requires_capacitive_sealing_ground is True

    # Inadequate model: HVI_light_75 (s_equiv=0.75m) for required s=0.90m
    inp_inadequate = HVIConductorSelectionInput(
        lps_class="I",
        required_equivalent_separation_s_air_m=0.90,
        down_conductor_route_length_m=20.0,
        hvi_conductor_model="HVI_light_75"
    )
    res_inad = hvi_assistant.evaluate_hvi_selection(inp_inadequate)
    assert res_inad.is_adequate_insulation is False
    assert res_inad.status == "NON_COMPLIANT_HAZARD"

def test_bom_takeoff_and_lifecycle_schedule():
    bom_engine = BOMAndLifecycleEngine()
    bom = bom_engine.generate_project_bom(
        project_name="Data Center LPS",
        lps_class="I",
        building_length_m=40.0,
        building_width_m=25.0,
        building_height_m=12.0
    )
    assert bom.total_components_count > 0
    assert any(i.category == "air_termination" for i in bom.items)
    assert any(i.category == "down_conductor" for i in bom.items)
    assert any(i.category == "earthing" for i in bom.items)
    assert any(i.category == "spd" for i in bom.items)
    # Class I inspection frequency is visual 1 yr, electrical 2 yr
    assert bom.inspection_schedule[0].frequency_years == 1
    assert bom.inspection_schedule[1].frequency_years == 2
