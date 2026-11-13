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
        conductor_diameter_m=0.01,
        burial_depth_m=0.5,
        peak_impulse_current_ka=100.0,
    )
    res = engine.evaluate_earthing_system(inp)
    # IEC 62305-3:2024 Clause 5.4.2.2 Figure 5: Class I at rho = 100 <= 500 ohm.m -> l1 = 5.0 m.
    assert res.minimum_length_l1_m == 5.0
    # Sanity check only (Type B r_e vs circumference rule is open under C4):
    assert res.actual_effective_length_m > res.minimum_length_l1_m
    # Sanity check only (Sunde ring primary source pending per H5):
    assert res.stationary_resistance_r_ohm > 0
    # Sanity check only (soil-ionization impulse reduction has no primary source in docs/):
    assert res.impulse_impedance_z_ohm <= res.stationary_resistance_r_ohm
    assert res.status == "PASS"

def test_earthing_type_a_vertical_dwight_mutual_coupling():
    engine = EarthingEngine()
    inp = EarthingAssessmentInput(
        lps_class="II",
        soil=SoilLayerModel(rho_upper_ohm_m=200.0),
        electrode_type="type_a_vertical",
        conductor_diameter_m=0.01,
        vertical_rod_length_m=3.0,
        vertical_rod_count=4,
        vertical_rod_spacing_m=5.0,
        peak_impulse_current_ka=100.0,
    )
    res = engine.evaluate_earthing_system(inp)
    assert res.actual_effective_length_m == 12.0
    # Sanity check only (no independent multi-rod reference at s/L = 5/3; see H4):
    assert res.stationary_resistance_r_ohm > 0
    # Sanity check only (soil-ionization impulse efficiency has no primary source in docs/):
    assert res.impulse_efficiency_factor < 1.0

def test_touch_and_step_hazard_control_dalziel():
    engine = TouchStepEngine()
    
    # Non-compliant: Bare soil and accessible down-conductor
    inp_hazard = TouchStepAssessmentInput(
        lps_class="I",
        soil_resistivity_ohm_m=100.0,
        surface_layer_material="bare_soil",
        fault_duration_s=0.05,
        body_weight_kg=70.0,
        peak_impulse_current_ka=100.0,
        down_conductor_radius_m=0.005,
        has_physical_insulation_barrier=False,
        earth_potential_rise_v=10000.0,
        electrode_equivalent_radius_m=2.0,
    )
    res_hazard = engine.evaluate(inp_hazard)
    assert res_hazard.status == "HAZARD_DETECTED"
    assert len(res_hazard.recommended_mitigations) > 0

    # Compliant: High-resistivity asphalt surface layer (C_s derating raises U_touch,tol above prospective)
    inp_safe = TouchStepAssessmentInput(
        lps_class="I",
        soil_resistivity_ohm_m=100.0,
        surface_layer_material="asphalt_5cm",
        surface_layer_resistivity_ohm_m=10000.0,
        fault_duration_s=0.05,
        body_weight_kg=70.0,
        peak_impulse_current_ka=100.0,
        down_conductor_radius_m=0.005,
        has_physical_insulation_barrier=True,
        earth_potential_rise_v=10000.0,
        electrode_equivalent_radius_m=2.0,
    )
    res_safe = engine.evaluate(inp_safe)
    assert res_safe.status == "COMPLIANT"
    assert res_safe.touch_hazard_controlled is True
    assert res_safe.prospective_touch_voltage_v == pytest.approx(10000.0 / 3.0, abs=0.1)

