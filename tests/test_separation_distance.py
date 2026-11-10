import json
import math
import pytest

from aegislps_domain.models import (
    Building,
    CalculationStatus,
    ConductorNode,
    ConductorSegment,
    Project,
    SeparationPoint,
)
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_standards.repository import StandardsRepository


def _run_single_point(
    *,
    lps_class: str = "I",
    insulation_medium: str = "air",
    down_conductor_count=None,
    earth_resistances_within_factor_2=None,
    route_length_to_bonding_m=None,
    node_z: float = 15.0,
    physical_distance_m: float = 1.5,
    segments=None,
):
    repo = StandardsRepository()
    engine = SeparationDistanceEngine(repo)
    proj = Project(
        name="IEC 62305-3:2024 Clause 6.3.2 Case",
        lps_class=lps_class,
        down_conductor_count=down_conductor_count,
        earth_resistances_within_factor_2=earth_resistances_within_factor_2,
        building=Building(length_m=20.0, width_m=10.0, height_m=max(15.0, node_z)),
        nodes=[ConductorNode(id="n1", x=0.0, y=0.0, z=node_z)],
        segments=segments or [],
        separation_points=[
            SeparationPoint(
                id="sp1",
                name="Test Separation Point",
                x=1.0,
                y=1.0,
                z=node_z,
                associated_node_id="n1",
                insulation_medium=insulation_medium,
                physical_distance_m=physical_distance_m,
                route_length_to_bonding_m=route_length_to_bonding_m,
            )
        ],
    )
    results = engine.calculate_project(proj)
    assert len(results) == 1
    return results[0]


# ---------------------------------------------------------------------------
# Updated legacy tests
# ---------------------------------------------------------------------------


def test_simplified_separation_distance_class_I():
    res = _run_single_point(
        lps_class="I",
        insulation_medium="air",
        down_conductor_count=None,
        route_length_to_bonding_m=None,
        node_z=15.0,
        physical_distance_m=1.5,
    )
    assert res.required_distance_s_m == pytest.approx(1.200, abs=1e-9)
    assert res.pass_compliance is True
    assert res.safety_margin_m == pytest.approx(0.300, abs=1e-9)
    assert res.status == CalculationStatus.WARNING


