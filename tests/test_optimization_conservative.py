"""Conservative verification and regression tests for DesignOptimizationEngine (Step 1.2: C1, H7-a/b)."""

import math
from typing import List

import pytest

from aegislps_engine.optimization import (
    CandidateRod,
    DesignOptimizationEngine,
    OptimizationInput,
    ProtectedTarget,
)
from aegislps_geometry.rolling_sphere import (
    RollingSphereEngine,
    protected_radius_at_height,
)


def _default_targets(inp: OptimizationInput) -> List[ProtectedTarget]:
    if inp.targets_to_protect:
        return list(inp.targets_to_protect)
    min_x, min_y, max_x, max_y = inp.building_bounds
    return [
        ProtectedTarget(id="t1", x=min_x + 2, y=min_y + 2, z=inp.roof_height_m),
        ProtectedTarget(id="t2", x=max_x - 2, y=min_y + 2, z=inp.roof_height_m),
        ProtectedTarget(id="t3", x=max_x - 2, y=max_y - 2, z=inp.roof_height_m),
        ProtectedTarget(id="t4", x=min_x + 2, y=max_y - 2, z=inp.roof_height_m),
        ProtectedTarget(id="t5", x=0.0, y=0.0, z=inp.roof_height_m + 1.5),
    ]


def _initial_corner_rods(inp: OptimizationInput) -> List[CandidateRod]:
    min_x, min_y, max_x, max_y = inp.building_bounds
    return [
        CandidateRod(id=f"rod-{i}", x=x, y=y, z=inp.roof_height_m, height_m=3.0)
        for i, (x, y) in enumerate(
            [
                (min_x + 1, min_y + 1),
                (max_x - 1, min_y + 1),
                (max_x - 1, max_y - 1),
                (min_x + 1, max_y - 1),
            ]
        )
    ]


def _oracle_coverage_pct(
    rods: List[CandidateRod],
    targets: List[ProtectedTarget],
    sphere_radius_m: float,
) -> float:
    rs = RollingSphereEngine(sphere_radius_m)
    covered = 0
    for t in targets:
        if any(
            rs.check_surface_exposure(
                t.x, t.y, t.z, rod.x, rod.y, rod.z + rod.height_m
            )["protected"]
            for rod in rods
        ):
            covered += 1
    return (covered / max(1, len(targets))) * 100.0


def _score(covered: int, n_rods: float) -> float:
    return covered - 0.2 * n_rods


def test_coverage_consistency_with_rolling_sphere_engine():
    """D.1: Returned coverage_percentage matches RollingSphereEngine(20) on default targets."""
    engine = DesignOptimizationEngine()
    inp = OptimizationInput()
    result = engine.optimize_air_terminations(inp)

    targets = _default_targets(inp)
    recomputed_pct = _oracle_coverage_pct(
        result.selected_rods, targets, sphere_radius_m=20.0
    )
    assert abs(recomputed_pct - result.coverage_percentage) <= 0.1


def test_best_score_never_worse_than_any_visited_state():
    """D.2: Returned best score is >= every visited trajectory state, including accepted worsening steps."""
    engine = DesignOptimizationEngine()
    inp = OptimizationInput()
    result, trajectory = engine._search(inp)

    targets = _default_targets(inp)
    best_covered = len(targets) - result.uncovered_targets_count
    best_score = _score(best_covered, len(result.selected_rods))

    trajectory_scores = [_score(cov, n_rods) for cov, n_rods in trajectory]
    for entry_score in trajectory_scores:
        assert best_score >= entry_score

    accepted_worse_steps = [
        idx
        for idx in range(1, len(trajectory_scores))
        if trajectory_scores[idx] < trajectory_scores[idx - 1]
    ]
    assert len(accepted_worse_steps) >= 1


