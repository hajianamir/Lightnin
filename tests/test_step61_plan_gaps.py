"""Step 6.1 — Plan-gap modules (M3–M7) and placeholder checksum removal tests."""

from __future__ import annotations

import io
import secrets

import docx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from aegislps_api.main import app
from aegislps_domain.integrity import INTEGRITY_KEY_ENV_VAR
from aegislps_engine.bom_engine import BOMAndLifecycleEngine
from aegislps_engine.earth_pit import EarthPitEngine, EarthPitSizingInput
from aegislps_engine.earth_rod_sizing import EarthRodSizingEngine, EarthRodSizingInput
from aegislps_engine.hvi_conductor import (
    HVIConductorAssistant,
    HVIConductorSelectionInput,
)
from aegislps_engine.pv_module import PVArraySpecification, PVEngineeringModule

client = TestClient(app)
_LEGACY_PLACEHOLDER = "3a0e5fd34a07fd3d21fb" + "ce074f84f612060e7174"


# ---------------------------------------------------------------------------
# M3 — bom_engine.py: 1.0 m Type B ring offset around all 4 external walls
# ---------------------------------------------------------------------------


def test_m3_bom_earth_ring_1m_offset_hand_calculated_for_two_buildings() -> None:
    engine = BOMAndLifecycleEngine()

    # Building 1: 30 m x 20 m -> outer ring (30 + 2) x (20 + 2) = 32 x 22 m
    # Perimeter = 2 * (30 + 20 + 4) = 108.0 m; with 5% waste: 108.0 * 1.05 = 113.4 m
    bom_1 = engine.generate_project_bom(
        project_name="Building One 30x20",
        lps_class="I",
        building_length_m=30.0,
        building_width_m=20.0,
        building_height_m=15.0,
        rod_count=4,
        down_conductor_count=4,
    )
    strip_1 = next(i for i in bom_1.items if i.item_code == "EARTH-STRIP-CU")
    assert strip_1.quantity == 113.4

    # Building 2: 40 m x 25 m -> outer ring (40 + 2) x (25 + 2) = 42 x 27 m
    # Perimeter = 2 * (40 + 25 + 4) = 138.0 m; with 5% waste: 138.0 * 1.05 = 144.9 m
    bom_2 = engine.generate_project_bom(
        project_name="Building Two 40x25",
        lps_class="II",
        building_length_m=40.0,
        building_width_m=25.0,
        building_height_m=12.0,
        rod_count=6,
        down_conductor_count=6,
    )
    strip_2 = next(i for i in bom_2.items if i.item_code == "EARTH-STRIP-CU")
    assert strip_2.quantity == 144.9


# ---------------------------------------------------------------------------
# M4 — hvi_conductor.py: unused inputs removed from model and API schema
# ---------------------------------------------------------------------------


def test_m4_hvi_unused_inputs_removed_and_rejected_in_model_and_api() -> None:
    schema = HVIConductorSelectionInput.model_json_schema()
    assert set(schema["properties"].keys()) == {
        "required_equivalent_separation_s_air_m",
        "down_conductor_route_length_m",
        "hvi_conductor_model",
    }
    assert schema.get("additionalProperties") is False

    base_payload = {
        "required_equivalent_separation_s_air_m": 0.75,
        "down_conductor_route_length_m": 18.0,
        "hvi_conductor_model": "HVI_light_75",
    }
    for removed_field, val in (
        ("lps_class", "I"),
        ("ambient_installation_type", "outdoor_façade"),
    ):
        with pytest.raises(ValidationError):
            HVIConductorSelectionInput(**{**base_payload, removed_field: val})
        resp_422 = client.post(
            "/api/v1/calculations/hvi-selection",
            json={**base_payload, removed_field: val},
        )
        assert resp_422.status_code == 422

    resp_200 = client.post("/api/v1/calculations/hvi-selection", json=base_payload)
    assert resp_200.status_code == 200
    assert resp_200.json()["status"] == "COMPLIANT_APPROVED"

    direct = HVIConductorAssistant().evaluate_hvi_selection(
        HVIConductorSelectionInput(**base_payload)
    )
    assert direct.equivalent_separation_distance_se_m == 0.75


# ---------------------------------------------------------------------------
# M5 — pv_module.py: Table 13 per-configuration kc + unused inputs removed
# ---------------------------------------------------------------------------


