import pytest
from fastapi.testclient import TestClient

from aegislps_api.main import app
from aegislps_engine.comprehensive_risk import (
    ComprehensiveRisk2024Engine,
    ComprehensiveRiskInput,
    IncomingServiceLine,
)
from aegislps_engine.risk import RiskAssessmentInput, RiskManagementEngine

client = TestClient(app)


def _valid_risk_kwargs() -> dict:
    return {
        "structure_length_m": 30.0,
        "structure_width_m": 20.0,
        "structure_height_m": 15.0,
        "ng_flashes_per_km2_year": 2.5,
        "environmental_cd": 1.0,
        "lps_class": "I",
        "loss_category": "normal",
        "fire_risk_rf": 0.01,
        "has_coordinated_spd": True,
    }


def _valid_comp_kwargs() -> dict:
    return {
        "structure_length_m": 40.0,
        "structure_width_m": 25.0,
        "structure_height_m": 15.0,
        "ng_flashes_per_km2_year": 2.5,
        "environmental_cd": 1.0,
        "lps_class": "I",
        "loss_category": "normal",
        "fire_risk_rf": 0.01,
        "has_coordinated_spd": True,
        "has_tws_early_warning": True,
    }


# ---------------------------------------------------------------------------
# Rule A.1 & A.2: RiskAssessmentInput.time_in_structure_hours_per_year
# ---------------------------------------------------------------------------


def test_a1_a2_risk_hours_default_8760_and_range_validation():
    inp_default = RiskAssessmentInput(**_valid_risk_kwargs())
    assert inp_default.time_in_structure_hours_per_year == 8760.0

    eng = RiskManagementEngine()
    res_default = eng.evaluate_r1_risk(inp_default)
    res_explicit = eng.evaluate_r1_risk(
        RiskAssessmentInput(**_valid_risk_kwargs(), time_in_structure_hours_per_year=8760.0)
    )
    assert res_default.risk_r1_loss_of_life == res_explicit.risk_r1_loss_of_life

    # Boundary values 0 and 8760 are valid
    assert RiskAssessmentInput(**_valid_risk_kwargs(), time_in_structure_hours_per_year=0.0).time_in_structure_hours_per_year == 0.0
    assert RiskAssessmentInput(**_valid_risk_kwargs(), time_in_structure_hours_per_year=4380.0).time_in_structure_hours_per_year == 4380.0

    # Above 8760 (no silent clamp), negative, non-finite, and bool raise ValueError
    for bad_hours in (-0.01, -10.0, 8760.01, 10000.0, float("nan"), float("inf"), -float("inf"), True, False):
        with pytest.raises(ValueError):
            RiskAssessmentInput(**_valid_risk_kwargs(), time_in_structure_hours_per_year=bad_hours)


# ---------------------------------------------------------------------------
# Rule A.3: RiskAssessmentInput.lps_class required and in {"none","I","II","III","IV"}
# ---------------------------------------------------------------------------


def test_a3_risk_lps_class_required_and_validated():
    missing = _valid_risk_kwargs()
    missing.pop("lps_class")
    with pytest.raises(ValueError):
        RiskAssessmentInput(**missing)

    for valid_cls in ("none", "I", "II", "III", "IV"):
        kw = {**_valid_risk_kwargs(), "lps_class": valid_cls}
        assert RiskAssessmentInput(**kw).lps_class == valid_cls

    for bad_cls in ("unprotected", "V", "i", " I", "", None, 1, True):
        kw = {**_valid_risk_kwargs(), "lps_class": bad_cls}
        with pytest.raises(ValueError):
            RiskAssessmentInput(**kw)


# ---------------------------------------------------------------------------
# Rule A.4: RiskAssessmentInput.has_coordinated_spd required strict bool
# ---------------------------------------------------------------------------


def test_a4_risk_has_coordinated_spd_required_and_strict_bool():
    missing = _valid_risk_kwargs()
    missing.pop("has_coordinated_spd")
    with pytest.raises(ValueError):
        RiskAssessmentInput(**missing)

    for valid_flag in (True, False):
        kw = {**_valid_risk_kwargs(), "has_coordinated_spd": valid_flag}
        assert RiskAssessmentInput(**kw).has_coordinated_spd is valid_flag

    for bad_flag in (1, 0, "true", "false", None):
        kw = {**_valid_risk_kwargs(), "has_coordinated_spd": bad_flag}
        with pytest.raises(ValueError):
            RiskAssessmentInput(**kw)


