"""Reference, consistency, and validation tests for IEC 62305-2:2024 risk factors (Step 2.5 — H3)."""

import math
import pytest

from aegislps_engine.comprehensive_risk import (
    ComprehensiveRisk2024Engine,
    ComprehensiveRiskInput,
    IncomingServiceLine,
)
from aegislps_engine.risk import RiskAssessmentInput, RiskManagementEngine
from aegislps_engine.risk_factors import (
    loss,
    map_fire_risk_rf,
    p_b,
    p_lps,
    p_s,
    p_spd,
    r_f,
    r_p,
)


# ---------------------------------------------------------------------------
# 1. Table B.3 Reference Tests — IEC 62305-2:2024 Annex B, Table B.3 (p. 56)
# ---------------------------------------------------------------------------


def test_table_b3_row1_unprotected():
    """IEC 62305-2:2024 Table B.3, row 1 (p. 56): unprotected structure -> P_LPS = 1."""
    assert p_lps("none") == 1.0
    assert p_lps("unprotected") == 1.0
    assert p_lps(None) == 1.0


def test_table_b3_row2_class_iv():
    """IEC 62305-2:2024 Table B.3, row 2 (p. 56): LPS Class IV -> P_LPS = 0.2."""
    assert p_lps("IV", "standard") == 0.2


def test_table_b3_row3_class_iii():
    """IEC 62305-2:2024 Table B.3, row 3 (p. 56): LPS Class III -> P_LPS = 0.1."""
    assert p_lps("III", "standard") == 0.1


def test_table_b3_row4_class_ii():
    """IEC 62305-2:2024 Table B.3, row 4 (p. 56): LPS Class II -> P_LPS = 0.05."""
    assert p_lps("II", "standard") == 0.05


def test_table_b3_row5_class_i_standard():
    """IEC 62305-2:2024 Table B.3, row 5 (p. 56): LPS Class I (standard) -> P_LPS = 0.02."""
    assert p_lps("I") == 0.02
    assert p_lps("I", "standard") == 0.02


def test_table_b3_row6_class_i_framework_natural_downconductor():
    """IEC 62305-2:2024 Table B.3, row 6 (p. 56): LPS I + continuous metal/RC framework -> P_LPS = 0.01."""
    assert p_lps("I", "framework_natural_downconductor") == 0.01


def test_table_b3_row7_class_i_metal_roof_full_protection():
    """IEC 62305-2:2024 Table B.3, row 7 (p. 56): LPS I + metal roof + complete air-termination + framework -> P_LPS = 0.001."""
    assert p_lps("I", "metal_roof_full_protection") == 0.001


# ---------------------------------------------------------------------------
# 2. Table B.4 Reference Tests — IEC 62305-2:2024 Annex B, Table B.4 (p. 57)
# ---------------------------------------------------------------------------


def test_table_b4_row1_wood_masonry():
    """IEC 62305-2:2024 Table B.4, row 1 (p. 57): Wood and masonry -> P_S = 1."""
    assert p_s() == 1.0
    assert p_s("wood_masonry") == 1.0


def test_table_b4_row2_continuous_rc_or_metal_framework():
    """IEC 62305-2:2024 Table B.4, row 2 (p. 57): Continuous RC or interconnected metal framework -> P_S = 0.5."""
    assert p_s("continuous_rc_or_metal_framework") == 0.5


# ---------------------------------------------------------------------------
# 3. Table B.5 Reference Tests — IEC 62305-2:2024 Annex B, Table B.5 (p. 58)
# ---------------------------------------------------------------------------


def test_table_b5_row1_no_provisions():
    """IEC 62305-2:2024 Table B.5, row 1 (p. 58): No provisions -> r_p = 1."""
    assert r_p() == 1.0
    assert r_p("none") == 1.0


def test_table_b5_row2_passive_or_manual():
    """IEC 62305-2:2024 Table B.5, row 2 (p. 58): Manual/passive fire provisions -> r_p = 0.5."""
    assert r_p("passive_or_manual") == 0.5


