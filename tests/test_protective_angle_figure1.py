"""Reference and domain tests for ProtectiveAngleEngine per IEC 62305-3:2024.

Primary source:
- IEC 62305-3:2024, Clause 5.2.2.1, Table 2 (p. 21) and Figure 1 (p. 22).
- Graphical reading of Figure 1; tolerance ±1.5° (points interpolated during
  digitization, marked `is_interpolated=True`, carry ±0.3° reading precision
  and are asserted within <= 1.0°).
"""

import math
import pytest

from aegislps_geometry.protective_angle import (
    MAX_HEIGHTS,
    TABULATED_ANGLES,
    ProtectiveAngleEngine,
)

# Supervisor-digitized Figure 1 anchors: (h_m, alpha_deg, is_interpolated)
EXPECTED_FIGURE_1_ANCHORS = {
    "I": [
        (2.0, 70.0, False),
        (4.0, 63.4, False),
        (6.0, 56.5, False),
        (8.0, 50.9, False),
        (10.0, 45.3, False),
        (12.0, 40.9, False),
        (14.0, 36.0, False),
        (16.0, 31.9, False),
        (18.0, 27.4, False),
        (20.0, 22.4, False),
    ],
    "II": [
        (2.0, 73.4, False),
        (4.0, 68.1, False),
        (6.0, 62.5, False),
        (8.0, 58.2, False),
        (10.0, 54.1, False),
        (12.0, 50.7, False),
        (14.0, 47.3, False),
        (15.0, 45.7, True),
        (16.0, 44.2, False),
        (18.0, 41.1, False),
        (19.0, 39.7, False),
        (20.0, 37.9, False),
        (22.0, 35.3, False),
        (24.0, 32.4, False),
        (25.0, 30.4, False),
        (26.0, 29.4, False),
        (28.0, 26.4, True),
        (30.0, 23.3, False),
    ],
    "III": [
        (2.0, 76.5, False),
        (4.0, 72.7, False),
        (6.0, 68.5, False),
        (8.0, 64.9, False),
        (10.0, 61.3, False),
        (12.0, 58.5, False),
        (14.0, 55.7, False),
        (15.0, 54.4, True),
        (16.0, 53.2, False),
        (18.0, 50.7, False),
        (19.0, 49.4, False),
        (20.0, 47.9, False),
        (22.0, 45.7, False),
        (24.0, 43.6, False),
        (25.0, 42.3, False),
        (26.0, 41.0, False),
        (28.0, 38.9, False),
        (30.0, 36.9, False),
        (32.0, 35.1, False),
        (34.0, 33.1, False),
        (36.0, 31.2, False),
        (38.0, 29.5, False),
        (40.0, 27.5, False),
        (42.0, 25.6, False),
        (44.0, 23.7, False),
        (45.0, 23.3, False),
    ],
    "IV": [
        (2.0, 79.0, False),
        (4.0, 75.4, False),
        (6.0, 71.2, False),
        (8.0, 68.2, False),
        (10.0, 65.4, False),
        (12.0, 62.4, False),
        (14.0, 59.9, False),
        (16.0, 57.4, False),
        (18.0, 55.4, False),
        (20.0, 53.4, False),
        (22.0, 51.7, False),
        (24.0, 50.0, False),
        (26.0, 48.5, True),
        (28.0, 46.6, False),
        (30.0, 45.0, False),
        (32.0, 43.6, False),
        (34.0, 42.0, False),
        (36.0, 40.4, False),
        (38.0, 39.1, False),
        (40.0, 37.7, False),
        (44.0, 35.0, False),
        (45.0, 34.0, True),
        (46.0, 33.1, False),
        (50.0, 30.2, False),
        (58.0, 24.5, False),
        (60.0, 22.5, False),
    ],
}

ANCHOR_CASES = [
    (lps_cls, h_m, alpha_deg, is_interp)
    for lps_cls, pts in EXPECTED_FIGURE_1_ANCHORS.items()
    for (h_m, alpha_deg, is_interp) in pts
]


@pytest.mark.parametrize("lps_cls,h_m,expected_deg,is_interp", ANCHOR_CASES)
def test_figure1_anchor_values(
    lps_cls: str, h_m: float, expected_deg: float, is_interp: bool
) -> None:
    """IEC 62305-3:2024 Clause 5.2.2.1, Figure 1 (p. 22) graphical reading.

    Direct digitized anchors asserted within ±1.5°; interpolated points (i) within ±1.0°.
    """
    tol = 1.0 if is_interp else 1.5
    computed = ProtectiveAngleEngine.get_protective_angle_deg(lps_cls, h_m)
    assert abs(computed - expected_deg) <= tol


def test_module_constant_heights_match_expected_set_without_extra_points() -> None:
    """Verify TABULATED_ANGLES stores only the specified (h, alpha) anchor heights."""
    assert set(TABULATED_ANGLES.keys()) == {"I", "II", "III", "IV"}
    for lps_cls, pts in EXPECTED_FIGURE_1_ANCHORS.items():
        expected_heights = [h for (h, _, _) in pts]
        actual_heights = [h for (h, _) in TABULATED_ANGLES[lps_cls]]
        assert actual_heights == expected_heights