def test_regression_h7a_preserves_best_state_after_late_degradation():
    """D.3: Regression against H7-a (overwriting best_* with accepted worse walker states).

    Construction:
    - Set roof_height_m = 4.0 m with Class I sphere radius R = 20.0 m and default perimeter
      targets t1..t4 at (±13, ±8, z = 4.0) plus HVAC target t5 at (0, 0, z = 5.5).
    - Initial 4 corner rods sit at (±14, ±9, z = 4.0) with height_m = 3.0 (tip_z = 7.0 m),
      horizontal distance sqrt(2) ~= 1.414 m from t1..t4. Under ground-referenced rolling
      sphere geometry, rho(4.0) = sqrt(231) - 12 ~= 3.199 m >= 1.414 m, so initial state
      covers 4/5 targets (80.0%, 4 rods, score = 4 - 0.2 * 4 = 3.2).
    - With random_seed = 1 and iterations = 11, high-temperature simulated annealing accepts
      worsening mutations at step 2 (4/5 with 4 rods -> 3/5 with 3 rods, score 3.2 -> 2.4),
      step 4 (3/5 with 3 rods -> 3/5 with 4 rods, score 2.4 -> 2.2), and on the final step 11
      (3/5 with 4 rods -> 3/5 with 5 rods, score 2.2 -> 2.0), never recovering before
      iterations runs out.
    - Because the annealing walker in _search uses the exact same mutations and RNG draws as
      the old H7-a loop, trajectory[-1] == (3, 5) (60.0% coverage, score 2.0) is the exact
      degraded state the old code would have returned, whereas strict best-state tracking
      preserves (4, 4) (80.0% coverage, score 3.2).
    """
    engine = DesignOptimizationEngine()
    inp = OptimizationInput(roof_height_m=4.0, iterations=11, random_seed=1)

    result = engine.optimize_air_terminations(inp)
    targets = _default_targets(inp)
    returned_covered = len(targets) - result.uncovered_targets_count
    returned_score = _score(returned_covered, len(result.selected_rods))

    assert result.coverage_percentage == pytest.approx(80.0)
    assert returned_covered == 4
    assert len(result.selected_rods) == 4
    assert returned_score == pytest.approx(3.2)

    _, trajectory = engine._search(inp)
    final_covered, final_n_rods = trajectory[-1]
    final_score = _score(final_covered, final_n_rods)
    assert (final_covered, final_n_rods) == (3, 5)
    assert final_score == pytest.approx(2.0)
    # Confirm the very last step was an accepted worsening step with no recovery left
    assert _score(*trajectory[-1]) < _score(*trajectory[-2])
    assert returned_score > final_score


def test_returned_coverage_at_least_initial_four_corner_coverage():
    """D.4: Returned coverage is >= initial 4-corner-rod coverage under the new rule."""
    engine = DesignOptimizationEngine()

    for inp in (
        OptimizationInput(),
        OptimizationInput(roof_height_m=4.0, iterations=11, random_seed=1),
        OptimizationInput(roof_height_m=4.0, iterations=30, random_seed=7),
    ):
        initial_rods = _initial_corner_rods(inp)
        targets = _default_targets(inp)
        initial_pct = _oracle_coverage_pct(
            initial_rods, targets, sphere_radius_m=inp.target_sphere_radius_m
        )
        result = engine.optimize_air_terminations(inp)
        assert result.coverage_percentage + 1e-9 >= round(initial_pct, 1)


def test_geometry_rule_matches_rolling_sphere_oracle_and_rejects_old_formula():
    """D.5: Single-rod coverage agrees with RollingSphereEngine at d=0 and d > rho(z)."""
    engine = DesignOptimizationEngine()
    r = 20.0
    roof_z = 15.0
    rod_height = 3.0
    tip_z = roof_z + rod_height

    # Wide bounds isolate corner rod-0 at (-99, -99); the other 3 rods are >= 198 m >> R away.
    bounds = (-100.0, -100.0, 100.0, 100.0)
    rod_x, rod_y = bounds[0] + 1.0, bounds[1] + 1.0
    rs = RollingSphereEngine(r)

    # Case 1: Target at d = 0 and z just below rod tip -> covered under oracle.
    target_under_tip = ProtectedTarget(
        id="t_under_tip", x=rod_x, y=rod_y, z=tip_z - 0.1
    )
    oracle_under_tip = rs.check_surface_exposure(
        target_under_tip.x,
        target_under_tip.y,
        target_under_tip.z,
        rod_x,
        rod_y,
        tip_z,
    )["protected"]
    assert oracle_under_tip is True

    res_covered = engine.optimize_air_terminations(
        OptimizationInput(
            building_bounds=bounds,
            roof_height_m=roof_z,
            targets_to_protect=[target_under_tip],
            target_sphere_radius_m=r,
            iterations=0,
        )
    )
    assert res_covered.coverage_percentage == (100.0 if oracle_under_tip else 0.0)
    assert res_covered.uncovered_targets_count == (0 if oracle_under_tip else 1)

    # Case 2: Target at z = roof_z and d > protected_radius_at_height -> NOT covered under
    # RollingSphereEngine, whereas the old tip-suspended sphere formula falsely marked it covered.
    rho_at_roof = protected_radius_at_height(r, tip_z, roof_z)
    d_outside = rho_at_roof + 1.0
    target_outside = ProtectedTarget(
        id="t_outside", x=rod_x + d_outside, y=rod_y, z=roof_z
    )

    oracle_outside = rs.check_surface_exposure(
        target_outside.x,
        target_outside.y,
        target_outside.z,
        rod_x,
        rod_y,
        tip_z,
    )["protected"]
    old_sphere_bottom = tip_z - (r - math.sqrt(max(0.0, r**2 - d_outside**2)))
    old_rule_covered = target_outside.z <= old_sphere_bottom
    assert old_rule_covered is True
    assert oracle_outside is False

    res_exposed = engine.optimize_air_terminations(
        OptimizationInput(
            building_bounds=bounds,
            roof_height_m=roof_z,
            targets_to_protect=[target_outside],
            target_sphere_radius_m=r,
            iterations=0,
        )
    )
    assert res_exposed.coverage_percentage == (100.0 if oracle_outside else 0.0)
    assert res_exposed.uncovered_targets_count == (0 if oracle_outside else 1)
