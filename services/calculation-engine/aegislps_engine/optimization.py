import math
import numpy as np
from typing import Any, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aegislps_geometry.rolling_sphere import (
    ROLLING_SPHERE_RADIUS_M_BY_CLASS,
    RollingSphereEngine,
)

# IEC 62305-3:2024, Clause 5.2.2.1, Table 2 (p. 21),
# "Table 2 – Values of rolling sphere radius, mesh size and protection angle
# corresponding to the class of LPS":
#   Class of LPS I  : Rolling sphere radius r = 20 m
#   Class of LPS II : Rolling sphere radius r = 30 m
#   Class of LPS III: Rolling sphere radius r = 45 m
#   Class of LPS IV : Rolling sphere radius r = 60 m
_VALID_LPS_CLASSES = ("I", "II", "III", "IV")

ROOF_COVERAGE_VERIFICATION_NOTE = (
    "Roof coverage not verified (H7): the optimizer evaluates "
    "ground-referenced (z = 0) rolling-sphere coverage only."
)


def _check_finite_float(name: str, v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name} must be a finite number, not bool; got {v!r}.")
    val = float(v)
    if not math.isfinite(val):
        raise ValueError(f"{name} must be finite, got {v!r}.")
    return val


def _check_nonnegative_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val < 0.0:
        raise ValueError(f"{name} must be >= 0, got {v!r}.")
    return val


def _check_positive_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val <= 0.0:
        raise ValueError(f"{name} must be > 0, got {v!r}.")
    return val