@pytest.mark.parametrize(
    "lps_cls,h_max,expected_end_deg",
    [
        ("I", 20.0, 22.4),
        ("II", 30.0, 23.3),
        ("III", 45.0, 23.3),
        ("IV", 60.0, 22.5),
    ],
)
def test_figure1_endpoints_at_h_max(
    lps_cls: str, h_max: float, expected_end_deg: float
) -> None:
    """IEC 62305-3:2024 Figure 1 (p. 22) upper-limit endpoints within ±1.5°."""
    alpha_end = ProtectiveAngleEngine.get_protective_angle_deg(lps_cls, h_max)
    assert abs(alpha_end - expected_end_deg) <= 1.5


def test_max_heights_match_iec_table2() -> None:
    """IEC 62305-3:2024 Clause 5.2.2.1, Table 2 (p. 21) & Figure 1 NOTE 1 (p. 22)."""
    expected = {"I": 20.0, "II": 30.0, "III": 45.0, "IV": 60.0}
    assert MAX_HEIGHTS == expected
    assert ProtectiveAngleEngine.MAX_HEIGHTS == expected


@pytest.mark.parametrize("lps_cls", ["I", "II", "III", "IV"])
def test_piecewise_linear_interpolation_midpoints_exact(lps_cls: str) -> None:
    """Midpoint between any two consecutive anchors equals exact linear average."""
    pts = EXPECTED_FIGURE_1_ANCHORS[lps_cls]
    for (h1, _, _), (h2, _, _) in zip(pts[:-1], pts[1:]):
        a1 = ProtectiveAngleEngine.get_protective_angle_deg(lps_cls, h1)
        a2 = ProtectiveAngleEngine.get_protective_angle_deg(lps_cls, h2)
        h_mid = 0.5 * (h1 + h2)
        a_mid = ProtectiveAngleEngine.get_protective_angle_deg(lps_cls, h_mid)
        assert a_mid == pytest.approx(0.5 * (a1 + a2), rel=0.0, abs=1e-12)


@pytest.mark.parametrize("lps_cls", ["I", "II", "III", "IV"])
@pytest.mark.parametrize("h_m", [0.1, 0.5, 1.0, 1.5, 1.999])
def test_below_2m_equals_angle_at_2m_per_note3(lps_cls: str, h_m: float) -> None:
    """IEC 62305-3:2024 Figure 1 NOTE 3 (p. 22): angle is constant for 0 < h < 2 m."""
    assert ProtectiveAngleEngine.get_protective_angle_deg(
        lps_cls, h_m
    ) == ProtectiveAngleEngine.get_protective_angle_deg(lps_cls, 2.0)


@pytest.mark.parametrize(
    "h_invalid",
    [0.0, -0.01, -5.0, float("nan"), float("inf"), -float("inf"), True, False],
)
def test_non_positive_or_non_finite_height_raises_value_error(h_invalid) -> None:
    """h <= 0 or non-finite height raises ValueError."""
    with pytest.raises(ValueError):
        ProtectiveAngleEngine.get_protective_angle_deg("I", h_invalid)


@pytest.mark.parametrize(
    "lps_cls,h_over,h_max_str",
    [
        ("I", 20.01, "20"),
        ("I", 25.0, "20"),
        ("II", 30.01, "30"),
        ("II", 45.0, "30"),
        ("III", 45.01, "45"),
        ("III", 60.0, "45"),
        ("IV", 60.01, "60"),
        ("IV", 100.0, "60"),
    ],
)
def test_above_h_max_raises_value_error_naming_class_and_limit(
    lps_cls: str, h_over: float, h_max_str: str
) -> None:
    """IEC 62305-3:2024 Figure 1 NOTE 1: h > h_max raises ValueError naming class & limit."""
    with pytest.raises(ValueError) as exc_info:
        ProtectiveAngleEngine.get_protective_angle_deg(lps_cls, h_over)
    msg = str(exc_info.value)
    assert lps_cls in msg
    assert h_max_str in msg


@pytest.mark.parametrize("bad_class", ["", "V", "0", "i", " I", None, 1])
def test_unknown_lps_class_raises_value_error(bad_class) -> None:
    """Unknown LPS class raises ValueError rather than defaulting to Class I."""
    with pytest.raises(ValueError):
        ProtectiveAngleEngine.get_protective_angle_deg(bad_class, 10.0)
    with pytest.raises(ValueError):
        ProtectiveAngleEngine().check_object_in_cone(
            bad_class, 0.0, 0.0, 10.0, 0.0, 2.0, 0.0, 5.0
        )


@pytest.mark.parametrize(
    "lps_cls,rod_tip_z",
    [("I", 25.0), ("II", 35.0), ("III", 50.0), ("IV", 65.0)],
)
def test_check_object_in_cone_above_h_max_returns_not_applicable_with_reason(
    lps_cls: str, rod_tip_z: float
) -> None:
    """check_object_in_cone returns applicable=False and reason without raising."""
    engine = ProtectiveAngleEngine()
    res = engine.check_object_in_cone(
        lps_class=lps_cls,
        rod_tip_x=0.0,
        rod_tip_y=0.0,
        rod_tip_z=rod_tip_z,
        ref_plane_z=0.0,
        object_x=2.0,
        object_y=0.0,
        object_z=5.0,
    )
    assert res["applicable"] is False
    assert res["protected"] is False
    assert isinstance(res.get("reason"), str) and len(res["reason"]) > 0
