"""Comprehensive validation, unclamping, invariance, and HTTP tests for Step 2.7-B3 (H9)."""

import math
import pytest
from fastapi.testclient import TestClient

from aegislps_api.main import app
from aegislps_engine.diagnostics import SystemDiagnostics
from aegislps_engine.earth_pit import EarthPitEngine, EarthPitSizingInput
from aegislps_engine.earth_rod_sizing import EarthRodSizingEngine, EarthRodSizingInput
from aegislps_engine.earthing import (
    LPL_FIRST_POSITIVE_PEAK_CURRENT_KA,
    EarthingAssessmentInput,
    EarthingEngine,
    SoilLayerModel,
)
from aegislps_engine.spd_coordination import (
    EquipmentWithstand,
    SPDCoordinationEngine,
    SPDEntry,
)

client = TestClient(app)


def _valid_ring_kwargs() -> dict:
    return {
        "lps_class": "I",
        "soil": SoilLayerModel(rho_upper_ohm_m=100.0),
        "electrode_type": "type_b_ring",
        "ring_radius_m": 15.0,
        "conductor_diameter_m": 0.01,
        "burial_depth_m": 0.5,
        "peak_impulse_current_ka": 100.0,
    }


def _valid_earth_pit_kwargs() -> dict:
    return {
        "is_disconnect_testing_required": True,
        "traffic_loading_area": "pedestrian",
        "electrode_rod_diameter_mm": 16.0,
        "auger_hole_diameter_mm": 100.0,
        "treatment_depth_m": 3.0,
        "enhancement_material": "carbon_gem",
        "native_soil_resistivity_ohm_m": 150.0,
    }


def _valid_earth_rod_kwargs() -> dict:
    return {
        "lps_class": "I",
        "soil_resistivity_ohm_m": 120.0,
        "target_resistance_ohm": 10.0,
        "electrode_material": "copper_bonded_steel",
        "rod_length_per_unit_m": 3.0,
        "min_distance_to_building_foundation_m": 1.0,
        "site_boundary_length_m": 40.0,
        "site_boundary_width_m": 25.0,
    }


# ---------------------------------------------------------------------------
# Module A: earthing.py (Rules A.1 - A.13 + Decisions 1, 3, 6, 7, 8)
# ---------------------------------------------------------------------------


def test_a1_a2_lps_class_and_soil_required_and_validated():
    for cls in ("I", "II", "III", "IV"):
        inp = EarthingAssessmentInput(**{**_valid_ring_kwargs(), "lps_class": cls})
        assert inp.lps_class == cls

    no_cls = _valid_ring_kwargs()
    no_cls.pop("lps_class")
    with pytest.raises(ValueError):
        EarthingAssessmentInput(**no_cls)

    for bad_cls in ("V", "i", "", None, 1, True):
        with pytest.raises(ValueError):
            EarthingAssessmentInput(**{**_valid_ring_kwargs(), "lps_class": bad_cls})

    no_soil = _valid_ring_kwargs()
    no_soil.pop("soil")
    with pytest.raises(ValueError):
        EarthingAssessmentInput(**no_soil)
    with pytest.raises(ValueError):
        EarthingAssessmentInput(**{**_valid_ring_kwargs(), "soil": None})