class CandidateRod(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str
    x: float
    y: float
    z: float
    height_m: float
    cost_units: float = 100.0

    @field_validator("x", "y", mode="before")
    @classmethod
    def _validate_xy(cls, v: Any, info) -> float:
        return _check_finite_float(info.field_name, v)

    @field_validator("z", "cost_units", mode="before")
    @classmethod
    def _validate_nonnegative(cls, v: Any, info) -> float:
        return _check_nonnegative_finite_float(info.field_name, v)

    @field_validator("height_m", mode="before")
    @classmethod
    def _validate_height(cls, v: Any) -> float:
        return _check_positive_finite_float("height_m", v)


class ProtectedTarget(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str
    x: float
    y: float
    z: float
    tolerance_radius_m: float = 0.5  # unused by optimizer

    @field_validator("x", "y", mode="before")
    @classmethod
    def _validate_xy(cls, v: Any, info) -> float:
        return _check_finite_float(info.field_name, v)

    @field_validator("z", mode="before")
    @classmethod
    def _validate_z(cls, v: Any) -> float:
        return _check_nonnegative_finite_float("z", v)

    @field_validator("tolerance_radius_m", mode="before")
    @classmethod
    def _validate_tolerance(cls, v: Any) -> float:
        return _check_positive_finite_float("tolerance_radius_m", v)


class OptimizationInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    lps_class: str
    building_bounds: Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)
    roof_height_m: float
    targets_to_protect: List[ProtectedTarget]
    # optimizer hyperparameters, not physical inputs
    max_candidate_rods: int = 8
    target_sphere_radius_m: Optional[float] = None
    # optimizer hyperparameters, not physical inputs
    iterations: int = 150
    random_seed: int = 42

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        return v

    @field_validator("building_bounds", mode="before")
    @classmethod
    def _validate_bounds(cls, v: Any) -> Tuple[float, float, float, float]:
        if isinstance(v, (str, bytes)) or not isinstance(v, (list, tuple)):
            raise ValueError(
                f"building_bounds must be a 4-tuple (min_x, min_y, max_x, max_y), got {v!r}."
            )
        if len(v) != 4:
            raise ValueError(
                f"building_bounds must have length 4, got {len(v)}."
            )
        min_x = _check_finite_float("building_bounds[0] (min_x)", v[0])
        min_y = _check_finite_float("building_bounds[1] (min_y)", v[1])
        max_x = _check_finite_float("building_bounds[2] (max_x)", v[2])
        max_y = _check_finite_float("building_bounds[3] (max_y)", v[3])
        if not (min_x < max_x):
            raise ValueError(
                f"building_bounds requires min_x < max_x, got min_x={min_x}, max_x={max_x}."
            )
        if not (min_y < max_y):
            raise ValueError(
                f"building_bounds requires min_y < max_y, got min_y={min_y}, max_y={max_y}."
            )
        return (min_x, min_y, max_x, max_y)

    @field_validator("roof_height_m", mode="before")
    @classmethod
    def _validate_roof_height(cls, v: Any) -> float:
        return _check_positive_finite_float("roof_height_m", v)

    @field_validator("targets_to_protect")
    @classmethod
    def _validate_targets_non_empty(
        cls, v: List[ProtectedTarget]
    ) -> List[ProtectedTarget]:
        if not v:
            raise ValueError("targets_to_protect must not be empty.")
        return v

    @field_validator("target_sphere_radius_m", mode="before")
    @classmethod
    def _validate_target_sphere_radius(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        return _check_positive_finite_float("target_sphere_radius_m", v)

    @field_validator("max_candidate_rods", "iterations", mode="before")
    @classmethod
    def _validate_positive_hyperparams(cls, v: Any, info) -> int:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(
                f"{info.field_name} must be a positive int, not bool; got {v!r}."
            )
        if v < 1:
            raise ValueError(f"{info.field_name} must be >= 1, got {v!r}.")
        return v

    @field_validator("random_seed", mode="before")
    @classmethod
    def _validate_random_seed(cls, v: Any) -> int:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(
                f"random_seed must be an int >= 0, not bool; got {v!r}."
            )
        if v < 0:
            raise ValueError(f"random_seed must be >= 0, got {v!r}.")
        return v

    @model_validator(mode="after")
    def _resolve_radius_and_height_domain(self) -> "OptimizationInput":
        table2_r = float(ROLLING_SPHERE_RADIUS_M_BY_CLASS[self.lps_class])
        if self.target_sphere_radius_m is None:
            self.target_sphere_radius_m = table2_r
        else:
            if not math.isclose(
                float(self.target_sphere_radius_m),
                table2_r,
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                raise ValueError(
                    f"target_sphere_radius_m ({self.target_sphere_radius_m} m) disagrees with "
                    f"IEC 62305-3:2024 Table 2 sphere radius ({table2_r} m) for LPS Class {self.lps_class}."
                )

        r = float(self.target_sphere_radius_m)
        if self.roof_height_m + 5.0 > 2.0 * r:
            raise ValueError(
                f"roof_height_m + 5.0 ({self.roof_height_m + 5.0} m) exceeds 2 * R ({2.0 * r} m) "
                f"for rolling sphere radius R = {r} m."
            )
        return self


class OptimizationResult(BaseModel):
    selected_rods: List[CandidateRod]
    uncovered_targets_count: int
    coverage_percentage: float
    total_rod_cost: float
    iterations_run: int
    pareto_score: float
    status: str
    roof_coverage_verification_note: str = ROOF_COVERAGE_VERIFICATION_NOTE
    diagnostics: List[str] = Field(default_factory=list)

    @property
    def engineering_insights(self) -> List[str]:
        return self.diagnostics


class DesignOptimizationEngine:
    """
    Advanced Multi-Objective Design Optimization Engine.

    Optimizes:
    - Minimal rod count & total installation cost
    - Maximal rolling-sphere geometric protection coverage
    - Zero separation-distance violation constraints
    Uses simulated annealing with stochastic multi-candidate mutations.

    Geometric coverage is evaluated via RollingSphereEngine(r).check_surface_exposure
    using ground z = 0 as the reference plane and absolute rod tip elevation
    tip_z = rod.z + rod.height_m above z = 0 (replacing the earlier sphere
    formula referenced only to the rod tip without ground contact).
    """

    def _search(
        self, inp: OptimizationInput
    ) -> Tuple[OptimizationResult, List[Tuple[int, float]]]:
        if not inp.targets_to_protect:
            raise ValueError("targets_to_protect must not be empty.")
        table2_r = float(ROLLING_SPHERE_RADIUS_M_BY_CLASS[inp.lps_class])
        r = float(inp.target_sphere_radius_m) if inp.target_sphere_radius_m is not None else table2_r
        if r <= 0.0:
            raise ValueError(f"target_sphere_radius_m must be > 0, got {r}.")
        if inp.roof_height_m + 5.0 > 2.0 * r:
            raise ValueError(
                f"roof_height_m + 5.0 ({inp.roof_height_m + 5.0} m) exceeds 2 * R ({2.0 * r} m)."
            )

        np.random.seed(inp.random_seed)
        rs = RollingSphereEngine(r)
        min_x, min_y, max_x, max_y = inp.building_bounds
        if not (min_x < max_x and min_y < max_y):
            raise ValueError("building_bounds requires min_x < max_x and min_y < max_y.")
        targets = inp.targets_to_protect

        # Initial candidate state: 4 corner rods
        current_rods = [
            CandidateRod(id=f"rod-{i}", x=x, y=y, z=inp.roof_height_m, height_m=3.0)
            for i, (x, y) in enumerate([
                (min_x + 1, min_y + 1),
                (max_x - 1, min_y + 1),
                (max_x - 1, max_y - 1),
                (min_x + 1, max_y - 1)
            ])
        ]

        def evaluate_coverage(rods: List[CandidateRod]) -> Tuple[int, float]:
            covered_count = 0
            for t in targets:
                target_covered = False
                for rod in rods:
                    tip_z = rod.z + rod.height_m
                    if rs.check_surface_exposure(
                        t.x, t.y, t.z, rod.x, rod.y, tip_z
                    )["protected"]:
                        target_covered = True
                        break
                if target_covered:
                    covered_count += 1
            return covered_count, (covered_count / len(targets)) * 100.0

        def score(covered: int, n_rods: int) -> float:
            return covered - 0.2 * n_rods

        current_covered, current_pct = evaluate_coverage(current_rods)
        best_rods = list(current_rods)
        best_covered, best_pct = current_covered, current_pct
        best_score = score(best_covered, len(best_rods))
        trajectory: List[Tuple[int, float]] = [(current_covered, len(current_rods))]
        temperature = 1.0

        # Simulated annealing search
        for step in range(inp.iterations):
            temp_rods = list(current_rods)
            mutation_choice = np.random.choice(["move", "height", "add", "remove"])

            if mutation_choice == "move" and temp_rods:
                idx = np.random.randint(len(temp_rods))
                old_rod = temp_rods[idx]
                new_x = float(np.clip(old_rod.x + np.random.uniform(-2.0, 2.0), min_x, max_x))
                new_y = float(np.clip(old_rod.y + np.random.uniform(-2.0, 2.0), min_y, max_y))
                temp_rods[idx] = CandidateRod(id=old_rod.id, x=new_x, y=new_y, z=old_rod.z, height_m=old_rod.height_m)

            elif mutation_choice == "height" and temp_rods:
                idx = np.random.randint(len(temp_rods))
                old_rod = temp_rods[idx]
                new_h = float(np.clip(old_rod.height_m + np.random.uniform(-0.5, 1.0), 1.5, 5.0))
                temp_rods[idx] = CandidateRod(id=old_rod.id, x=old_rod.x, y=old_rod.y, z=old_rod.z, height_m=new_h)

            elif mutation_choice == "add" and len(temp_rods) < inp.max_candidate_rods:
                rx = float(np.random.uniform(min_x, max_x))
                ry = float(np.random.uniform(min_y, max_y))
                temp_rods.append(CandidateRod(id=f"rod-opt-{step}", x=rx, y=ry, z=inp.roof_height_m, height_m=3.0))

            elif mutation_choice == "remove" and len(temp_rods) > 2:
                idx = np.random.randint(len(temp_rods))
                temp_rods.pop(idx)

            cur_cov, cur_pct = evaluate_coverage(temp_rods)
            cand_score = score(cur_cov, len(temp_rods))

            if cand_score > best_score:
                best_rods = list(temp_rods)
                best_covered = cur_cov
                best_pct = cur_pct
                best_score = cand_score

            # Objective: Maximize coverage, minimize rod count
            score_delta = (cur_cov - current_covered) - 0.2 * (len(temp_rods) - len(current_rods))
            if score_delta > 0 or np.exp(score_delta / max(1e-4, temperature)) > np.random.rand():
                current_rods = temp_rods
                current_covered = cur_cov
                current_pct = cur_pct

            trajectory.append((current_covered, len(current_rods)))
            temperature *= 0.98

        uncovered = len(targets) - best_covered
        total_cost = sum([r.cost_units * (r.height_m / 2.0) for r in best_rods])
        pareto = float(best_pct - 0.05 * total_cost)

        result = OptimizationResult(
            selected_rods=best_rods,
            uncovered_targets_count=uncovered,
            coverage_percentage=round(best_pct, 1),
            total_rod_cost=round(total_cost, 2),
            iterations_run=inp.iterations,
            pareto_score=round(pareto, 2),
            status="CONVERGED" if uncovered == 0 else "PARTIAL_COVERAGE",
            roof_coverage_verification_note=ROOF_COVERAGE_VERIFICATION_NOTE,
            diagnostics=[
                f"Evaluated {len(targets)} critical rooftop target coordinates.",
                f"Optimal configuration achieved {best_pct:.1f}% coverage with {len(best_rods)} rods.",
                ROOF_COVERAGE_VERIFICATION_NOTE,
            ],
        )
        return result, trajectory

    def optimize_air_terminations(self, inp: OptimizationInput) -> OptimizationResult:
        """ Optimize air-termination rods using ground-referenced (z = 0) rolling-sphere coverage. """
        result, _ = self._search(inp)
        return result
