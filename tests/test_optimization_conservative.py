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
    rolling_sphere_radius_m,
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
    """D.1: Returned coverage_percentage matches RollingSphereEngine(Class I) on default targets."""
    engine = DesignOptimizationEngine()
    inp = OptimizationInput()
    result = engine.optimize_air_terminations(inp)

    targets = _default_targets(inp)
    recomputed_pct = _oracle_coverage_pct(
        result.selected_rods, targets, sphere_radius_m=rolling_sphere_radius_m("I")
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

    Input:
    - OptimizationInput(roof_height_m=4.0, iterations=11, random_seed=1) with default
      Class I sphere radius R = 20.0 m, building_bounds = (-15.0, -10.0, 15.0, 10.0),
      perimeter targets t1..t4 at (±13, ±8, z = 4.0), and HVAC target t5 at (0, 0, z = 5.5).
    - Under ground-referenced rolling-sphere geometry, the initial 4 corner rods at
      (±14, ±9, z = 4.0, height_m = 3.0, tip_z = 7.0 m) cover 4/5 targets (80.0%, 4 rods,
      score = 3.2), while simulated annealing accepts worsening transitions at steps 2, 4,
      and 11, ending at walker state (3, 5) (60.0% coverage, 5 rods, score = 2.0) with no
      remaining iterations to recover.

    Validation:
    - Validated by the runtime mutation test in
      test_mutation_h7a_last_accepted_logic_fails_d3_expectation, which restores ONLY the
      old H7-a last-accepted best-state overwrite logic on top of the corrected
      RollingSphereEngine coverage rule (that mutant returns 60.0% coverage with 5 rods).
    - Unmodified commit 31796ba does NOT return 60.0% on this input; 31796ba returns
      100.0% coverage with 7 rods because its coverage geometry was the old ungrounded
      tip-suspended sphere formula (C1).
    """
    engine = DesignOptimizationEngine()
    inp = OptimizationInput(
        roof_height_m=4.0,
        target_sphere_radius_m=20.0,
        iterations=11,
        random_seed=1,
    )

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


def test_mutation_h7a_last_accepted_logic_fails_d3_expectation(tmp_path, monkeypatch):
    """Mutation check for D.3: swapping in H7-a last-accepted best-state logic degrades 80%/4 rods -> 60%/5 rods.

    Method:
    - First run the real DesignOptimizationEngine on the D.3 input and verify 80.0% coverage
      with 4 rods (score = 3.2).
    - Next write a temporary copy of optimization.py into tmp_path (outside the repository)
      replacing ONLY the strict best-state update (`if cand_score > best_score:`) with the
      old H7-a behavior (overwriting best_* whenever a simulated-annealing step is accepted),
      keeping the corrected RollingSphereEngine coverage rule unchanged.
    - Monkeypatch DesignOptimizationEngine._search at runtime with the mutant implementation
      and assert that it returns 60.0% coverage with 5 rods (score = 2.0), causing the D.3
      expectation (80.0% coverage with 4 rods) to fail.
    """
    import importlib.util
    import inspect
    from pathlib import Path

    inp = OptimizationInput(
        roof_height_m=4.0,
        target_sphere_radius_m=20.0,
        iterations=11,
        random_seed=1,
    )

    real_res = DesignOptimizationEngine().optimize_air_terminations(inp)
    assert real_res.coverage_percentage == pytest.approx(80.0)
    assert len(real_res.selected_rods) == 4
    assert real_res.uncovered_targets_count == 1

    opt_path = Path(inspect.getfile(DesignOptimizationEngine))
    src = opt_path.read_text(encoding="utf-8")

    fixed_block = """            if cand_score > best_score:
                best_rods = list(temp_rods)
                best_covered = cur_cov
                best_pct = cur_pct
                best_score = cand_score

            # Objective: Maximize coverage, minimize rod count
            score_delta = (cur_cov - current_covered) - 0.2 * (len(temp_rods) - len(current_rods))
            if score_delta > 0 or np.exp(score_delta / max(1e-4, temperature)) > np.random.rand():
                current_rods = temp_rods
                current_covered = cur_cov
                current_pct = cur_pct"""

    mutant_block = """            # Objective: Maximize coverage, minimize rod count (H7-a mutant)
            score_delta = (cur_cov - current_covered) - 0.2 * (len(temp_rods) - len(current_rods))
            if score_delta > 0 or np.exp(score_delta / max(1e-4, temperature)) > np.random.rand():
                current_rods = temp_rods
                current_covered = cur_cov
                current_pct = cur_pct
                best_rods = list(temp_rods)
                best_covered = cur_cov
                best_pct = cur_pct"""

    assert fixed_block in src
    mutant_file = tmp_path / "optimization_h7a_mutant.py"
    mutant_file.write_text(src.replace(fixed_block, mutant_block, 1), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("optimization_h7a_mutant", mutant_file)
    assert spec is not None and spec.loader is not None
    mutant_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mutant_mod)

    monkeypatch.setattr(
        DesignOptimizationEngine, "_search", mutant_mod.DesignOptimizationEngine._search
    )
    mutant_res = DesignOptimizationEngine().optimize_air_terminations(inp)

    assert mutant_res.coverage_percentage == pytest.approx(60.0)
    assert len(mutant_res.selected_rods) == 5
    assert mutant_res.uncovered_targets_count == 2

    with pytest.raises(AssertionError):
        test_regression_h7a_preserves_best_state_after_late_degradation()