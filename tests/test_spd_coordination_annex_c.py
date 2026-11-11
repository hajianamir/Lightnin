"""Reference, boundary, and validation tests for IEC 62305-4:2024 Annex C.2.3 SPD coordination (Step 2.6 — H15)."""

import pytest
from fastapi.testclient import TestClient

from aegislps_api.main import app
from aegislps_engine.spd_coordination import (
    EquipmentWithstand,
    SPDCoordinationAssessment,
    SPDCoordinationEngine,
    SPDEntry,
)


# ---------------------------------------------------------------------------
# 1. Equation Reference Tests — IEC 62305-4:2024 Annex C.2.3 (pp. 87–93)
# ---------------------------------------------------------------------------


def test_rule1_simplified_up_limit():
    """IEC 62305-4:2024 Clause C.2.3.1.2 (p. 88): U_p should not exceed 80 % of U_w when the equipment is <= 10 m from the entrance SPD. Clause C.2.3.1.4 (p. 89): for > 10 m, one-port SPD at the origin: U_p <= 50 % of U_w. The code applies the stricter 0.5 * U_w bound to all cases as a conservative screen (conservative screening bound (C.2.3.1.4))."""
    assert SPDCoordinationEngine.check_rule1_up(1.25, 2.5) is True
    assert SPDCoordinationEngine.check_rule1_up(1.20, 2.5) is True
    assert SPDCoordinationEngine.check_rule1_up(1.26, 2.5) is False


def test_equation_c1_required_effective_protection_level():
    """IEC 62305-4:2024 Clause C.2.3.2 Eq. (C.1) (p. 89): U_p/f = (U_w - U_i) / k_r for k_r = 1, 2, default."""
    # k_r = 1.0 (no reflection)
    assert SPDCoordinationEngine.calculate_required_upf_c1(4.0, 0.4, 1.0) == pytest.approx(
        3.6, rel=1e-15
    )
    # k_r = 2.0 explicit (full open-circuit doubling)
    assert SPDCoordinationEngine.calculate_required_upf_c1(4.0, 0.4, 2.0) == pytest.approx(
        1.8, rel=1e-15
    )
    # Default k_r = 2.0 (worst case when unknown per Clause C.2.3.2)
    assert SPDCoordinationEngine.calculate_required_upf_c1(2.5, 0.5) == pytest.approx(
        1.0, rel=1e-15
    )


def test_equation_c2_voltage_limiting_and_hybrid_upf():
    """IEC 62305-4:2024 Clause C.2.3.3 Eq. (C.2) (p. 90): U_p/f = U_p + ΔU for limiting and hybrid SPDs."""
    assert SPDCoordinationEngine.calculate_effective_protection_level_upf(
        1.2, 0.5, "varistor_mov"
    ) == pytest.approx(1.7, rel=1e-15)
    assert SPDCoordinationEngine.calculate_effective_protection_level_upf(
        1.2, 0.5, "hybrid"
    ) == pytest.approx(1.7, rel=1e-15)

    # End-to-end check: U_p = 1.5 <= U_req = 2.0, but at lead = 0.6 m ΔU = 0.6 -> U_p/f = 2.1 > U_req
    engine = SPDCoordinationEngine()
    res = engine.evaluate_coordination(
        [
            SPDEntry(
                id="t1",
                spd_class="Type 1",
                technology="spark_gap",
                up_kv=1.8,
                cable_length_to_downstream_m=15.0,
                lead_length_m=0.5,
            ),
            SPDEntry(
                id="t2",
                spd_class="Type 2",
                technology="varistor_mov",
                i_n_ka=10.0,
                up_kv=1.5,
                lead_length_m=0.6,
            ),
        ],
        EquipmentWithstand(
            category="Cat III",
            uw_kv=4.0,
            induced_voltage_kv=0.0,
            reflection_coefficient_kr=2.0,
        ),
    )
    assert res.voltage_protection_verified is False
    assert res.max_connecting_lead_length_m == 0.0
    assert res.status == "ACTION_REQUIRED"