# ---------------------------------------------------------------------------
# Rule A.5: Required positive finite numeric inputs on RiskAssessmentInput
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field_name",
    [
        "structure_length_m",
        "structure_width_m",
        "structure_height_m",
        "ng_flashes_per_km2_year",
        "environmental_cd",
    ],
)
def test_a5_risk_positive_numeric_fields_required_and_validated(field_name: str):
    missing = _valid_risk_kwargs()
    missing.pop(field_name)
    with pytest.raises(ValueError):
        RiskAssessmentInput(**missing)

    for bad_val in (0.0, -1e-6, -5.0, float("nan"), float("inf"), -float("inf"), True, False):
        kw = {**_valid_risk_kwargs(), field_name: bad_val}
        with pytest.raises(ValueError):
            RiskAssessmentInput(**kw)

    for cd_val in (0.25, 0.5, 1.0, 2.0):
        kw = {**_valid_risk_kwargs(), "environmental_cd": cd_val}
        assert RiskAssessmentInput(**kw).environmental_cd == cd_val


# ---------------------------------------------------------------------------
# Rule A.6: Explicit fire_risk_level or fire_risk_rf required
# ---------------------------------------------------------------------------


def test_a6_risk_requires_explicit_fire_risk_level_or_rf():
    missing = _valid_risk_kwargs()
    missing.pop("fire_risk_rf")
    with pytest.raises(ValueError):
        RiskAssessmentInput(**missing)

    # Explicit fire_risk_level alone passes
    by_level = RiskAssessmentInput(**missing, fire_risk_level="explosion_zone_1_21")
    assert by_level.fire_risk_level == "explosion_zone_1_21"
    assert by_level.fire_risk_rf is None

    # Explicit fire_risk_rf alone passes
    by_rf = RiskAssessmentInput(**missing, fire_risk_rf=0.001)
    assert by_rf.fire_risk_rf == 0.001
    assert by_rf.fire_risk_level is None

    # Conflicting fire_risk_level and fire_risk_rf raises ValueError
    with pytest.raises(ValueError):
        RiskAssessmentInput(**missing, fire_risk_level="fire_low", fire_risk_rf=0.1)


# ---------------------------------------------------------------------------
# Rule B.1: IncomingServiceLine.line_length_m default 1000.0, > 0, no 100m clamp
# ---------------------------------------------------------------------------


def test_b1_incoming_service_line_length_validation_and_unclamped_short_line():
    default_line = IncomingServiceLine()
    assert default_line.line_length_m == 1000.0

    for bad_len in (0.0, -0.1, -100.0, float("nan"), float("inf"), -float("inf"), True, False):
        with pytest.raises(ValueError):
            IncomingServiceLine(line_length_m=bad_len)

    eng = ComprehensiveRisk2024Engine()
    res_50m = eng.evaluate_risk(
        ComprehensiveRiskInput(
            **_valid_comp_kwargs(),
            incoming_lines=[IncomingServiceLine(service_type="aerial_power", line_length_m=50.0)],
        )
    )
    res_100m = eng.evaluate_risk(
        ComprehensiveRiskInput(
            **_valid_comp_kwargs(),
            incoming_lines=[IncomingServiceLine(service_type="aerial_power", line_length_m=100.0)],
        )
    )
    assert res_50m.collection_area_al_services_m2 == pytest.approx(2000.0, rel=1e-12)
    assert res_100m.collection_area_al_services_m2 == pytest.approx(4000.0, rel=1e-12)
    assert res_50m.annual_strikes_nl_services == pytest.approx(
        0.5 * res_100m.annual_strikes_nl_services, rel=1e-12
    )


# ---------------------------------------------------------------------------
# Rule B.2: ComprehensiveRiskInput required fields & validators
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "required_field",
    [
        "structure_length_m",
        "structure_width_m",
        "structure_height_m",
        "ng_flashes_per_km2_year",
        "environmental_cd",
        "lps_class",
        "has_coordinated_spd",
        "has_tws_early_warning",
    ],
)
def test_b2_comprehensive_risk_required_fields(required_field: str):
    missing = _valid_comp_kwargs()
    missing.pop(required_field)
    with pytest.raises(ValueError):
        ComprehensiveRiskInput(**missing)