def test_m5_pv_table13_kc_selection_and_unused_inputs_removed() -> None:
    schema = PVArraySpecification.model_json_schema()
    assert set(schema["properties"].keys()) == {
        "separation_to_lps_m",
        "lps_class",
        "down_conductor_length_l_m",
        "insulation_medium",
        "down_conductor_count",
        "earth_resistances_within_factor_2",
    }
    assert schema.get("additionalProperties") is False

    engine = PVEngineeringModule()
    common = {
        "lps_class": "I",  # ki = 0.08
        "down_conductor_length_l_m": 15.0,
        "separation_to_lps_m": 0.85,
        "insulation_medium": "air",  # km = 1.0
    }

    # 1. Omitted down_conductor_count -> Table 13 fallback kc = 1.0 -> s = 0.08 * 1.0 * 15 = 1.2 m
    res_fallback = engine.evaluate_pv_installation(PVArraySpecification(**common))
    assert res_fallback.kc_used == 1.0
    assert "fallback" in res_fallback.kc_basis
    assert res_fallback.required_separation_s_m == 1.2
    assert res_fallback.status == "BONDING_MANDATORY"

    # 2. n = 1, earth_resistances_within_factor_2 = True -> Table 13 kc = 1.0 -> s = 1.2 m
    res_n1 = engine.evaluate_pv_installation(
        PVArraySpecification(
            **common, down_conductor_count=1, earth_resistances_within_factor_2=True
        )
    )
    assert res_n1.kc_used == 1.0
    assert "n=1" in res_n1.kc_basis
    assert res_n1.required_separation_s_m == 1.2

    # 3. n = 2, earth_resistances_within_factor_2 = True -> Table 13 kc = 0.66 -> s = 0.792 m
    res_n2 = engine.evaluate_pv_installation(
        PVArraySpecification(
            **common, down_conductor_count=2, earth_resistances_within_factor_2=True
        )
    )
    assert res_n2.kc_used == 0.66
    assert "n=2" in res_n2.kc_basis
    assert res_n2.required_separation_s_m == 0.792
    assert res_n2.status == "ISOLATED_PASS"

    # 4. n = 4 (>= 3), earth_resistances_within_factor_2 = True -> Table 13 kc = 0.44 -> s = 0.528 m
    res_n4 = engine.evaluate_pv_installation(
        PVArraySpecification(
            **common, down_conductor_count=4, earth_resistances_within_factor_2=True
        )
    )
    assert res_n4.kc_used == 0.44
    assert "3 and more" in res_n4.kc_basis
    assert res_n4.required_separation_s_m == 0.528
    assert res_n4.status == "ISOLATED_PASS"

    # 5. n = 4, earth_resistances_within_factor_2 = False -> Table 13 fallback kc = 1.0
    res_unbalanced = engine.evaluate_pv_installation(
        PVArraySpecification(
            **common, down_conductor_count=4, earth_resistances_within_factor_2=False
        )
    )
    assert res_unbalanced.kc_used == 1.0

    # 6. Removed unused inputs rejected on API route
    for removed_key, val in (
        ("id", "pv-1"),
        ("tilt_angle_deg", 15.0),
        ("panel_count", 24),
        ("array_length_m", 12.0),
        ("array_width_m", 6.0),
        ("metallic_frame_bonded", True),
    ):
        resp_422 = client.post(
            "/api/v1/calculations/pv-clearance",
            json={**common, removed_key: val},
        )
        assert resp_422.status_code == 422


# ---------------------------------------------------------------------------
# M6 — earth_pit.py: unsourced rho_c flag present for all backfill materials
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "material",
    ("carbon_gem", "sodium_bentonite", "chemical_salts", "native_backfill"),
)
def test_m6_earth_pit_marks_all_rho_c_values_as_unsourced_assumption(
    material: str,
) -> None:
    assert (
        EarthPitEngine.BACKFILL_PROPERTIES[material]["rho_c_unsourced_assumption"]
        is True
    )
    res = EarthPitEngine().evaluate_earth_pit_and_backfill(
        EarthPitSizingInput(
            is_disconnect_testing_required=True,
            traffic_loading_area="pedestrian",
            electrode_rod_diameter_mm=16.0,
            auger_hole_diameter_mm=100.0,
            treatment_depth_m=3.0,
            enhancement_material=material,
            native_soil_resistivity_ohm_m=150.0,
        )
    )
    assert res.rho_c_unsourced_assumption is True
    assert "Unsourced assumption (M6)" in res.rho_c_assumption_note