def test_equation_c3_voltage_switching_upf():
    """IEC 62305-4:2024 Clause C.2.3.3 Eq. (C.3) (p. 90): U_p/f = max(U_p, ΔU) for spark-gap SPDs."""
    assert SPDCoordinationEngine.calculate_effective_protection_level_upf(
        1.5, 0.8, "spark_gap"
    ) == pytest.approx(1.5, rel=1e-15)
    assert SPDCoordinationEngine.calculate_effective_protection_level_upf(
        1.5, 2.1, "spark_gap"
    ) == pytest.approx(2.1, rel=1e-15)


def test_equation_c4_lead_voltage_drop_10ka_1m():
    """IEC 62305-4:2024 Clause C.2.3.3 Eq. (C.4) (p. 90): 1 m lead carrying 10 kA produces ΔU = 1.0 kV."""
    assert SPDCoordinationEngine.calculate_lead_voltage_drop_c4(10.0, 1.0) == pytest.approx(
        1.0, rel=1e-15
    )

    # End-to-end L_max reference: Cat III U_w = 4.0 kV, U_i = 0.0 kV, k_r = 2.0 -> U_req = 2.0 kV;
    # limiting Type 2 SPD with U_p = 1.0 kV, I_n = 10 kA, lead = 0.5 m -> L_max = (2.0 - 1.0) / 1.0 = 1.000 m.
    engine = SPDCoordinationEngine()
    res = engine.evaluate_coordination(
        [
            SPDEntry(
                id="t1",
                spd_class="Type 1",
                technology="spark_gap",
                up_kv=1.8,
                cable_length_to_downstream_m=12.0,
                lead_length_m=0.5,
            ),
            SPDEntry(
                id="t2",
                spd_class="Type 2",
                technology="varistor_mov",
                i_n_ka=10.0,
                up_kv=1.0,
                lead_length_m=0.5,
            ),
        ],
        EquipmentWithstand(
            category="Cat III",
            uw_kv=4.0,
            induced_voltage_kv=0.0,
            reflection_coefficient_kr=2.0,
        ),
    )
    assert res.status == "COORDINATED"
    assert res.voltage_protection_verified is True
    assert res.max_connecting_lead_length_m == pytest.approx(1.0, abs=1e-9)


def test_equation_c5_oscillation_bound():
    """IEC 62305-4:2024 Clause C.2.3.4 Eq. (C.5) (p. 92): U_p/f <= U_w."""
    assert SPDCoordinationEngine.check_oscillation_c5(2.5, 2.5) is True
    assert SPDCoordinationEngine.check_oscillation_c5(2.0, 2.5) is True
    assert SPDCoordinationEngine.check_oscillation_c5(2.51, 2.5) is False


# ---------------------------------------------------------------------------
# 2. Boundary, Stage Selection, and Warning Tests
# ---------------------------------------------------------------------------


def test_legacy_heuristic_removed_and_output_field_renamed():
    """Confirm empirical calculate_effective_protective_distance and effective_protection_distance_m are removed."""
    assert not hasattr(SPDCoordinationEngine, "calculate_effective_protective_distance")
    assert "effective_protection_distance_m" not in SPDCoordinationAssessment.model_fields
    assert "max_connecting_lead_length_m" in SPDCoordinationAssessment.model_fields


@pytest.mark.parametrize("up_kv", [1.25, 1.50])
def test_boundary_non_positive_numerator_gives_zero_length_and_not_coordinated(up_kv: float):
    """When U_req - U_p <= 0 (limiting) or U_p > U_req, L_max = 0.0 m and status is NOT COORDINATED."""
    engine = SPDCoordinationEngine()
    res = engine.evaluate_coordination(
        [
            SPDEntry(
                id="t1",
                spd_class="Type 1",
                technology="spark_gap",
                up_kv=1.2,
                cable_length_to_downstream_m=15.0,
                lead_length_m=0.2,
            ),
            SPDEntry(
                id="t2",
                spd_class="Type 2",
                technology="varistor_mov",
                i_n_ka=20.0,
                up_kv=up_kv,
                lead_length_m=0.0,
            ),
        ],
        EquipmentWithstand(
            category="Cat II",
            uw_kv=2.5,
            induced_voltage_kv=0.0,
            reflection_coefficient_kr=2.0,
        ),
    )
    assert res.max_connecting_lead_length_m == 0.0
    assert res.voltage_protection_verified is False
    assert res.status != "COORDINATED"
    assert any("L_max=0.000 m" in w for w in res.warnings)