def test_simplified_separation_distance_class_III_solid_medium():
    """
    With down_conductor_count omitted, IEC 62305-3:2024 Clause 6.3.2 / Table 13
    requires conservative k_c = 1.0 (not the non-standard segment-count k_c = 0.5),
    giving s = (0.04 / 0.5) * 1.0 * 20.0 = 1.600 m and status WARNING.
    """
    res = _run_single_point(
        lps_class="III",
        insulation_medium="solid",
        down_conductor_count=None,
        route_length_to_bonding_m=None,
        node_z=20.0,
        physical_distance_m=0.6,
        segments=[
            ConductorSegment(start_node_id="n1", end_node_id="n2"),
            ConductorSegment(start_node_id="n1", end_node_id="n3"),
        ],
    )
    assert res.kc_used == pytest.approx(1.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(1.600, abs=1e-9)
    assert res.pass_compliance is False
    assert res.safety_margin_m == pytest.approx(-1.000, abs=1e-9)
    assert res.status == CalculationStatus.WARNING


# ---------------------------------------------------------------------------
# Seven normative expected-value cases (IEC 62305-3:2024 Clause 6.3.2, Eq. (6))
# ---------------------------------------------------------------------------


def test_expected_case_1_class_i_air_missing_kc_and_route_z15():
    expected_s = (0.08 / 1.0) * 1.0 * 15.0
    assert expected_s == pytest.approx(1.200, abs=1e-12)

    res = _run_single_point(
        lps_class="I",
        insulation_medium="air",
        down_conductor_count=None,
        route_length_to_bonding_m=None,
        node_z=15.0,
        physical_distance_m=1.200,
    )
    assert res.ki_used == pytest.approx(0.08, abs=1e-12)
    assert res.km_used == pytest.approx(1.0, abs=1e-12)
    assert res.kc_used == pytest.approx(1.0, abs=1e-12)
    assert res.length_l_m == pytest.approx(15.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(expected_s, abs=1e-12)
    assert res.pass_compliance is True
    assert res.status == CalculationStatus.WARNING
    assert "route length was not given" in res.formula_trace


def test_expected_case_2_class_i_air_n2_earth_ok_route_absent_z15():
    expected_s = (0.08 / 1.0) * 0.66 * 15.0
    assert expected_s == pytest.approx(0.792, abs=1e-12)

    res = _run_single_point(
        lps_class="I",
        insulation_medium="air",
        down_conductor_count=2,
        earth_resistances_within_factor_2=True,
        route_length_to_bonding_m=None,
        node_z=15.0,
        physical_distance_m=0.80,
    )
    assert res.kc_used == pytest.approx(0.66, abs=1e-12)
    assert res.length_l_m == pytest.approx(15.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(expected_s, abs=1e-12)
    assert res.status == CalculationStatus.WARNING
    assert "route length was not given" in res.formula_trace


def test_expected_case_3_class_i_air_n2_earth_ok_route_6m():
    expected_s = (0.08 / 1.0) * 0.66 * 6.0
    assert expected_s == pytest.approx(0.3168, abs=1e-12)

    res = _run_single_point(
        lps_class="I",
        insulation_medium="air",
        down_conductor_count=2,
        earth_resistances_within_factor_2=True,
        route_length_to_bonding_m=6.0,
        node_z=15.0,
        physical_distance_m=0.30,
    )
    assert res.kc_used == pytest.approx(0.66, abs=1e-12)
    assert res.length_l_m == pytest.approx(6.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(expected_s, abs=1e-12)
    assert res.pass_compliance is False
    assert res.status == CalculationStatus.CALCULATED


def test_expected_case_4_class_i_air_n3_earth_ok_route_6m():
    expected_s = (0.08 / 1.0) * 0.44 * 6.0
    assert expected_s == pytest.approx(0.2112, abs=1e-12)

    res = _run_single_point(
        lps_class="I",
        insulation_medium="air",
        down_conductor_count=3,
        earth_resistances_within_factor_2=True,
        route_length_to_bonding_m=6.0,
        node_z=15.0,
        physical_distance_m=0.25,
    )
    assert res.kc_used == pytest.approx(0.44, abs=1e-12)
    assert res.length_l_m == pytest.approx(6.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(expected_s, abs=1e-12)
    assert res.pass_compliance is True
    assert res.status == CalculationStatus.CALCULATED


def test_expected_case_5_class_i_air_n2_earth_ratio_false_route_6m():
    expected_s = (0.08 / 1.0) * 1.0 * 6.0
    assert expected_s == pytest.approx(0.480, abs=1e-12)

    res = _run_single_point(
        lps_class="I",
        insulation_medium="air",
        down_conductor_count=2,
        earth_resistances_within_factor_2=False,
        route_length_to_bonding_m=6.0,
        node_z=15.0,
        physical_distance_m=0.50,
    )
    assert res.kc_used == pytest.approx(1.0, abs=1e-12)
    assert res.length_l_m == pytest.approx(6.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(expected_s, abs=1e-12)
    assert res.status == CalculationStatus.WARNING
    assert "factor of 2" in res.formula_trace


def test_expected_case_6_class_iii_solid_n2_earth_ok_route_20m():
    expected_s = (0.04 / 0.5) * 0.66 * 20.0
    assert expected_s == pytest.approx(1.056, abs=1e-12)

    res = _run_single_point(
        lps_class="III",
        insulation_medium="solid",
        down_conductor_count=2,
        earth_resistances_within_factor_2=True,
        route_length_to_bonding_m=20.0,
        node_z=20.0,
        physical_distance_m=1.10,
    )
    assert res.ki_used == pytest.approx(0.04, abs=1e-12)
    assert res.km_used == pytest.approx(0.5, abs=1e-12)
    assert res.kc_used == pytest.approx(0.66, abs=1e-12)
    assert res.length_l_m == pytest.approx(20.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(expected_s, abs=1e-12)
    assert res.pass_compliance is True
    assert res.status == CalculationStatus.CALCULATED


def test_expected_case_7_class_iii_solid_defaults_z20():
    expected_s = (0.04 / 0.5) * 1.0 * 20.0
    assert expected_s == pytest.approx(1.600, abs=1e-12)

    res = _run_single_point(
        lps_class="III",
        insulation_medium="solid",
        down_conductor_count=None,
        route_length_to_bonding_m=None,
        node_z=20.0,
        physical_distance_m=1.50,
    )
    assert res.kc_used == pytest.approx(1.0, abs=1e-12)
    assert res.length_l_m == pytest.approx(20.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(expected_s, abs=1e-12)
    assert res.pass_compliance is False
    assert res.status == CalculationStatus.WARNING


# ---------------------------------------------------------------------------
# Additional normative, trace, validation, and independence tests
# ---------------------------------------------------------------------------


def test_table_13_n1_isolated_lps_warns_and_uses_kc_1():
    res = _run_single_point(
        lps_class="II",
        insulation_medium="air",
        down_conductor_count=1,
        earth_resistances_within_factor_2=True,
        route_length_to_bonding_m=10.0,
    )
    assert res.ki_used == pytest.approx(0.06, abs=1e-12)
    assert res.kc_used == pytest.approx(1.0, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(0.60, abs=1e-12)
    assert res.status == CalculationStatus.WARNING
    assert "isolated LPS" in res.formula_trace


def test_table_12_note_1_insulating_standoff_km_07():
    expected_s = (0.08 / 0.7) * 0.44 * 7.0
    res = _run_single_point(
        lps_class="I",
        insulation_medium="insulating_standoff",
        down_conductor_count=4,
        earth_resistances_within_factor_2=True,
        route_length_to_bonding_m=7.0,
    )
    assert res.km_used == pytest.approx(0.7, abs=1e-12)
    assert res.kc_used == pytest.approx(0.44, abs=1e-12)
    assert res.required_distance_s_m == pytest.approx(expected_s, abs=1e-12)
    assert res.status == CalculationStatus.CALCULATED


@pytest.mark.parametrize("bad_count", [0, -1, -5, True, False, 2.5, "2"])
def test_invalid_down_conductor_count_rejected(bad_count):
    with pytest.raises(ValueError):
        Project(name="Bad Count", down_conductor_count=bad_count)


@pytest.mark.parametrize(
    "bad_route_length",
    [0, 0.0, -0.1, -10.0, float("nan"), float("inf"), float("-inf"), True, False],
)
def test_invalid_route_length_to_bonding_rejected(bad_route_length):
    with pytest.raises(ValueError):
        SeparationPoint(
            id="sp_bad",
            name="Invalid Route Length",
            x=0.0,
            y=0.0,
            z=10.0,
            associated_node_id="n1",
            physical_distance_m=1.0,
            route_length_to_bonding_m=bad_route_length,
        )


def test_segment_list_does_not_change_kc():
    """
    Replaces old tautological segment test: verifies that varying
    project.segments (0, 1, 2, 5 segments) has zero effect on k_c or s.
    """
    for down_count, earth_ok, expected_kc in [
        (None, None, 1.0),
        (2, True, 0.66),
        (4, True, 0.44),
    ]:
        seen_s = []
        for seg_count in (0, 1, 2, 5):
            segs = [
                ConductorSegment(
                    id=f"seg_{i}", start_node_id="n1", end_node_id="n1"
                )
                for i in range(seg_count)
            ]
            res = _run_single_point(
                lps_class="I",
                insulation_medium="air",
                down_conductor_count=down_count,
                earth_resistances_within_factor_2=earth_ok,
                route_length_to_bonding_m=8.0,
                segments=segs,
            )
            assert res.kc_used == pytest.approx(expected_kc, abs=1e-12)
            seen_s.append(res.required_distance_s_m)
        assert all(math.isclose(val, seen_s[0], rel_tol=0.0, abs_tol=1e-12) for val in seen_s)


def test_calculated_formula_trace_contains_6_3_2_eq_6_table_13_and_l_source():
    res = _run_single_point(
        lps_class="I",
        insulation_medium="air",
        down_conductor_count=2,
        earth_resistances_within_factor_2=True,
        route_length_to_bonding_m=6.0,
    )
    assert res.status == CalculationStatus.CALCULATED
    assert "6.3.2" in res.formula_trace
    assert "Eq. (6)" in res.formula_trace
    assert "Table 13" in res.formula_trace
    assert "route_length_to_bonding_m" in res.formula_trace


def test_standards_repository_clause_6_3_parameters_and_no_silent_fallback():
    repo = StandardsRepository()
    param_ids = [
        "ki_class_I",
        "ki_class_II",
        "ki_class_III_IV",
        "km_air",
        "km_solid",
        "km_insulating_standoff",
        "kc_n_1_isolated",
        "kc_n_2",
        "kc_n_3_or_more",
        "kc_earth_resistance_fallback",
    ]
    for pid in param_ids:
        param = repo.get_parameter("IEC 62305-3:2024", pid)
        assert param is not None, f"Missing parameter {pid}"
        assert param.source_clause == "IEC 62305-3:2024, Clause 6.3"

    # Deleting a required parameter must raise rather than silently falling back
    del repo._parts["IEC 62305-3:2024"].parameters["kc_n_2"]
    engine = SeparationDistanceEngine(repo)
    proj = Project(
        lps_class="I",
        down_conductor_count=2,
        earth_resistances_within_factor_2=True,
        nodes=[ConductorNode(id="n1", x=0.0, y=0.0, z=10.0)],
        separation_points=[
            SeparationPoint(
                id="sp1",
                name="P1",
                x=0.0,
                y=0.0,
                z=10.0,
                associated_node_id="n1",
                physical_distance_m=1.0,
                route_length_to_bonding_m=5.0,
            )
        ],
    )
    with pytest.raises(ValueError, match="kc_n_2"):
        engine.calculate_project(proj)


def test_legacy_project_json_loads_without_new_optional_fields():
    legacy_json = json.dumps(
        {
            "project_id": "legacy-001",
            "name": "Legacy Project",
            "lps_class": "II",
            "building": {"length_m": 20.0, "width_m": 10.0, "height_m": 12.0, "roof_type": "flat"},
            "nodes": [{"id": "n1", "x": 0.0, "y": 0.0, "z": 12.0, "node_type": "air_termination"}],
            "segments": [],
            "separation_points": [
                {
                    "id": "sp1",
                    "name": "Legacy Point",
                    "x": 1.0,
                    "y": 1.0,
                    "z": 12.0,
                    "associated_node_id": "n1",
                    "insulation_medium": "air",
                    "physical_distance_m": 1.0,
                }
            ],
            "results": [],
            "schema_version": "1.0.0",
        }
    )
    proj = Project.model_validate_json(legacy_json)
    assert proj.down_conductor_count is None
    assert proj.earth_resistances_within_factor_2 is None
    assert proj.separation_points[0].route_length_to_bonding_m is None
