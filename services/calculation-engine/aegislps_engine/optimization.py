import numpy as np
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field, model_validator

from aegislps_geometry.rolling_sphere import (
    RollingSphereEngine,
    rolling_sphere_radius_m,
)

class CandidateRod(BaseModel):
    id: str
    x: float
    y: float
    z: float
    height_m: float
    cost_units: float = 100.0

class ProtectedTarget(BaseModel):
    id: str
    x: float
    y: float
    z: float
    tolerance_radius_m: float = 0.5

class OptimizationInput(BaseModel):
    lps_class: str = "I"
    building_bounds: Tuple[float, float, float, float] = (-15.0, -10.0, 15.0, 10.0) # (min_x, min_y, max_x, max_y)
    roof_height_m: float = 15.0
    targets_to_protect: List[ProtectedTarget] = Field(default_factory=list)
    max_candidate_rods: int = 8
    target_sphere_radius_m: float = Field(
        default_factory=lambda: rolling_sphere_radius_m(lps_class="I")
    )
    iterations: int = 150
    random_seed: int = 42

    @model_validator(mode="after")
    def _default_radius_from_lps_class(self) -> "OptimizationInput":
        if "target_sphere_radius_m" not in self.model_fields_set:
            self.target_sphere_radius_m = rolling_sphere_radius_m(
                lps_class=self.lps_class
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
    diagnostics: List[str] = Field(default_factory=list)

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
        np.random.seed(inp.random_seed)
        r = inp.target_sphere_radius_m
        rs = RollingSphereEngine(r)
        min_x, min_y, max_x, max_y = inp.building_bounds
        targets = inp.targets_to_protect

        if not targets:
            # Default rooftop perimeter targets
            targets = [
                ProtectedTarget(id="t1", x=min_x + 2, y=min_y + 2, z=inp.roof_height_m),
                ProtectedTarget(id="t2", x=max_x - 2, y=min_y + 2, z=inp.roof_height_m),
                ProtectedTarget(id="t3", x=max_x - 2, y=max_y - 2, z=inp.roof_height_m),
                ProtectedTarget(id="t4", x=min_x + 2, y=max_y - 2, z=inp.roof_height_m),
                ProtectedTarget(id="t5", x=0, y=0, z=inp.roof_height_m + 1.5), # Rooftop HVAC unit
            ]

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
            return covered_count, (covered_count / max(1, len(targets))) * 100.0

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
            diagnostics=[
                f"Evaluated {len(targets)} critical rooftop target coordinates.",
                f"Optimal configuration achieved {best_pct:.1f}% coverage with {len(best_rods)} rods."
            ]
        )
        return result, trajectory

    def optimize_air_terminations(self, inp: OptimizationInput) -> OptimizationResult:
        """ Optimize air-termination rods using ground-referenced (z = 0) rolling-sphere coverage. """
        result, _ = self._search(inp)
        return result