def test_table_b5_row3_automatic():
    """IEC 62305-2:2024 Table B.5, row 3 (p. 58): Automatic extinguishing or protected alarm -> r_p = 0.2."""
    assert r_p("automatic") == 0.2


# ---------------------------------------------------------------------------
# 4. Table B.6 Reference Tests — IEC 62305-2:2024 Annex B, Table B.6 (p. 58)
# ---------------------------------------------------------------------------


def test_table_b6_row1_explosion_zone_0_20():
    """IEC 62305-2:2024 Table B.6, row 1 (p. 58): Explosion Zones 0, 20 and solid explosive -> r_f = 1."""
    assert r_f("explosion_zone_0_20") == 1.0
    assert map_fire_risk_rf(1) == "explosion_zone_0_20"
    assert r_f(1.0) == 1.0


def test_table_b6_row2_explosion_zone_1_21():
    """IEC 62305-2:2024 Table B.6, row 2 (p. 58): Explosion Zones 1, 21 -> r_f = 1e-1."""
    assert r_f("explosion_zone_1_21") == 1e-1


def test_table_b6_row3_explosion_zone_2_22():
    """IEC 62305-2:2024 Table B.6, row 3 (p. 58): Explosion Zones 2, 22 -> r_f = 1e-3."""
    assert r_f("explosion_zone_2_22") == 1e-3


def test_table_b6_row4_fire_high():
    """IEC 62305-2:2024 Table B.6, row 4 (p. 58): Fire — High -> r_f = 1e-1."""
    assert r_f("fire_high") == 1e-1
    assert map_fire_risk_rf(1e-1) == "fire_high"
    assert r_f(1e-1) == 1e-1


def test_table_b6_row5_fire_ordinary():
    """IEC 62305-2:2024 Table B.6, row 5 (p. 58): Fire — Ordinary -> r_f = 1e-2."""
    assert r_f("fire_ordinary") == 1e-2
    assert map_fire_risk_rf(1e-2) == "fire_ordinary"
    assert r_f(1e-2) == 1e-2


def test_table_b6_row6_fire_low():
    """IEC 62305-2:2024 Table B.6, row 6 (p. 58): Fire — Low -> r_f = 1e-3."""
    assert r_f("fire_low") == 1e-3
    assert map_fire_risk_rf(1e-3) == "fire_low"
    assert r_f(1e-3) == 1e-3


def test_table_b6_row7_none():
    """IEC 62305-2:2024 Table B.6, row 7 (p. 58): Explosion or fire — None -> r_f = 0."""
    assert r_f("none") == 0.0
    assert map_fire_risk_rf(0) == "none"
    assert r_f(0.0) == 0.0


# ---------------------------------------------------------------------------
# 5. Table B.7 Reference Tests — IEC 62305-2:2024 Annex B, Table B.7 (p. 60)
# ---------------------------------------------------------------------------


def test_table_b7_row1_no_spd():
    """IEC 62305-2:2024 Table B.7, row 1 (p. 60): No SPDs (or uncoordinated) -> P_SPD = 1."""
    for src in ("S1", "S2", "S3", "S4"):
        assert p_spd("I", False, False, src) == 1.0
        assert p_spd("I", True, False, src) == 1.0


def test_table_b7_row2_lpl_iii_and_iv():
    """IEC 62305-2:2024 Table B.7, row 2 (p. 60): LPL III–IV -> P_SPD = 0.05."""
    for src in ("S1", "S2", "S3", "S4"):
        assert p_spd("IV", True, True, src) == 0.05
        assert p_spd("III", True, True, src) == 0.05


def test_table_b7_row3_lpl_ii():
    """IEC 62305-2:2024 Table B.7, row 3 (p. 60): LPL II -> P_SPD = 0.02."""
    for src in ("S1", "S2", "S3", "S4"):
        assert p_spd("II", True, True, src) == 0.02