def test_limiting_vs_switching_give_distinct_l_max_for_identical_inputs():
    """IEC 62305-4:2024 Eq. (C.2) vs Eq. (C.3): limiting and switching yield different L_max."""
    engine = SPDCoordinationEngine()
    equip = EquipmentWithstand(
        category="Cat III",
        uw_kv=4.0,
        induced_voltage_kv=0.0,
        reflection_coefficient_kr=2.0,
    )
    t1 = SPDEntry(
        id="t1",
        spd_class="Type 1",
        technology="spark_gap",
        up_kv=1.8,
        cable_length_to_downstream_m=15.0,
        lead_length_m=0.3,
    )

    res_lim = engine.evaluate_coordination(
        [
            t1,
            SPDEntry(
                id="t2-lim",
                spd_class="Type 2",
                technology="varistor_mov",
                i_n_ka=20.0,
                up_kv=1.2,
                lead_length_m=0.2,
            ),
        ],
        equip,
    )
    res_sw = engine.evaluate_coordination(
        [
            t1,
            SPDEntry(
                id="t2-sw",
                spd_class="Type 2",
                technology="spark_gap",
                i_n_ka=20.0,
                up_kv=1.2,
                lead_length_m=0.2,
            ),
        ],
        equip,
    )
    # Limiting: (2.0 - 1.2) / (0.1 * 20) = 0.400 m; Switching: 2.0 / (0.1 * 20) = 1.000 m
    assert res_lim.status == "COORDINATED"
    assert res_sw.status == "COORDINATED"
    assert res_lim.max_connecting_lead_length_m == pytest.approx(0.4, abs=1e-9)
    assert res_sw.max_connecting_lead_length_m == pytest.approx(1.0, abs=1e-9)
    assert res_lim.max_connecting_lead_length_m != res_sw.max_connecting_lead_length_m


def test_default_lead_length_and_default_kr_emit_warnings():
    """Omitting lead_length_m (should not be greater than 0,5 m per C.2.5) or reflection_coefficient_kr (2.0 per C.2.3.2) emits warnings."""
    engine = SPDCoordinationEngine()
    res = engine.evaluate_coordination(
        [
            SPDEntry(
                id="t1",
                spd_class="Type 1",
                technology="spark_gap",
                up_kv=1.8,
                cable_length_to_downstream_m=15.0,
            ),
            SPDEntry(
                id="t2",
                spd_class="Type 2",
                technology="varistor_mov",
                i_n_ka=10.0,
                up_kv=1.0,
            ),
        ],
        EquipmentWithstand(category="Cat III", uw_kv=4.0, induced_voltage_kv=0.0),
    )
    assert any("k_r = 2.0" in w for w in res.warnings)
    assert any("lead_length_m not specified" in w and "0.5 m" in w for w in res.warnings)
    assert any("Assumed connecting lead length lead_length_m = 0.5 m" in d for d in res.coordination_details)


def test_equipment_side_stage_selects_smallest_up_type2_or_type3_and_missing_stage_fails():
    """Equipment-side check selects smallest-U_p Type 2/3 SPD (Type 3 uses i_n_ka); Type 1 alone is unverified."""
    engine = SPDCoordinationEngine()
    equip = EquipmentWithstand(
        category="Cat II",
        uw_kv=2.5,
        induced_voltage_kv=0.1,
        reflection_coefficient_kr=2.0,
    )
    t1 = SPDEntry(
        id="t1",
        spd_class="Type 1",
        technology="spark_gap",
        up_kv=1.2,
        cable_length_to_downstream_m=15.0,
        lead_length_m=0.5,
    )
    t2 = SPDEntry(
        id="t2",
        spd_class="Type 2",
        technology="varistor_mov",
        i_n_ka=20.0,
        up_kv=1.2,
        lead_length_m=0.5,
    )
    t3 = SPDEntry(
        id="t3",
        spd_class="Type 3",
        technology="varistor_mov",
        i_n_ka=5.0,
        up_kv=0.9,
        lead_length_m=0.3,
    )
    # U_req = (2.5 - 0.1)/2 = 1.2 kV; t3 selected (U_p=0.9 < 1.2): L_max = (1.2 - 0.9)/(0.1*5) = 0.600 m
    res = engine.evaluate_coordination([t1, t2, t3], equip)
    assert res.status == "COORDINATED"
    assert res.max_connecting_lead_length_m == pytest.approx(0.6, abs=1e-9)

    # Type 1 only -> no Type 2/3 equipment-side SPD
    res_only_t1 = engine.evaluate_coordination([t1], equip)
    assert res_only_t1.voltage_protection_verified is False
    assert res_only_t1.max_connecting_lead_length_m == 0.0
    assert res_only_t1.status == "ACTION_REQUIRED"


