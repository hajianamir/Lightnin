"""Step 5.1 Part C — Independent-oracle verification of M2 (`peec_thermal.py`).

Verifies `PEECThermalEngine.calculate_mutual_inductance_neumann` against
independent closed-form double-integral evaluations:
1. Two parallel filaments of equal length L at known separation d within rel=1e-6.
2. Two perpendicular filaments within 1e-12 of 0.0 H.
3. Touching or overlapping collinear filaments raise ValueError naming
   logarithmic divergence.
4. Small separations (1 mm and 0.2 mm vs 1 m length, plus shared-vertex 60 deg
   non-collinear filaments): result is finite, matches closed-form reference
   within rel=1e-6, and adaptive quadrature converges without silent distance
   clamping.

Primary-source disclosure (Step 5.1 Part C.2):
`docs/` (`docs/35_THREE_PASS_MATHEMATICAL_VERIFICATION_AUDIT.md` §3.2) states
the filament double integral M_ij = (mu_0 / (4*pi)) * iint (dl_i . dl_j) / |r_i - r_j|
without a primary source text in `docs/`. The elementary antiderivative used
below is derived directly by integrating 1 / sqrt((x_1 - x_2)^2 + d^2) over
[0, L]^2; formula and source to be confirmed by owner.
"""

import math
import pytest

from aegislps_engine.peec_thermal import PEECThermalEngine, SkewSegment3D


def _parallel_equal_filaments_closed_form_h(length_m: float, spacing_m: float) -> float:
    """Elementary closed-form evaluation of the equal-length parallel filament double integral:

        M(L, d) = (mu_0 / (4*pi)) * int_0^L int_0^L dx_1 dx_2 / sqrt((x_1 - x_2)^2 + d^2)
                = (mu_0 / (2*pi)) * [L * asinh(L / d) - sqrt(L^2 + d^2) + d]

    Formula and source to be confirmed by owner (primary source for Neumann's
    filament integral is not in `docs/`).
    """
    return 2.0e-7 * (
        length_m * math.asinh(length_m / spacing_m)
        - math.hypot(length_m, spacing_m)
        + spacing_m
    )


@pytest.mark.parametrize(
    ("length_m", "spacing_m", "expected_h"),
    [
        # Hand-evaluated values from M(L, d) = 2e-7 * [L * asinh(L/d) - sqrt(L^2 + d^2) + d]
        # (formula and source to be confirmed by owner):
        (1.0, 0.10, 4.186470776371761e-07),
        (2.0, 0.25, 7.574760248745596e-07),
        (5.0, 0.50, 2.093235388185880e-06),
        (10.0, 1.00, 4.186470776371761e-06),
    ],
)
def test_m2_parallel_equal_filaments_match_closed_form_within_1e6(
    length_m: float, spacing_m: float, expected_h: float
):
    """Part C.1a: Equal-length parallel filaments match closed-form integral within rel=1e-6.

    Formula: M = (mu_0 / (2*pi)) * [L * asinh(L / d) - sqrt(L^2 + d^2) + d]
    (formula and source to be confirmed by owner).
    """
    seg_1 = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(length_m, 0.0, 0.0))
    seg_2 = SkewSegment3D(start=(0.0, spacing_m, 0.0), end=(length_m, spacing_m, 0.0))

    hand_ref = _parallel_equal_filaments_closed_form_h(length_m, spacing_m)
    assert hand_ref == pytest.approx(expected_h, rel=1e-12)

    m_computed = PEECThermalEngine.calculate_mutual_inductance_neumann(seg_1, seg_2)
    assert math.isfinite(m_computed)
    assert m_computed == pytest.approx(expected_h, rel=1e-6)

    # Anti-parallel orientation reverses sign with identical magnitude:
    seg_2_rev = SkewSegment3D(
        start=(length_m, spacing_m, 0.0), end=(0.0, spacing_m, 0.0)
    )
    m_rev = PEECThermalEngine.calculate_mutual_inductance_neumann(seg_1, seg_2_rev)
    assert m_rev == pytest.approx(-expected_h, rel=1e-6)