def test_table_b7_row4_lpl_i():
    """IEC 62305-2:2024 Table B.7, row 4 (p. 60): LPL I -> P_SPD = 0.01."""
    for src in ("S1", "S2", "S3", "S4"):
        assert p_spd("I", True, True, src) == 0.01


@pytest.mark.parametrize(
    "current_ka,expected",
    [
        (2.5, 1e-4),
        (3.75, 5e-5),
        (5.0, 1e-5),
    ],
)
def test_table_b7_rows5_to_7_better_than_lpl_i(current_ka: float, expected: float):
    """IEC 62305-2:2024 Table B.7, rows 5–7 (p. 60): Better than LPL I (S2 and S4 only)."""
    assert p_spd("I", True, True, "S2", enhanced_spd_current_ka=current_ka) == expected
    assert p_spd("I", True, True, "S4", enhanced_spd_current_ka=current_ka) == expected


def test_p_spd_equal_across_sources_at_every_lpl_row():
    """IEC 62305-2:2024 Table B.7 (p. 60): S1, S2, S3, S4 yield identical P_SPD at every LPL row."""
    for spd_flag in (False, True):
        for cls in ("none", "IV", "III", "II", "I"):
            vals = [p_spd(cls, spd_flag, spd_flag, src) for src in ("S1", "S2", "S3", "S4")]
            assert len(set(vals)) == 1


# ---------------------------------------------------------------------------
# 6. Table C.2 Reference Tests — IEC 62305-2:2024 Annex C, Table C.2 (p. 73)
# ---------------------------------------------------------------------------


def test_table_c2_row1_very_high_upper_bound():
    """IEC 62305-2:2024 Table C.2, row 1 (p. 73): Very high loss upper-bound defaults."""
    lv = loss("very_high")
    assert (lv.l_t, lv.l_d, lv.l_f1, lv.l_f2, lv.l_o1, lv.l_o2) == (
        1e-2,
        1e-1,
        2e-1,
        2e-1,
        1e-2,
        1e-2,
    )


def test_table_c2_row2_high_upper_bound():
    """IEC 62305-2:2024 Table C.2, row 2 (p. 73): High loss upper-bound defaults."""
    lv = loss("high")
    assert (lv.l_t, lv.l_d, lv.l_f1, lv.l_f2, lv.l_o1, lv.l_o2) == (
        1e-2,
        1e-1,
        1e-1,
        1e-1,
        1e-3,
        1e-3,
    )


def test_table_c2_row3_normal_upper_bound():
    """IEC 62305-2:2024 Table C.2, row 3 (p. 73): Normal loss upper-bound defaults."""
    lv = loss("normal")
    assert (lv.l_t, lv.l_d, lv.l_f1, lv.l_f2, lv.l_o1, lv.l_o2) == (
        1e-2,
        1e-1,
        5e-2,
        5e-2,
        5e-4,
        5e-4,
    )


def test_table_c2_row4_low_upper_bound():
    """IEC 62305-2:2024 Table C.2, row 4 (p. 73): Low loss upper-bound defaults."""
    lv = loss("low")
    assert (lv.l_t, lv.l_d, lv.l_f1, lv.l_f2, lv.l_o1, lv.l_o2) == (
        1e-2,
        1e-1,
        2e-2,
        2e-2,
        1e-4,
        1e-4,
    )