# ---------------------------------------------------------------------------
# 3. Validation & FastAPI HTTP 422 Tests
# ---------------------------------------------------------------------------


def test_missing_or_invalid_induced_voltage_raises_value_error():
    """Missing, negative, non-finite, or boolean induced_voltage_kv raises ValueError."""
    with pytest.raises(ValueError):
        EquipmentWithstand()  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        EquipmentWithstand(induced_voltage_kv=None)  # type: ignore[arg-type]
    for bad_ui in (-0.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            EquipmentWithstand(induced_voltage_kv=bad_ui)  # type: ignore[arg-type]

    engine = SPDCoordinationEngine()
    with pytest.raises(ValueError):
        engine.evaluate_coordination([], None)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_kr", [0.99, 0.0, -1.0, 2.01, 3.0, float("nan"), float("inf"), True])
def test_reflection_coefficient_outside_bounds_raises_value_error(bad_kr):
    """reflection_coefficient_kr outside [1.0, 2.0] or non-finite raises ValueError."""
    with pytest.raises(ValueError):
        EquipmentWithstand(induced_voltage_kv=0.0, reflection_coefficient_kr=bad_kr)
    with pytest.raises(ValueError):
        SPDCoordinationEngine.calculate_required_upf_c1(2.5, 0.0, bad_kr)


def test_invalid_spd_technology_class_and_lead_length_raise_value_error():
    """Unknown technology, unknown spd_class, or negative/non-finite lead_length_m raises ValueError."""
    for bad_tech in ("gas_tube", "combination", "", "MOV"):
        with pytest.raises(ValueError):
            SPDEntry(id="s", spd_class="Type 2", technology=bad_tech)
    for bad_cls in ("Type 4", "Class I", "1", ""):
        with pytest.raises(ValueError):
            SPDEntry(id="s", spd_class=bad_cls)
    for bad_lead in (-0.1, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            SPDEntry(id="s", spd_class="Type 2", lead_length_m=bad_lead)  # type: ignore[arg-type]


def test_api_spd_coordination_requires_equipment_and_induced_voltage():
    """POST /api/v1/calculations/spd-coordination returns 422 when equipment or induced_voltage_kv is missing."""
    client = TestClient(app)
    spds_payload = [
        {
            "id": "spd-1",
            "spd_class": "Type 1",
            "technology": "spark_gap",
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
    ]

    # Legacy list-only body (missing equipment) -> 422
    resp_missing_equip = client.post("/api/v1/calculations/spd-coordination", json=spds_payload)
    assert resp_missing_equip.status_code == 422

    # Body with equipment missing induced_voltage_kv -> 422
    resp_missing_ui = client.post(
        "/api/v1/calculations/spd-coordination",
        json={"spds": spds_payload, "equipment": {"category": "Cat II", "uw_kv": 2.5}},
    )
    assert resp_missing_ui.status_code == 422

    # Valid body -> 200 with max_connecting_lead_length_m = (1.25 - 1.0) / 1.0 = 0.25 m
    resp_ok = client.post(
        "/api/v1/calculations/spd-coordination",
        json={
            "spds": spds_payload,
            "equipment": {
                "category": "Cat II",
                "uw_kv": 2.5,
                "induced_voltage_kv": 0.0,
                "reflection_coefficient_kr": 2.0,
            },
        },
    )
    assert resp_ok.status_code == 200
    body = resp_ok.json()
    assert body["status"] == "COORDINATED"
    assert body["max_connecting_lead_length_m"] == pytest.approx(0.25, abs=1e-9)