def test_spd_lpz_coordination_advanced():
    """IEC 62305-4:2024 Annex C.2.3 & C.2.5 coordination check.

    With Cat II U_w = 2.5 kV, k_r = 2.0 (U_req = 1.25 kV at U_i = 0.0 kV), and 0.5 m
    connecting leads (C.2.5 limit), spd-1 (U_p = 1.5 kV > 0.5 * U_w) fails Rule 1 and
    spd-2 (U_p/f = 1.2 + 0.1 * 20 * 0.5 = 2.2 kV > 1.25 kV) exceeds U_req, yielding
    voltage_protection_verified=False, status='ACTION_REQUIRED', and L_max=0.0 m.
    """
    engine = SPDCoordinationEngine()
    
    # Cascaded setup: Type 1 at boundary with 15m cable + Type 2 sub-panel (0.5m leads)
    spds = [
        SPDEntry(id="spd-1", spd_class="Type 1", technology="spark_gap", i_imp_ka=25.0, up_kv=1.5, cable_length_to_downstream_m=15.0, lead_length_m=0.5),
        SPDEntry(id="spd-2", spd_class="Type 2", technology="varistor_mov", i_n_ka=20.0, up_kv=1.2, lead_length_m=0.5)
    ]
    # Test fixture: induced voltage not evaluated (lower bound). Not a default.
    equip = EquipmentWithstand(category="Cat II", uw_kv=2.5, induced_voltage_kv=0.0)
    res = engine.evaluate_coordination(spds, equip)
    assert res.energy_coordination_verified is True
    assert res.voltage_protection_verified is False
    assert res.status == "ACTION_REQUIRED"
    assert res.max_connecting_lead_length_m == 0.0

    # Incomplete setup: Missing Type 1
    spds_incomplete = [
        SPDEntry(id="spd-2", spd_class="Type 2", technology="varistor_mov", i_n_ka=20.0, up_kv=1.2)
    ]
    res_inc = engine.evaluate_coordination(spds_incomplete, equip)
    assert res_inc.status == "NON_COMPLIANT"

def test_protective_angle_non_linear_decay():
    engine = ProtectiveAngleEngine()
    # IEC 62305-3:2024 Clause 5.2.2.1 Figure 1 (p. 22) graphical reading (+/-1.5 deg):
    # Class I: alpha(2 m) = 70.0 deg, alpha(18 m) = 27.4 deg.
    angle_2m = engine.get_protective_angle_deg("I", 2.0)
    angle_18m = engine.get_protective_angle_deg("I", 18.0)

    assert angle_2m == pytest.approx(70.0, abs=1.5)
    assert angle_18m == pytest.approx(27.4, abs=1.5)

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
        environmental_cd=1.0,
        lps_class="I",
        fire_risk_rf=0.01,
        has_coordinated_spd=True,
        time_in_structure_hours_per_year=2190.0,
        loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
    )
    res = engine.evaluate_r1_risk(inp)
    # IEC 62305-2:2024 Annex A: A_D = 40*25 + 6*20*65 + 9*pi*400 = 20109.7336 m^2,
    # N_D = 2.5 * A_D * 1.0 * 1e-6 = 0.050274333882 /yr.
    # Tables B.3-B.7 & C.2 (t_z/8760 = 2190/8760 = 0.25):
    # R_B = N_D * 2e-4 * (5e-2 * 0.25) = 1.2568583471e-7
    # R_C = N_D * 0.01 * (5e-4 * 0.25) = 6.2842917353e-8
    assert res.collection_area_ad_m2 == pytest.approx(20109.7, abs=0.1)
    assert res.annual_strikes_nd == pytest.approx(0.050274333882, rel=1e-6)
    assert res.risk_rb_physical_damage == pytest.approx(1.2568583471e-7, rel=1e-6)
    assert res.risk_rc_internal_systems == pytest.approx(6.2842917353e-8, rel=1e-6)
    # Sanity check only (total R1 includes R_A whose P_A factor is open under H3):
    assert res.risk_r1_loss_of_life > 0
    assert res.risk_r1_loss_of_life == pytest.approx(res.risk_ra_touch_step + res.risk_rb_physical_damage + res.risk_rc_internal_systems)
    assert res.risk_acceptable is True