# ---------------------------------------------------------------------------
# 7. Equation (B.4) Exhaustive Product Test — IEC 62305-2:2024 Clause B.4 (p. 57)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lps_class,variant",
    [
        ("none", "standard"),
        ("IV", "standard"),
        ("III", "standard"),
        ("II", "standard"),
        ("I", "standard"),
        ("I", "framework_natural_downconductor"),
        ("I", "metal_roof_full_protection"),
    ],
)
@pytest.mark.parametrize("structure_type", ["wood_masonry", "continuous_rc_or_metal_framework"])
@pytest.mark.parametrize("provisions", ["none", "passive_or_manual", "automatic"])
@pytest.mark.parametrize(
    "fire_level",
    ["explosion_zone_0_20", "explosion_zone_1_21", "fire_ordinary", "fire_low", "none"],
)
def test_equation_b4_pb_product_all_combinations(
    lps_class: str,
    variant: str,
    structure_type: str,
    provisions: str,
    fire_level: str,
):
    """IEC 62305-2:2024 Eq. (B.4) (p. 57): P_B = P_S * P_LPS * r_p * r_f across all valid combinations."""
    expected = p_s(structure_type) * p_lps(lps_class, variant) * r_p(provisions) * r_f(fire_level)
    actual = p_b(
        lps_class=lps_class,
        fire_risk_level=fire_level,
        structure_type=structure_type,
        protection_variant=variant,
        provisions=provisions,
    )
    assert actual == pytest.approx(expected, rel=1e-15, abs=0.0)


def test_rp_applied_once_in_pb_and_legacy_half_factor_removed():
    """Confirm automatic provisions enter solely via r_p in P_B (no 0.5 double-counting in L_F)."""
    eng = RiskManagementEngine()
    base = eng.evaluate_r1_risk(
        RiskAssessmentInput(
            provisions="none",
            has_automatic_fire_system=False,
            loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
        )
    )
    legacy_flag_true = eng.evaluate_r1_risk(
        RiskAssessmentInput(
            provisions="none",
            has_automatic_fire_system=True,
            loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
        )
    )
    auto_prov = eng.evaluate_r1_risk(
        RiskAssessmentInput(
            provisions="automatic",
            has_automatic_fire_system=True,
            loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
        )
    )
    assert legacy_flag_true.risk_rb_physical_damage == pytest.approx(
        base.risk_rb_physical_damage, rel=1e-15
    )
    assert auto_prov.risk_rb_physical_damage == pytest.approx(
        0.2 * base.risk_rb_physical_damage, rel=1e-15
    )


# ---------------------------------------------------------------------------
# 8. Cross-Module Consistency Tests (risk.py vs comprehensive_risk.py)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lps_class,variant",
    [
        ("none", "standard"),
        ("IV", "standard"),
        ("III", "standard"),
        ("II", "standard"),
        ("I", "standard"),
        ("I", "framework_natural_downconductor"),
        ("I", "metal_roof_full_protection"),
    ],
)
@pytest.mark.parametrize("loss_category", ["very_high", "high", "normal", "low"])
@pytest.mark.parametrize("has_spd", [True, False])
def test_cross_engine_consistency_pb_pspd_and_loss(
    lps_class: str,
    variant: str,
    loss_category: str,
    has_spd: bool,
):
    """For identical inputs, risk.py and comprehensive_risk.py produce identical P_B, P_SPD, L_F, L_O, R_B, and R_C."""
    risk_eng = RiskManagementEngine()
    comp_eng = ComprehensiveRisk2024Engine()

    common = dict(
        structure_length_m=35.0,
        structure_width_m=22.0,
        structure_height_m=14.0,
        ng_flashes_per_km2_year=3.0,
        environmental_cd=0.5,
        lps_class=lps_class,
        structure_type="continuous_rc_or_metal_framework",
        protection_variant=variant,
        provisions="passive_or_manual",
        fire_risk_rf=0.01,
        has_coordinated_spd=has_spd,
        loss_category=loss_category,
        time_in_structure_hours_per_year=4380.0,
    )

    res_r = risk_eng.evaluate_r1_risk(RiskAssessmentInput(**common))
    res_c = comp_eng.evaluate_risk(ComprehensiveRiskInput(**common))

    assert res_r.annual_strikes_nd == pytest.approx(res_c.annual_strikes_nd_direct, rel=1e-15)
    assert res_r.risk_rb_physical_damage == pytest.approx(
        res_c.risk_components.r_b_physical_damage, rel=1e-15
    )
    assert res_r.risk_rc_internal_systems == pytest.approx(
        res_c.risk_components.r_c_internal_surges, rel=1e-15
    )

    nd = res_r.annual_strikes_nd
    expected_pb = p_b(
        lps_class=lps_class,
        fire_risk_level="fire_ordinary",
        structure_type="continuous_rc_or_metal_framework",
        protection_variant=variant,
        provisions="passive_or_manual",
    )
    expected_pspd = p_spd(lps_class, has_spd, has_spd, "S1")
    expected_t_occ = 4380.0 / 8760.0
    expected_lf = loss(loss_category).l_f1 * expected_t_occ
    expected_lo = loss(loss_category).l_o1 * expected_t_occ

    assert res_r.risk_rb_physical_damage / nd == pytest.approx(expected_pb * expected_lf, rel=1e-15)
    assert res_c.risk_components.r_b_physical_damage / nd == pytest.approx(
        expected_pb * expected_lf, rel=1e-15
    )
    assert res_r.risk_rc_internal_systems / nd == pytest.approx(
        expected_pspd * expected_lo, rel=1e-15
    )
    assert res_c.risk_components.r_c_internal_surges / nd == pytest.approx(
        expected_pspd * expected_lo, rel=1e-15
    )