def test_b2_comprehensive_risk_field_validators():
    for field_name in (
        "structure_length_m",
        "structure_width_m",
        "structure_height_m",
        "ng_flashes_per_km2_year",
        "environmental_cd",
    ):
        for bad_val in (0.0, -1.0, float("nan"), float("inf"), True, False):
            with pytest.raises(ValueError):
                ComprehensiveRiskInput(**{**_valid_comp_kwargs(), field_name: bad_val})

    for valid_cls in ("none", "I", "II", "III", "IV"):
        assert ComprehensiveRiskInput(**{**_valid_comp_kwargs(), "lps_class": valid_cls}).lps_class == valid_cls

    for bad_cls in ("unprotected", "V", "i", "", None, 1, True):
        with pytest.raises(ValueError):
            ComprehensiveRiskInput(**{**_valid_comp_kwargs(), "lps_class": bad_cls})

    for bool_field in ("has_coordinated_spd", "has_tws_early_warning"):
        for bad_bool in (1, 0, "true", None):
            with pytest.raises(ValueError):
                ComprehensiveRiskInput(**{**_valid_comp_kwargs(), bool_field: bad_bool})


# ---------------------------------------------------------------------------
# Rule B.3, B.4, B.5: ComprehensiveRiskInput occupancy, fire_risk, standard defaults
# ---------------------------------------------------------------------------


def test_b3_b4_b5_comprehensive_risk_hours_fire_and_standard_defaults():
    inp = ComprehensiveRiskInput(**_valid_comp_kwargs())
    assert inp.time_in_structure_hours_per_year == 8760.0
    assert inp.structure_type == "wood_masonry"
    assert inp.protection_variant == "standard"
    assert inp.provisions == "none"

    assert ComprehensiveRiskInput(**_valid_comp_kwargs(), time_in_structure_hours_per_year=0.0).time_in_structure_hours_per_year == 0.0

    for bad_hours in (-0.1, 8760.1, 10000.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            ComprehensiveRiskInput(**_valid_comp_kwargs(), time_in_structure_hours_per_year=bad_hours)

    missing_fire = _valid_comp_kwargs()
    missing_fire.pop("fire_risk_rf")
    with pytest.raises(ValueError):
        ComprehensiveRiskInput(**missing_fire)

    by_level = ComprehensiveRiskInput(**missing_fire, fire_risk_level="fire_high")
    assert by_level.fire_risk_level == "fire_high"
    assert by_level.fire_risk_rf is None


# ---------------------------------------------------------------------------
# HTTP Endpoint Checks (/risk and /comprehensive-risk-2024)
# ---------------------------------------------------------------------------


def test_risk_and_comprehensive_risk_http_endpoints():
    resp_risk_empty = client.post("/api/v1/calculations/risk", json={})
    assert resp_risk_empty.status_code == 422

    resp_comp_empty = client.post("/api/v1/calculations/comprehensive-risk-2024", json={})
    assert resp_comp_empty.status_code == 422

    resp_risk_ok = client.post("/api/v1/calculations/risk", json=_valid_risk_kwargs())
    assert resp_risk_ok.status_code == 200
    risk_body = resp_risk_ok.json()
    # IEC 62305-2:2024 Annex A & Tables B.3-B.6, C.2 (30x20x15, Ng=2.5, Cd=1, Class I, normal, t_z=8760):
    # A_D = 11461.7251 m^2, N_D = 0.028654312809 /yr, R_B = N_D * 2e-4 * 5e-2 = 2.8654312809e-7
    assert risk_body["collection_area_ad_m2"] == pytest.approx(11461.7, abs=0.1)
    assert risk_body["risk_rb_physical_damage"] == pytest.approx(2.8654312809e-7, rel=1e-6)
    # Sanity check only (total R1 includes open H3 component R_A):
    assert risk_body["risk_r1_loss_of_life"] > 0.0

    resp_comp_ok = client.post(
        "/api/v1/calculations/comprehensive-risk-2024",
        json=_valid_comp_kwargs(),
    )
    assert resp_comp_ok.status_code == 200
    comp_body = resp_comp_ok.json()
    # IEC 62305-2:2024 Annex A & Tables B.3-B.6, C.2 (40x25x15, Ng=2.5, Cd=1, Class I, normal, t_z=8760):
    # A_D = 1000 + 5850 + 2025*pi = 13211.7251 m^2, N_D = 0.033029312809 /yr, R_B = 3.3029312809e-7
    assert comp_body["collection_area_ad_structure_m2"] == pytest.approx(13211.7, abs=0.1)
    assert comp_body["risk_components"]["r_b_physical_damage"] == pytest.approx(
        3.3029312809e-7, rel=1e-6
    )
    # Sanity check only (total R1 includes open H3 components):
    assert comp_body["risk_components"]["total_risk_r1"] > 0.0