def test_a3_a4_a5_soil_layer_model_validation_and_unclamped():
    # Single-layer default is_two_layer=False
    s_single = SoilLayerModel(rho_upper_ohm_m=100.0)
    assert s_single.is_two_layer is False
    assert s_single.h_upper_m is None
    assert s_single.rho_lower_ohm_m is None

    # Strict bool on is_two_layer
    for bad_bool in ("false", "true", 0, 1, None):
        with pytest.raises(ValueError):
            SoilLayerModel(is_two_layer=bad_bool, rho_upper_ohm_m=100.0)  # type: ignore[arg-type]

    # rho_upper_ohm_m required, finite, > 0, not bool
    with pytest.raises(ValueError):
        SoilLayerModel()  # type: ignore[call-arg]
    for bad_rho in (0.0, -5.0, float("nan"), float("inf"), -float("inf"), True, False):
        with pytest.raises(ValueError):
            SoilLayerModel(rho_upper_ohm_m=bad_rho)

    # Two-layer requires h_upper_m and rho_lower_ohm_m
    with pytest.raises(ValueError, match="h_upper_m"):
        SoilLayerModel(is_two_layer=True, rho_upper_ohm_m=100.0, rho_lower_ohm_m=300.0)
    with pytest.raises(ValueError, match="rho_lower_ohm_m"):
        SoilLayerModel(is_two_layer=True, rho_upper_ohm_m=100.0, h_upper_m=1.5)

    for bad_val in (0.0, -1.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            SoilLayerModel(
                is_two_layer=True,
                rho_upper_ohm_m=100.0,
                h_upper_m=bad_val,
                rho_lower_ohm_m=300.0,
            )
        with pytest.raises(ValueError):
            SoilLayerModel(
                is_two_layer=True,
                rho_upper_ohm_m=100.0,
                h_upper_m=1.5,
                rho_lower_ohm_m=bad_val,
            )

    # Unclamped check: rho1=0.4 (< 1.0), rho2=0.8 (< 1.0), h=0.05 (< 0.1) are NOT clamped
    s_unclamped = SoilLayerModel(
        is_two_layer=True,
        rho_upper_ohm_m=0.4,
        h_upper_m=0.05,
        rho_lower_ohm_m=0.8,
    )
    rho_app = EarthingEngine.calculate_apparent_resistivity(s_unclamped, 0.5)
    k = (0.8 - 0.4) / (0.8 + 0.4)
    expected_app = 0.4 * (1.0 + k * (1.0 - math.exp(-1.8 * (0.5 / 0.05))))
    assert rho_app == pytest.approx(expected_app, rel=1e-12)
    assert rho_app < 1.0  # Would have been >= 1.0 under old max(1.0, rho1) clamp


def test_a6_a7_electrode_type_and_ring_radius_validation_and_unclamped():
    no_type = _valid_ring_kwargs()
    no_type.pop("electrode_type")
    with pytest.raises(ValueError):
        EarthingAssessmentInput(**no_type)

    # Unknown electrode_type raises ValueError (no silent fallback to foundation)
    for bad_type in ("mesh", "ring", "vertical", "", None, 1):
        with pytest.raises(ValueError):
            EarthingAssessmentInput(**{**_valid_ring_kwargs(), "electrode_type": bad_type})

    # ring_radius_m required for type_b_ring
    no_ring = _valid_ring_kwargs()
    no_ring.pop("ring_radius_m")
    with pytest.raises(ValueError, match="ring_radius_m"):
        EarthingAssessmentInput(**no_ring)
    for bad_r in (0.0, -1.0, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            EarthingAssessmentInput(**{**_valid_ring_kwargs(), "ring_radius_m": bad_r})

    # Unclamped ring_radius_m < 1.0 m (0.4 m != clamped 1.0 m)
    res_04 = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(**{**_valid_ring_kwargs(), "ring_radius_m": 0.4})
    )
    res_10 = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(**{**_valid_ring_kwargs(), "ring_radius_m": 1.0})
    )
    assert res_04.stationary_resistance_r_ohm > res_10.stationary_resistance_r_ohm