def test_t_occupancy_consistency_at_8760_hours():
    """At hours = 8760, t_occ = 1.0 and both engines match unscaled Table C.2 L_F1 and L_O1."""
    risk_eng = RiskManagementEngine()
    comp_eng = ComprehensiveRisk2024Engine()

    r_8760 = risk_eng.evaluate_r1_risk(
        RiskAssessmentInput(
            structure_length_m=40.0,
            structure_width_m=25.0,
            structure_height_m=15.0,
            ng_flashes_per_km2_year=2.5,
            lps_class="I",
            fire_risk_rf=0.01,
            has_coordinated_spd=True,
            time_in_structure_hours_per_year=8760.0,
            loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
        )
    )
    c_8760 = comp_eng.evaluate_risk(
        ComprehensiveRiskInput(
            structure_length_m=40.0,
            structure_width_m=25.0,
            structure_height_m=15.0,
            ng_flashes_per_km2_year=2.5,
            lps_class="I",
            fire_risk_rf=0.01,
            has_coordinated_spd=True,
            time_in_structure_hours_per_year=8760.0,
            loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
        )
    )
    r_clamped = risk_eng.evaluate_r1_risk(
        RiskAssessmentInput(
            structure_length_m=40.0,
            structure_width_m=25.0,
            structure_height_m=15.0,
            ng_flashes_per_km2_year=2.5,
            lps_class="I",
            fire_risk_rf=0.01,
            has_coordinated_spd=True,
            time_in_structure_hours_per_year=10000.0,
            loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
        )
    )

    nd = r_8760.annual_strikes_nd
    assert r_8760.risk_rb_physical_damage == pytest.approx(
        c_8760.risk_components.r_b_physical_damage, rel=1e-15
    )
    assert r_8760.risk_rc_internal_systems == pytest.approx(
        c_8760.risk_components.r_c_internal_surges, rel=1e-15
    )
    assert r_8760.risk_rb_physical_damage / nd == pytest.approx(
        p_b("I", 0.01) * loss("normal").l_f1, rel=1e-15
    )
    assert r_8760.risk_rc_internal_systems / nd == pytest.approx(
        p_spd("I", True, True, "S1") * loss("normal").l_o1, rel=1e-15
    )
    assert r_clamped.risk_rb_physical_damage == pytest.approx(
        r_8760.risk_rb_physical_damage, rel=1e-15
    )


