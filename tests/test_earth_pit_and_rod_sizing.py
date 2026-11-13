import pytest
from aegislps_engine.earth_pit import EarthPitEngine, EarthPitSizingInput
from aegislps_engine.earth_rod_sizing import EarthRodSizingEngine, EarthRodSizingInput

def test_earth_pit_sizing_and_gem_backfill():
    engine = EarthPitEngine()
    inp = EarthPitSizingInput(
        is_disconnect_testing_required=True,
        traffic_loading_area="car_park", # Class B125
        electrode_rod_diameter_mm=16.0,
        auger_hole_diameter_mm=100.0,
        treatment_depth_m=3.0,
        enhancement_material="carbon_gem",
        native_soil_resistivity_ohm_m=150.0
    )
    res = engine.evaluate_earth_pit_and_backfill(inp)
    assert res.is_pit_required is True
    assert "B125" in res.en124_load_class
    # Sanity check only (no independent IEC 62561-5 / EN 124 inner-diameter table in docs/):
    assert res.pit_inner_diameter_mm >= 250.0
    # Cylindrical annulus volume V = pi * (r_hole^2 - r_rod^2) * L = pi * (0.05^2 - 0.008^2) * 3.0 = 0.022959 m^3:
    assert res.backfill_volume_m3 == pytest.approx(0.023, abs=1e-3)
    # Dwight single vertical rod R_1 = (150 / (2*pi*3)) * (ln(12 / 0.008) - 1) = 50.2400 ohm:
    assert res.unconditioned_resistance_single_rod_ohm == pytest.approx(50.24, abs=0.01)
    # Sanity check only (backfill density / rho_c values have no primary source in docs/; see M6):
    assert res.number_of_25kg_bags > 0
    assert res.conditioned_resistance_single_rod_ohm < res.unconditioned_resistance_single_rod_ohm
    # Sanity check only (conditioned resistance reduction depends on unsourced rho_c; see M6):
    assert res.resistance_reduction_percentage > 20.0
    assert res.status == "SIZED_AND_VERIFIED"

def test_earth_rod_sizing_multi_material():
    engine = EarthRodSizingEngine()
    
    # 1. Copper bonded steel (5/8" / 16mm)
    inp_cu_bond = EarthRodSizingInput(
        soil_resistivity_ohm_m=120.0,
        target_resistance_ohm=10.0,
        electrode_material="copper_bonded_steel",
        rod_length_per_unit_m=3.0,
        site_boundary_length_m=40.0,
        site_boundary_width_m=25.0,
    )
    res_cu = engine.size_earth_rod_system(inp_cu_bond)
    assert res_cu.nominal_diameter_mm == 16.0
    # IEC 62561-2 Table 1 minimum copper coating thickness for copper-bonded steel is 250 um:
    assert res_cu.coating_thickness_um == 250.0
    assert res_cu.inter_rod_spacing_rule_m == 6.0 # 2 * 3m = 6m rule
    # Dwight single rod: R_1 = (120 / (6*pi)) * (ln(12/0.008) - 1) = 40.1912 ohm;
    # even with zero mutual resistance, R_1 / 4 = 10.0478 > 10.0 ohm requires N >= 5 rods:
    assert res_cu.single_rod_resistance_ohm == pytest.approx(40.19, abs=0.01)
    assert res_cu.required_number_of_rods == 5
    # Sanity check only (multi-rod array mutual-coupling primary source pending per H4; checks target <= 10 ohm):
    assert res_cu.total_array_resistance_ohm <= 10.0
    assert res_cu.target_achieved is True
    assert len(res_cu.recommended_rod_coordinates) == res_cu.required_number_of_rods

    # 2. Galvanized steel (min 20mm per IEC 62561-2)
    inp_galv = EarthRodSizingInput(
        soil_resistivity_ohm_m=80.0,
        target_resistance_ohm=10.0,
        electrode_material="galvanized_steel",
        rod_length_per_unit_m=3.0,
        site_boundary_length_m=40.0,
        site_boundary_width_m=25.0,
    )
    res_galv = engine.size_earth_rod_system(inp_galv)
    assert res_galv.nominal_diameter_mm == 20.0
    # Dwight single rod: R_1 = (80 / (6*pi)) * (ln(12/0.010) - 1) = 25.8471 ohm:
    assert res_galv.single_rod_resistance_ohm == pytest.approx(25.85, abs=0.01)
    # Sanity check only (multi-rod array mutual-coupling primary source pending per H4; checks target <= 10 ohm):
    assert res_galv.total_array_resistance_ohm <= 10.0