def test_a8_a9_conductor_diameter_required_and_burial_depth_default():
    # A.8 / Decision 6: conductor_diameter_m required (no default), unclamped below 2e-4 m
    no_dia = _valid_ring_kwargs()
    no_dia.pop("conductor_diameter_m")
    with pytest.raises(ValueError):
        EarthingAssessmentInput(**no_dia)
    for bad_d in (0.0, -0.01, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            EarthingAssessmentInput(**{**_valid_ring_kwargs(), "conductor_diameter_m": bad_d})

    res_thin = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(**{**_valid_ring_kwargs(), "conductor_diameter_m": 1e-4})
    )
    res_2e4 = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(**{**_valid_ring_kwargs(), "conductor_diameter_m": 2e-4})
    )
    assert res_thin.stationary_resistance_r_ohm > res_2e4.stationary_resistance_r_ohm

    # A.9 / Decision 7: burial_depth_m defaults to 0.5 m (Clause 5.4.3); > 0 allowed (< 0.5 does NOT raise)
    omitted_depth = _valid_ring_kwargs()
    omitted_depth.pop("burial_depth_m")
    inp_default_depth = EarthingAssessmentInput(**omitted_depth)
    assert inp_default_depth.burial_depth_m == 0.5

    inp_shallow = EarthingAssessmentInput(**{**_valid_ring_kwargs(), "burial_depth_m": 0.03})
    res_shallow = EarthingEngine().evaluate_earthing_system(inp_shallow)
    res_01 = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(**{**_valid_ring_kwargs(), "burial_depth_m": 0.1})
    )
    assert res_shallow.stationary_resistance_r_ohm > res_01.stationary_resistance_r_ohm

    for bad_h in (0.0, -0.2, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            EarthingAssessmentInput(**{**_valid_ring_kwargs(), "burial_depth_m": bad_h})


def test_a10_type_a_vertical_requires_at_least_two_rods_and_unclamped():
    base_vert = {
        "lps_class": "I",
        "soil": SoilLayerModel(rho_upper_ohm_m=100.0),
        "electrode_type": "type_a_vertical",
        "conductor_diameter_m": 0.01,
        "vertical_rod_length_m": 3.0,
        "vertical_rod_count": 2,
        "vertical_rod_spacing_m": 5.0,
        "peak_impulse_current_ka": 100.0,
    }
    res_ok = EarthingEngine().evaluate_earthing_system(EarthingAssessmentInput(**base_vert))
    assert res_ok.actual_effective_length_m == 6.0

    # Missing any of the three vertical rod parameters raises ValueError
    for field_name in ("vertical_rod_length_m", "vertical_rod_count", "vertical_rod_spacing_m"):
        missing = dict(base_vert)
        missing.pop(field_name)
        with pytest.raises(ValueError, match=field_name):
            EarthingAssessmentInput(**missing)

    # Decision 1 (IEC 62305-3:2024 Clause 5.4.2.2): vertical_rod_count < 2 raises ValueError
    for bad_count in (1, 0, -1, 2.5, True, False, "2"):
        with pytest.raises(ValueError):
            EarthingAssessmentInput(**{**base_vert, "vertical_rod_count": bad_count})  # type: ignore[arg-type]

    for bad_num in (0.0, -1.0, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            EarthingAssessmentInput(**{**base_vert, "vertical_rod_length_m": bad_num})
        with pytest.raises(ValueError):
            EarthingAssessmentInput(**{**base_vert, "vertical_rod_spacing_m": bad_num})

    # Unclamped below 0.5 m length and spacing
    res_short = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(
            **{**base_vert, "vertical_rod_length_m": 0.3, "vertical_rod_spacing_m": 0.3}
        )
    )
    assert res_short.actual_effective_length_m == pytest.approx(0.6)


def test_a11_foundation_parameters_required_and_unclamped():
    base_found = {
        "lps_class": "I",
        "soil": SoilLayerModel(rho_upper_ohm_m=100.0),
        "electrode_type": "foundation",
        "conductor_diameter_m": 0.01,
        "foundation_perimeter_m": 4.0,
        "foundation_area_m2": 1.0,
        "peak_impulse_current_ka": 100.0,
    }
    # Unclamped below 10.0 m / 10.0 m^2
    res = EarthingEngine().evaluate_earthing_system(EarthingAssessmentInput(**base_found))
    r_equiv = math.sqrt(1.0 / math.pi)
    expected_r = (100.0 / (4.0 * r_equiv)) + (100.0 / 4.0)
    assert res.stationary_resistance_r_ohm == round(expected_r, 2)
    assert res.actual_effective_length_m == 4.0

    for field_name in ("foundation_perimeter_m", "foundation_area_m2"):
        missing = dict(base_found)
        missing.pop(field_name)
        with pytest.raises(ValueError, match=field_name):
            EarthingAssessmentInput(**missing)
        for bad_val in (0.0, -5.0, float("nan"), float("inf"), True):
            with pytest.raises(ValueError):
                EarthingAssessmentInput(**{**base_found, field_name: bad_val})


def test_a12_peak_impulse_current_derived_from_table_3_and_unclamped():
    assert LPL_FIRST_POSITIVE_PEAK_CURRENT_KA == {
        "I": 200.0,
        "II": 150.0,
        "III": 100.0,
        "IV": 100.0,
    }
    for cls, expected_ka in (("I", 200.0), ("II", 150.0), ("III", 100.0), ("IV", 100.0)):
        kw = _valid_ring_kwargs()
        kw.pop("peak_impulse_current_ka")
        kw["lps_class"] = cls
        inp = EarthingAssessmentInput(**kw)
        assert inp.peak_impulse_current_ka == expected_ka

    # Explicit override > 0 (including < 1.0 kA, proving max(1e3, ...) clamp is removed)
    res_02ka = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(**{**_valid_ring_kwargs(), "peak_impulse_current_ka": 0.2})
    )
    res_1ka = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(**{**_valid_ring_kwargs(), "peak_impulse_current_ka": 1.0})
    )
    assert res_02ka.impulse_efficiency_factor > res_1ka.impulse_efficiency_factor

    for bad_i in (0.0, -10.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            EarthingAssessmentInput(
                **{**_valid_ring_kwargs(), "peak_impulse_current_ka": bad_i}
            )


# ---------------------------------------------------------------------------
# Module B: spd_coordination.py (Rules B.1 - B.9)
# ---------------------------------------------------------------------------


def test_b1_to_b5_and_b8_spd_entry_required_fields_and_metadata():
    # Valid Type 1 spark_gap, Type 1 varistor_mov (no cable_length required), Type 2, Type 3
    t1_sg = SPDEntry(
        id="t1-sg",
        spd_class="Type 1",
        technology="spark_gap",
        i_imp_ka=25.0,
        up_kv=1.2,
        cable_length_to_downstream_m=15.0,
    )
    assert t1_sg.uc_volts == 275.0
    assert t1_sg.installed_lpz_boundary == "LPZ 0B / 1"

    t1_mov = SPDEntry(
        id="t1-mov",
        spd_class="Type 1",
        technology="varistor_mov",
        i_imp_ka=25.0,
        up_kv=1.2,
    )
    assert t1_mov.cable_length_to_downstream_m is None

    t2 = SPDEntry(
        id="t2", spd_class="Type 2", technology="varistor_mov", i_n_ka=20.0, up_kv=1.0
    )
    t3 = SPDEntry(
        id="t3", spd_class="Type 3", technology="hybrid", i_n_ka=5.0, up_kv=0.8, uc_volts=None
    )
    assert t2.i_imp_ka is None and t3.uc_volts is None

    # B.1: technology required & validated
    with pytest.raises(ValueError):
        SPDEntry(id="s", spd_class="Type 2", i_n_ka=20.0, up_kv=1.2)  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        SPDEntry(id="s", spd_class="Type 2", technology="avalanche_diode", i_n_ka=20.0, up_kv=1.2)

    # B.2: up_kv required & > 0
    with pytest.raises(ValueError):
        SPDEntry(id="s", spd_class="Type 2", technology="varistor_mov", i_n_ka=20.0)  # type: ignore[call-arg]
    for bad_up in (0.0, -1.0, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            SPDEntry(
                id="s", spd_class="Type 2", technology="varistor_mov", i_n_ka=20.0, up_kv=bad_up
            )

    # B.3: i_n_ka required for Type 2 & Type 3, > 0
    for cls in ("Type 2", "Type 3"):
        with pytest.raises(ValueError, match="i_n_ka"):
            SPDEntry(id="s", spd_class=cls, technology="varistor_mov", up_kv=1.2)
        for bad_in in (0.0, -5.0, float("nan"), float("inf"), True):
            with pytest.raises(ValueError):
                SPDEntry(
                    id="s", spd_class=cls, technology="varistor_mov", i_n_ka=bad_in, up_kv=1.2
                )

    # B.4: i_imp_ka required for Type 1, > 0
    with pytest.raises(ValueError, match="i_imp_ka"):
        SPDEntry(
            id="s",
            spd_class="Type 1",
            technology="spark_gap",
            up_kv=1.2,
            cable_length_to_downstream_m=10.0,
        )
    for bad_iimp in (0.0, -5.0, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            SPDEntry(
                id="s",
                spd_class="Type 1",
                technology="varistor_mov",
                i_imp_ka=bad_iimp,
                up_kv=1.2,
            )

    # B.5: cable_length_to_downstream_m required for Type 1 spark_gap, >= 0
    with pytest.raises(ValueError, match="cable_length_to_downstream_m"):
        SPDEntry(
            id="s", spd_class="Type 1", technology="spark_gap", i_imp_ka=25.0, up_kv=1.2
        )
    assert (
        SPDEntry(
            id="s0",
            spd_class="Type 1",
            technology="spark_gap",
            i_imp_ka=25.0,
            up_kv=1.2,
            cable_length_to_downstream_m=0.0,
        ).cable_length_to_downstream_m
        == 0.0
    )
    for bad_cab in (-0.1, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            SPDEntry(
                id="s",
                spd_class="Type 1",
                technology="spark_gap",
                i_imp_ka=25.0,
                up_kv=1.2,
                cable_length_to_downstream_m=bad_cab,
            )

    # B.8: uc_volts > 0 if present
    for bad_uc in (0.0, -275.0, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            SPDEntry(
                id="s",
                spd_class="Type 2",
                technology="varistor_mov",
                i_n_ka=20.0,
                up_kv=1.2,
                uc_volts=bad_uc,
            )


def test_b6_b7_b9_equipment_withstand_and_coordination_formulas():
    # B.6: uw_kv required & > 0
    with pytest.raises(ValueError):
        EquipmentWithstand(induced_voltage_kv=0.0)  # type: ignore[call-arg]
    for bad_uw in (0.0, -2.5, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            EquipmentWithstand(uw_kv=bad_uw, induced_voltage_kv=0.0)

    # B.7: category validated in {"Cat I", "Cat II", "Cat III", "Cat IV"}
    for cat in ("Cat I", "Cat II", "Cat III", "Cat IV"):
        eq = EquipmentWithstand(category=cat, uw_kv=2.5, induced_voltage_kv=0.0)
        assert eq.category == cat
    for bad_cat in ("Cat V", "II", "", None, 2):
        with pytest.raises(ValueError):
            EquipmentWithstand(category=bad_cat, uw_kv=2.5, induced_voltage_kv=0.0)  # type: ignore[arg-type]

    # B.9: coordination with Type 1 MOV (no cable_length) + Type 2 MOV
    res = SPDCoordinationEngine().evaluate_coordination(
        [
            SPDEntry(
                id="t1-mov",
                spd_class="Type 1",
                technology="varistor_mov",
                i_imp_ka=25.0,
                up_kv=1.2,
            ),
            SPDEntry(
                id="t2",
                spd_class="Type 2",
                technology="varistor_mov",
                i_n_ka=10.0,
                up_kv=1.0,
            ),
        ],
        EquipmentWithstand(uw_kv=4.0, induced_voltage_kv=0.0),
    )
    assert res.status == "COORDINATED"
    assert any("k_r = 2.0" in w for w in res.warnings)
    assert any("lead_length_m not specified" in w for w in res.warnings)


# ---------------------------------------------------------------------------
# Module C: earth_pit.py (Rules C.1 - C.4 + Decision 4)
# ---------------------------------------------------------------------------


def test_c1_to_c4_earth_pit_validation_and_unclamped():
    # Default is_disconnect_testing_required=True (Clause 5.3.6)
    kw_no_disc = _valid_earth_pit_kwargs()
    kw_no_disc.pop("is_disconnect_testing_required")
    inp_def = EarthPitSizingInput(**kw_no_disc)
    assert inp_def.is_disconnect_testing_required is True

    inp_false = EarthPitSizingInput(
        **{**_valid_earth_pit_kwargs(), "is_disconnect_testing_required": False}
    )
    assert EarthPitEngine().evaluate_earth_pit_and_backfill(inp_false).is_pit_required is False

    # C.4: strict bool
    for bad_bool in (1, 0, "true", None):
        with pytest.raises(ValueError):
            EarthPitSizingInput(
                **{**_valid_earth_pit_kwargs(), "is_disconnect_testing_required": bad_bool}
            )

    # C.1: traffic_loading_area required & validated
    for area in ("pedestrian", "car_park", "roadway_heavy"):
        res_area = EarthPitEngine().evaluate_earth_pit_and_backfill(
            EarthPitSizingInput(**{**_valid_earth_pit_kwargs(), "traffic_loading_area": area})
        )
        assert res_area.status == "SIZED_AND_VERIFIED"
    no_area = _valid_earth_pit_kwargs()
    no_area.pop("traffic_loading_area")
    with pytest.raises(ValueError):
        EarthPitSizingInput(**no_area)
    for bad_area in ("highway", "", None, 1):
        with pytest.raises(ValueError):
            EarthPitSizingInput(**{**_valid_earth_pit_kwargs(), "traffic_loading_area": bad_area})

    # C.2: numeric fields required, > 0, auger > rod, unclamped depth < 0.5 & rho < 5.0
    for field_name in (
        "electrode_rod_diameter_mm",
        "auger_hole_diameter_mm",
        "treatment_depth_m",
        "native_soil_resistivity_ohm_m",
    ):
        missing = _valid_earth_pit_kwargs()
        missing.pop(field_name)
        with pytest.raises(ValueError):
            EarthPitSizingInput(**missing)
        for bad_val in (0.0, -5.0, float("nan"), float("inf"), True):
            with pytest.raises(ValueError):
                EarthPitSizingInput(**{**_valid_earth_pit_kwargs(), field_name: bad_val})

    for bad_auger in (16.0, 10.0):
        with pytest.raises(ValueError, match="auger_hole_diameter_mm"):
            EarthPitSizingInput(
                **{
                    **_valid_earth_pit_kwargs(),
                    "electrode_rod_diameter_mm": 16.0,
                    "auger_hole_diameter_mm": bad_auger,
                }
            )

    res_unclamped = EarthPitEngine().evaluate_earth_pit_and_backfill(
        EarthPitSizingInput(
            **{
                **_valid_earth_pit_kwargs(),
                "treatment_depth_m": 0.2,
                "native_soil_resistivity_ohm_m": 2.0,
            }
        )
    )
    res_clamped_ref = EarthPitEngine().evaluate_earth_pit_and_backfill(
        EarthPitSizingInput(
            **{
                **_valid_earth_pit_kwargs(),
                "treatment_depth_m": 0.5,
                "native_soil_resistivity_ohm_m": 5.0,
            }
        )
    )
    assert res_unclamped.backfill_volume_m3 < res_clamped_ref.backfill_volume_m3

    # C.3: enhancement_material required & in BACKFILL_PROPERTIES
    for mat in EarthPitEngine.BACKFILL_PROPERTIES:
        assert (
            EarthPitEngine()
            .evaluate_earth_pit_and_backfill(
                EarthPitSizingInput(**{**_valid_earth_pit_kwargs(), "enhancement_material": mat})
            )
            .backfill_material
            == mat
        )
    no_mat = _valid_earth_pit_kwargs()
    no_mat.pop("enhancement_material")
    with pytest.raises(ValueError):
        EarthPitSizingInput(**no_mat)
    for bad_mat in ("conductive_cement_gem", "unknown", "", None):
        with pytest.raises(ValueError):
            EarthPitSizingInput(**{**_valid_earth_pit_kwargs(), "enhancement_material": bad_mat})


# ---------------------------------------------------------------------------
# Module D: earth_rod_sizing.py (Rules D.1 - D.5 + Decision 5)
# ---------------------------------------------------------------------------


def test_d1_to_d5_earth_rod_sizing_validation_and_unclamped():
    # Defaults retained: lps_class="I", target_resistance_ohm=10.0, min_distance_to_building_foundation_m=1.0
    minimal = {
        "soil_resistivity_ohm_m": 120.0,
        "electrode_material": "copper_bonded_steel",
        "rod_length_per_unit_m": 3.0,
        "site_boundary_length_m": 40.0,
        "site_boundary_width_m": 25.0,
    }
    inp_min = EarthRodSizingInput(**minimal)
    assert inp_min.lps_class == "I"
    assert inp_min.target_resistance_ohm == 10.0
    assert inp_min.min_distance_to_building_foundation_m == 1.0

    # Decision 5: lps_class validated in {"I", "II", "III", "IV"}
    for cls in ("I", "II", "III", "IV"):
        assert EarthRodSizingInput(**{**minimal, "lps_class": cls}).lps_class == cls
    for bad_cls in ("V", "i", "", None, 1):
        with pytest.raises(ValueError):
            EarthRodSizingInput(**{**minimal, "lps_class": bad_cls})  # type: ignore[arg-type]

    # D.1 & D.2: strictly positive numeric fields
    for req_field in (
        "soil_resistivity_ohm_m",
        "rod_length_per_unit_m",
        "site_boundary_length_m",
        "site_boundary_width_m",
    ):
        missing = dict(minimal)
        missing.pop(req_field)
        with pytest.raises(ValueError):
            EarthRodSizingInput(**missing)

    for pos_field in (
        "soil_resistivity_ohm_m",
        "target_resistance_ohm",
        "rod_length_per_unit_m",
        "site_boundary_length_m",
        "site_boundary_width_m",
    ):
        for bad_val in (0.0, -2.0, float("nan"), float("inf"), True):
            with pytest.raises(ValueError):
                EarthRodSizingInput(**{**_valid_earth_rod_kwargs(), pos_field: bad_val})

    # D.3: min_distance_to_building_foundation_m >= 0 (0.0 allowed; < 0 rejected)
    res_zero_setback = EarthRodSizingEngine().size_earth_rod_system(
        EarthRodSizingInput(
            **{**_valid_earth_rod_kwargs(), "min_distance_to_building_foundation_m": 0.0}
        )
    )
    assert res_zero_setback.recommended_rod_coordinates[0] == (-20.0, -12.5)
    for bad_sb in (-0.1, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            EarthRodSizingInput(
                **{**_valid_earth_rod_kwargs(), "min_distance_to_building_foundation_m": bad_sb}
            )

    # D.4: electrode_material required & in IEC_62561_2_SPECS
    for mat in EarthRodSizingEngine.IEC_62561_2_SPECS:
        assert (
            EarthRodSizingEngine()
            .size_earth_rod_system(
                EarthRodSizingInput(**{**_valid_earth_rod_kwargs(), "electrode_material": mat})
            )
            .selected_material
            == mat
        )
    no_mat = dict(minimal)
    no_mat.pop("electrode_material")
    with pytest.raises(ValueError):
        EarthRodSizingInput(**no_mat)
    for bad_mat in ("aluminum", "hot_dip_galvanized_steel", "", None):
        with pytest.raises(ValueError):
            EarthRodSizingInput(**{**minimal, "electrode_material": bad_mat})  # type: ignore[arg-type]

    # D.5: unclamped below l_rod=1.0, rho=1.0, r_target=0.5, setback=1.0
    res_unclamped = EarthRodSizingEngine().size_earth_rod_system(
        EarthRodSizingInput(
            soil_resistivity_ohm_m=0.5,
            target_resistance_ohm=0.2,
            electrode_material="copper_bonded_steel",
            rod_length_per_unit_m=0.6,
            min_distance_to_building_foundation_m=0.25,
            site_boundary_length_m=40.0,
            site_boundary_width_m=25.0,
        )
    )
    assert res_unclamped.unit_rod_length_m == 0.6
    assert res_unclamped.inter_rod_spacing_rule_m == 1.2
    assert res_unclamped.recommended_rod_coordinates[0] == (-20.25, -12.75)


# ---------------------------------------------------------------------------
# Decision 3 & Criterion D: Diagnostics self-test and HTTP 422 / 200 probes
# ---------------------------------------------------------------------------


def test_diagnostics_self_test_unchanged():
    diag = SystemDiagnostics.run_self_test()
    assert diag["system_status"] == "OPERATIONAL"
    assert diag["tests"]["earthing_engine"] == {
        "status": "PASS",
        "message": "Type B ring resistance: 2.51 ohm",
    }


def test_http_endpoints_reject_empty_422_and_accept_valid_200():
    for endpoint in (
        "/api/v1/calculations/earthing",
        "/api/v1/calculations/spd-coordination",
        "/api/v1/calculations/earth-pit-sizing",
        "/api/v1/calculations/earth-rod-sizing",
    ):
        resp_empty = client.post(endpoint, json={})
        assert resp_empty.status_code == 422, f"{endpoint} returned {resp_empty.status_code}"

    resp_earthing = client.post(
        "/api/v1/calculations/earthing",
        json={
            "lps_class": "I",
            "soil": {"rho_upper_ohm_m": 100.0},
            "electrode_type": "type_b_ring",
            "ring_radius_m": 15.0,
            "conductor_diameter_m": 0.01,
            "burial_depth_m": 0.5,
            "peak_impulse_current_ka": 100.0,
        },
    )
    assert resp_earthing.status_code == 200
    assert resp_earthing.json()["status"] == "PASS"

    resp_spd = client.post(
        "/api/v1/calculations/spd-coordination",
        json={
            "spds": [
                {
                    "id": "spd-1",
                    "spd_class": "Type 1",
                    "technology": "spark_gap",
                    "i_imp_ka": 25.0,
                    "up_kv": 1.2,
                    "cable_length_to_downstream_m": 15.0,
                    "lead_length_m": 0.3,
                },
                {
                    "id": "spd-2",
                    "spd_class": "Type 2",
                    "technology": "varistor_mov",
                    "i_n_ka": 10.0,
                    "up_kv": 1.0,
                    "lead_length_m": 0.2,
                },
            ],
            "equipment": {
                "category": "Cat II",
                "uw_kv": 2.5,
                "induced_voltage_kv": 0.0,
                "reflection_coefficient_kr": 2.0,
            },
        },
    )
    assert resp_spd.status_code == 200
    assert resp_spd.json()["status"] == "COORDINATED"

    resp_pit = client.post(
        "/api/v1/calculations/earth-pit-sizing",
        json=_valid_earth_pit_kwargs(),
    )
    assert resp_pit.status_code == 200
    assert resp_pit.json()["status"] == "SIZED_AND_VERIFIED"

    resp_rod = client.post(
        "/api/v1/calculations/earth-rod-sizing",
        json=_valid_earth_rod_kwargs(),
    )
    assert resp_rod.status_code == 200
    assert resp_rod.json()["status"] == "SIZED_AND_COMPLIANT"