# ---------------------------------------------------------------------------
# M7 — earth_rod_sizing.py: copper-coated steel 14.0 mm boundary check
# ---------------------------------------------------------------------------


def test_m7_copper_bonded_steel_diameter_14mm_boundary_and_just_below() -> None:
    assert "minimum 14.0 mm diameter" in (EarthRodSizingEngine.__doc__ or "")
    assert (
        EarthRodSizingEngine.IEC_62561_2_SPECS["copper_bonded_steel"]["min_dia_mm"]
        == 14.0
    )

    common = {
        "soil_resistivity_ohm_m": 120.0,
        "target_resistance_ohm": 10.0,
        "electrode_material": "copper_bonded_steel",
        "rod_length_per_unit_m": 3.0,
        "site_boundary_length_m": 40.0,
        "site_boundary_width_m": 25.0,
    }

    # Exact minimum boundary (14.0 mm) passes
    res_exact = EarthRodSizingEngine().size_earth_rod_system(
        EarthRodSizingInput(**common, rod_diameter_mm=14.0)
    )
    assert res_exact.nominal_diameter_mm == 14.0
    assert res_exact.single_rod_resistance_ohm == pytest.approx(41.04, abs=0.01)

    # Commercial 16.0 mm (> 14.0 mm) also passes
    res_16 = EarthRodSizingEngine().size_earth_rod_system(
        EarthRodSizingInput(**common, rod_diameter_mm=16.0)
    )
    assert res_16.nominal_diameter_mm == 16.0
    assert res_16.single_rod_resistance_ohm == pytest.approx(40.19, abs=0.01)

    # Just below minimum (13.99 mm) fails validation and returns HTTP 422
    with pytest.raises(ValidationError, match="14.0 mm"):
        EarthRodSizingInput(**common, rod_diameter_mm=13.99)

    resp_below = client.post(
        "/api/v1/calculations/earth-rod-sizing",
        json={**common, "rod_diameter_mm": 13.99},
    )
    assert resp_below.status_code == 422


# ---------------------------------------------------------------------------
# Placeholder checksum — API /api/v1/reports/docx & /api/v1/projects/compute-checksum
# ---------------------------------------------------------------------------


def test_docx_api_uses_computed_project_checksum_or_not_computed_when_key_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "project_id": "step61-docx-checksum-proj",
        "name": "Step 6.1 Checksum Verification",
        "lps_class": "I",
        "building": {
            "length_m": 30.0,
            "width_m": 20.0,
            "height_m": 15.0,
            "roof_type": "flat",
        },
        "nodes": [{"id": "n1", "x": 0.0, "y": 0.0, "z": 15.0, "node_type": "air_termination"}],
        "segments": [],
        "separation_points": [
            {
                "id": "sp1",
                "name": "Target 1",
                "x": 4.0,
                "y": 3.0,
                "z": 15.0,
                "associated_node_id": "n1",
                "insulation_medium": "air",
                "physical_distance_m": 1.5,
            }
        ],
    }

    # 1. Key configured -> DOCX embeds the exact checksum returned by /api/v1/projects/compute-checksum
    monkeypatch.setenv(INTEGRITY_KEY_ENV_VAR, secrets.token_hex(32))
    chk_resp = client.post("/api/v1/projects/compute-checksum", json=payload)
    assert chk_resp.status_code == 200
    expected_checksum = chk_resp.json()["checksum"]

    docx_resp = client.post("/api/v1/reports/docx", json=payload)
    assert docx_resp.status_code == 200
    doc_set = docx.Document(io.BytesIO(docx_resp.content))
    text_set = "\n".join(p.text for p in doc_set.paragraphs if p.text)
    assert _LEGACY_PLACEHOLDER not in text_set
    assert f"SHA-256 HMAC Checksum: {expected_checksum}" in text_set

    # 2. Key unconfigured -> DOCX still renders (200) and displays "not computed", never a fixed hash
    monkeypatch.delenv(INTEGRITY_KEY_ENV_VAR, raising=False)
    docx_unset_resp = client.post("/api/v1/reports/docx", json=payload)
    assert docx_unset_resp.status_code == 200
    doc_unset = docx.Document(io.BytesIO(docx_unset_resp.content))
    text_unset = "\n".join(p.text for p in doc_unset.paragraphs if p.text)
    assert _LEGACY_PLACEHOLDER not in text_unset
    assert "SHA-256 HMAC Checksum: not computed" in text_unset
