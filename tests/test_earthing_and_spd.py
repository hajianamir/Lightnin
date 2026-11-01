import pytest
from aegislps_engine.earthing import EarthingEngine, EarthingAssessmentInput
from aegislps_engine.touch_step import TouchStepEngine, TouchStepAssessmentInput
from aegislps_engine.spd_coordination import SPDCoordinationEngine, SPDSpecification
from aegislps_geometry.protective_angle import ProtectiveAngleEngine

def test_earthing_type_b_ring():
    engine = EarthingEngine()
    inp = EarthingAssessmentInput(
        lps_class="I",
        soil_resistivity_ohm_m=100.0,
        electrode_type="type_b_ring",
        ring_radius_m=15.0
    )
    res = engine.evaluate_earthing_system(inp)
    assert res.minimum_length_l1_m > 0
    assert res.actual_effective_length_m > res.minimum_length_l1_m
    assert res.calculated_resistance_ohm < 10.0 # R ~ 100 / (2*30) = 1.67 ohm
    assert res.status == "PASS"

def test_earthing_type_a_vertical():
    engine = EarthingEngine()
    inp = EarthingAssessmentInput(
        lps_class="II",
        soil_resistivity_ohm_m=200.0,
        electrode_type="type_a_vertical",
        rod_length_m=3.0,
        rod_count=4
    )
    res = engine.evaluate_earthing_system(inp)
    assert res.actual_effective_length_m == 12.0
    assert res.calculated_resistance_ohm > 0

def test_touch_and_step_hazard_control():
    engine = TouchStepEngine()

    # Non-compliant: Bare soil and accessible down-conductor
    inp_hazard = TouchStepAssessmentInput(soil_surface_type="bare_soil", conductor_accessible=True, has_insulation_barrier=False)
    res_hazard = engine.evaluate(inp_hazard)
    assert res_hazard.status == "ACTION_REQUIRED"
    assert len(res_hazard.recommended_mitigations) > 0

    # Compliant: Asphalt surface layer and insulated barrier
    inp_safe = TouchStepAssessmentInput(soil_surface_type="asphalt_5cm", conductor_accessible=True, has_insulation_barrier=True)
    res_safe = engine.evaluate(inp_safe)
    assert res_safe.status == "COMPLIANT"
    assert res_safe.touch_hazard_controlled is True

def test_spd_lpz_coordination():
    engine = SPDCoordinationEngine()

    # Coordinated setup: Type 1 at boundary + Type 2 sub-panel
    spds = [
        SPDSpecification(id="spd-1", spd_type="Type 1", i_imp_ka=25.0, up_kv=1.5),
        SPDSpecification(id="spd-2", spd_type="Type 2", i_n_ka=20.0, up_kv=1.2)
    ]
    res = engine.evaluate_coordination(spds)
    assert res.coordination_verified is True
    assert res.status == "COORDINATED"

    # Incomplete setup: Missing Type 1
    spds_incomplete = [
        SPDSpecification(id="spd-2", spd_type="Type 2", i_n_ka=20.0, up_kv=1.2)
    ]
    res_inc = engine.evaluate_coordination(spds_incomplete)
    assert res_inc.coordination_verified is False
    assert res_inc.status == "INCOMPLETE"

def test_protective_angle_cone():
    engine = ProtectiveAngleEngine()
    # Class I rod, 5m height above roof
    angle = engine.get_protective_angle_deg("I", 5.0)
    assert 50.0 <= angle <= 75.0

    # Object close to rod base -> protected
    res = engine.check_object_in_cone(
        lps_class="I",
        rod_tip_x=0.0, rod_tip_y=0.0, rod_tip_z=20.0,
        ref_plane_z=15.0, # 5m rod
        object_x=1.5, object_y=1.5, object_z=15.5
    )
    assert res["protected"] is True
    assert res["clearance_margin_m"] > 0