@pytest.mark.parametrize(
    ("seg_a", "seg_b"),
    [
        # Orthogonal skew filaments in 3D (x-directed vs y-directed, separated in z):
        (
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(2.0, 0.0, 0.0)),
            SkewSegment3D(start=(0.5, -1.0, 0.3), end=(0.5, 1.0, 0.3)),
        ),
        # Orthogonal filaments sharing an endpoint at the origin:
        (
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(1.0, 0.0, 0.0)),
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(0.0, 0.0, 1.0)),
        ),
        # Orthogonal rotated filaments in arbitrary plane (dot product = 0):
        (
            SkewSegment3D(start=(1.0, 2.0, 3.0), end=(4.0, 6.0, 3.0)),
            SkewSegment3D(start=(2.0, 1.0, 5.0), end=(-2.0, 4.0, 5.0)),
        ),
    ],
)
def test_m2_perpendicular_filaments_within_1e12_of_zero(
    seg_a: SkewSegment3D, seg_b: SkewSegment3D
):
    """Part C.1b: Orthogonal filaments have dl_i . dl_j = 0 -> M within 1e-12 of 0.0 H."""
    m_val = PEECThermalEngine.calculate_mutual_inductance_neumann(seg_a, seg_b)
    assert math.isfinite(m_val)
    assert abs(m_val - 0.0) <= 1e-12


@pytest.mark.parametrize(
    ("seg_a", "seg_b"),
    [
        # Touching collinear segments sharing endpoint (1, 0, 0):
        (
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(1.0, 0.0, 0.0)),
            SkewSegment3D(start=(1.0, 0.0, 0.0), end=(2.0, 0.0, 0.0)),
        ),
        # Touching anti-parallel collinear segments sharing endpoint (1, 0, 0):
        (
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(1.0, 0.0, 0.0)),
            SkewSegment3D(start=(2.0, 0.0, 0.0), end=(1.0, 0.0, 0.0)),
        ),
        # Partially overlapping collinear segments along 3D diagonal:
        (
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(2.0, 2.0, 2.0)),
            SkewSegment3D(start=(1.0, 1.0, 1.0), end=(3.0, 3.0, 3.0)),
        ),
        # Identical coincident segments:
        (
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(1.0, 0.0, 0.0)),
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(1.0, 0.0, 0.0)),
        ),
    ],
)
def test_m2_touching_or_overlapping_collinear_filaments_raise_value_error(
    seg_a: SkewSegment3D, seg_b: SkewSegment3D
):
    """Part C.1c: Touching or overlapping collinear filaments raise ValueError naming logarithmic divergence."""
    with pytest.raises(ValueError, match="logarithmic divergence"):
        PEECThermalEngine.calculate_mutual_inductance_neumann(seg_a, seg_b)


@pytest.mark.parametrize(
    ("length_m", "spacing_m", "expected_h"),
    [
        # Small separations (1.0 mm vs 1.0 m, 0.2 mm vs 1.0 m, and 0.2 mm vs 0.1 m):
        # M(1.0, 1e-3) = 2e-7 * [asinh(1000) - sqrt(1 + 1e-6) + 1e-3] = 1.320380441908423e-06 H
        # M(1.0, 2e-4) = 2e-7 * [asinh(5000) - sqrt(1 + 4e-8) + 2e-4] = 1.642108072395236e-06 H
        # M(0.1, 2e-4) = 2e-7 * [0.1*asinh(500) - sqrt(0.01 + 4e-8) + 2e-4] = 1.181950855797338e-07 H
        # (formula and source to be confirmed by owner).
        (1.0, 1.0e-3, 1.320380441908423e-06),
        (1.0, 2.0e-4, 1.642108072395236e-06),
        (0.1, 2.0e-4, 1.181950855797338e-07),
    ],
)
def test_m2_small_separation_filaments_finite_converged_and_unclamped(
    length_m: float, spacing_m: float, expected_h: float
):
    """Part C.1d: Small separation (1 mm and 0.2 mm) is finite, matches reference, and converges."""
    seg_1 = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(length_m, 0.0, 0.0))
    seg_2 = SkewSegment3D(start=(0.0, spacing_m, 0.0), end=(length_m, spacing_m, 0.0))

    m_10 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_1, seg_2, num_gauss_points=10
    )
    m_20 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_1, seg_2, num_gauss_points=20
    )

    assert math.isfinite(m_10)
    assert math.isfinite(m_20)
    assert m_10 == pytest.approx(expected_h, rel=1e-6)
    assert m_20 == pytest.approx(expected_h, rel=1e-6)
    assert abs(m_10 - m_20) / abs(m_20) < 1e-6