# ---------------------------------------------------------------------------
# 9. Input Validation Tests (H9 Pattern — Section 4.4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_class", ["V", "0", "i", " I ", "", 1, True])
def test_unknown_lps_class_raises_value_error(bad_class):
    """Unknown or ill-typed lps_class raises ValueError in risk_factors and both input models."""
    with pytest.raises(ValueError):
        p_lps(bad_class)
    with pytest.raises(ValueError):
        p_spd(bad_class, True, True, "S1")
    with pytest.raises(ValueError):
        RiskAssessmentInput(lps_class=bad_class, loss_category="normal")
    with pytest.raises(ValueError):
        ComprehensiveRiskInput(lps_class=bad_class, loss_category="normal")


@pytest.mark.parametrize("non_i_class", ["II", "III", "IV", "none", None])
@pytest.mark.parametrize(
    "special_variant",
    ["framework_natural_downconductor", "metal_roof_full_protection"],
)
def test_special_protection_variants_reject_non_class_i(non_i_class, special_variant):
    """Table B.3 special variants are valid only for Class I; other classes raise ValueError."""
    with pytest.raises(ValueError):
        p_lps(non_i_class, special_variant)


def test_invalid_enums_and_float_mappings_raise_value_error():
    """Unknown enum tokens, S1a/S1b SPD sources, non-Table-B.6 floats, and missing loss_category raise ValueError."""
    with pytest.raises(ValueError):
        p_lps("I", "custom_variant")
    with pytest.raises(ValueError):
        p_s("steel_shed")
    with pytest.raises(ValueError):
        r_p("sprinkler_maybe")
    with pytest.raises(ValueError):
        r_f("fire_medium")
    for bad_rf in (0.02, 0.5, -0.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            map_fire_risk_rf(bad_rf)
        with pytest.raises(ValueError):
            r_f(bad_rf)
    for bad_src in ("S1a", "S1b", "S5", ""):
        with pytest.raises(ValueError):
            p_spd("I", True, True, bad_src)
    with pytest.raises(ValueError):
        p_spd("I", False, True, "S1")
    with pytest.raises(ValueError):
        p_spd("I", True, True, "S1", enhanced_spd_current_ka=2.5)
    with pytest.raises(ValueError):
        p_spd("I", True, True, "S2", enhanced_spd_current_ka=4.0)
    for bad_cat in ("", "medium", None, 1):
        with pytest.raises(ValueError):
            loss(bad_cat)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        RiskAssessmentInput()  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        ComprehensiveRiskInput()  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "field,bad_val",
    [
        ("structure_length_m", 0.0),
        ("structure_length_m", -5.0),
        ("structure_width_m", float("nan")),
        ("structure_height_m", float("inf")),
        ("ng_flashes_per_km2_year", -0.1),
        ("ng_flashes_per_km2_year", float("inf")),
        ("environmental_cd", -1.0),
        ("fire_risk_rf", 0.02),
        ("time_in_structure_hours_per_year", -10.0),
        ("time_in_structure_hours_per_year", float("nan")),
        ("structure_type", "brick"),
        ("provisions", "hydrant"),
        ("loss_category", "unknown"),
    ],
)
def test_engine_input_models_reject_invalid_values(field: str, bad_val):
    """Both RiskAssessmentInput and ComprehensiveRiskInput reject negative, non-finite, and unknown values."""
    base_kwargs = {"loss_category": "normal"}
    kwargs = {**base_kwargs, field: bad_val}
    with pytest.raises(ValueError):
        RiskAssessmentInput(**kwargs)
    with pytest.raises(ValueError):
        ComprehensiveRiskInput(**kwargs)


def test_incoming_service_line_validation():
    """IncomingServiceLine rejects unknown service_type and negative/non-finite line_length_m."""
    with pytest.raises(ValueError):
        IncomingServiceLine(service_type="fiber_unknown")
    with pytest.raises(ValueError):
        IncomingServiceLine(line_length_m=-1.0)
    with pytest.raises(ValueError):
        IncomingServiceLine(line_length_m=float("nan"))
