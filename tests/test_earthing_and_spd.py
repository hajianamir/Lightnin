import pytest
from aegislps_engine.earthing import EarthingEngine, EarthingAssessmentInput, SoilLayerModel
from aegislps_engine.touch_step import TouchStepEngine, TouchStepAssessmentInput
from aegislps_engine.spd_coordination import SPDCoordinationEngine, SPDEntry, EquipmentWithstand
from aegislps_geometry.protective_angle import ProtectiveAngleEngine
from aegislps_engine.risk import RiskManagementEngine, RiskAssessmentInput

def test_earthing_type_b_ring_dwight():
    engine = EarthingEngine()
    inp = EarthingAssessmentInput(
        lps_class="I",
        soil=SoilLayerModel(rho_upper_ohm_m=100.0),
        electrode_type="type_b_ring",
        ring_radius_m=15.0,
        burial_depth_m=0.5
    )
    res = engine.evaluate_earthing_system(inp)
    assert res.minimum_length_l1_m > 0
    assert res.actual_effective_length_m > res.minimum_length_l1_m
    assert res.stationary_resistance_r_ohm > 0
    assert res.impulse_impedance_z_ohm <= res.stationary_resistance_r_ohm
    assert res.status == "PASS"

def test_earthing_type_a_vertical_dwight_mutual_coupling():
    engine = EarthingEngine()
    inp = EarthingAssessmentInput(
        lps_class="II",
        soil=SoilLayerModel(rho_upper_ohm_m=200.0),
        electrode_type="type_a_vertical",
        vertical_rod_length_m=3.0,
        vertical_rod_count=4,
        vertical_rod_spacing_m=5.0
    )
    res = engine.evaluate_earthing_system(inp)
    assert res.actual_effective_length_m == 12.0
    assert res.stationary_resistance_r_ohm > 0
    assert res.impulse_efficiency_factor < 1.0

def test_touch_and_step_hazard_control_dalziel():
    engine = TouchStepEngine()

    # Non-compliant: Bare soil and accessible down-conductor
    inp_hazard = TouchStepAssessmentInput(
        soil_resistivity_ohm_m=100.0,
        surface_layer_material="bare_soil",
        has_physical_insulation_barrier=False
    )
    res_hazard = engine.evaluate(inp_hazard)
    assert res_hazard.status == "HAZARD_DETECTED"
    assert len(res_hazard.recommended_mitigations) > 0

    # Compliant: High-resistivity asphalt surface layer and insulated barrier
    inp_safe = TouchStepAssessmentInput(
        soil_resistivity_ohm_m=100.0,
        surface_layer_material="asphalt_5cm",
        has_physical_insulation_barrier=True
    )
    res_safe = engine.evaluate(inp_safe)
    assert res_safe.status == "COMPLIANT"
    assert res_safe.touch_hazard_controlled is True
    assert res_safe.prospective_touch_voltage_v == 0.0

def test_spd_lpz_coordination_advanced():
    engine = SPDCoordinationEngine()

    # Coordinated setup: Type 1 at boundary with 15m cable + Type 2 sub-panel
    spds = [
        SPDEntry(id="spd-1", spd_class="Type 1", technology="spark_gap", i_imp_ka=25.0, up_kv=1.5, cable_length_to_downstream_m=15.0),
        SPDEntry(id="spd-2", spd_class="Type 2", technology="varistor_mov", i_n_ka=20.0, up_kv=1.2)
    ]
    equip = EquipmentWithstand(category="Cat II", uw_kv=2.5)
    res = engine.evaluate_coordination(spds, equip)
    assert res.energy_coordination_verified is True
    assert res.voltage_protection_verified is True
    assert res.status == "COORDINATED"
    assert res.effective_protection_distance_m >= 10.0

    # Incomplete setup: Missing Type 1
    spds_incomplete = [
        SPDEntry(id="spd-2", spd_class="Type 2", technology="varistor_mov", i_n_ka=20.0, up_kv=1.2)
    ]
    res_inc = engine.evaluate_coordination(spds_incomplete, equip)
    assert res_inc.status == "NON_COMPLIANT"

def test_protective_angle_non_linear_decay():
    engine = ProtectiveAngleEngine()
    # Height H=2m -> large angle ~70 deg
    angle_2m = engine.get_protective_angle_deg("I", 2.0)
    # Height H=18m -> steep angle ~25 deg
    angle_18m = engine.get_protective_angle_deg("I", 18.0)

    assert angle_2m > angle_18m
    assert 60.0 <= angle_2m <= 75.0
    assert 20.0 <= angle_18m <= 35.0

    # Exceeding 20m for Class I -> not applicable
    res_exceed = engine.check_object_in_cone(
        lps_class="I",
        rod_tip_x=0, rod_tip_y=0, rod_tip_z=35,
        ref_plane_z=10, # H = 25m > 20m limit
        object_x=1, object_y=1, object_z=12
    )
    assert res_exceed["applicable"] is False

def test_iec62305_2_risk_components():
    engine = RiskManagementEngine()
    inp = RiskAssessmentInput(
        structure_length_m=40.0,
        structure_width_m=25.0,
        structure_height_m=20.0,
        ng_flashes_per_km2_year=2.5,
        lps_class="I",
        has_coordinated_spd=True
    )
    res = engine.evaluate_r1_risk(inp)
    assert res.collection_area_ad_m2 > 0
    assert res.risk_r1_loss_of_life > 0
    assert res.risk_r1_loss_of_life == pytest.approx(res.risk_ra_touch_step + res.risk_rb_physical_damage + res.risk_rc_internal_systems)
    assert res.risk_acceptable is True
