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
    assert res.pit_inner_diameter_mm >= 250.0
    assert res.backfill_volume_m3 > 0.01
    assert res.number_of_25kg_bags > 0
    assert res.conditioned_resistance_single_rod_ohm < res.unconditioned_resistance_single_rod_ohm
    assert res.resistance_reduction_percentage > 20.0
    assert res.status == "SIZED_AND_VERIFIED"

def test_earth_rod_sizing_multi_material():
    engine = EarthRodSizingEngine()

    # 1. Copper bonded steel (5/8" / 16mm)
    inp_cu_bond = EarthRodSizingInput(
        soil_resistivity_ohm_m=120.0,
        target_resistance_ohm=10.0,
        electrode_material="copper_bonded_steel",
        rod_length_per_unit_m=3.0
    )
    res_cu = engine.size_earth_rod_system(inp_cu_bond)
    assert res_cu.nominal_diameter_mm == 16.0
    assert res_cu.coating_thickness_um >= 250.0
    assert res_cu.inter_rod_spacing_rule_m == 6.0 # 2 * 3m = 6m rule
    assert res_cu.required_number_of_rods >= 2
    assert res_cu.total_array_resistance_ohm <= 10.0
    assert res_cu.target_achieved is True
    assert len(res_cu.recommended_rod_coordinates) == res_cu.required_number_of_rods

    # 2. Galvanized steel (min 20mm per IEC 62561-2)
    inp_galv = EarthRodSizingInput(
        soil_resistivity_ohm_m=80.0,
        target_resistance_ohm=10.0,
        electrode_material="galvanized_steel",
        rod_length_per_unit_m=3.0
    )
    res_galv = engine.size_earth_rod_system(inp_galv)
    assert res_galv.nominal_diameter_mm == 20.0
    assert res_galv.total_array_resistance_ohm <= 10.0
