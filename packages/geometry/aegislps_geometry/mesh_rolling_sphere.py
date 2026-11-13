import math
import numpy as np
from typing import Any, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aegislps_geometry.rolling_sphere import (
    ROLLING_SPHERE_RADIUS_M_BY_CLASS,
    protected_radius_at_height,
)

# Internal numerical sample-grid subdivision level (91 points per triangle; not a standard value).
BARYCENTRIC_SUBDIVISION_N: int = 12


def _check_finite_coord(name: str, v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float, np.number)):
        raise ValueError(f"{name} must be a finite number, not bool; got {v!r}")
    val = float(v)
    if not math.isfinite(val):
        raise ValueError(f"{name} must be finite, got {v!r}")
    return val


def _validate_point3(
    name: str, v: Any, *, require_z_nonnegative: bool = True
) -> Tuple[float, float, float]:
    if isinstance(v, (str, bytes)) or not isinstance(v, (list, tuple, np.ndarray)):
        raise ValueError(f"{name} must be a 3-element (x, y, z) sequence, got {v!r}")
    if len(v) != 3:
        raise ValueError(f"{name} must have length 3, got {len(v)}")
    x = _check_finite_coord(f"{name}[0]", v[0])
    y = _check_finite_coord(f"{name}[1]", v[1])
    z = _check_finite_coord(f"{name}[2]", v[2])
    if require_z_nonnegative and z < 0.0:
        raise ValueError(f"{name} z coordinate must be >= 0, got {z}")
    return (x, y, z)


def barycentric_grid(n: int = BARYCENTRIC_SUBDIVISION_N) -> List[Tuple[float, float, float]]:
    """
    Build a uniform barycentric sample grid of subdivision level n over a triangle.

    Returns (n + 1) * (n + 2) // 2 weight triples (w0, w1, w2) with w0 + w1 + w2 = 1.
    When n is a multiple of 6 (such as the default n = 12, giving 91 points), the grid
    includes all three vertices, all three edge midpoints, and the triangle centroid.
    """
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)):
        raise ValueError(f"Subdivision level n must be an integer >= 1, not bool; got {n!r}")
    n_int = int(n)
    if n_int < 1:
        raise ValueError(f"Subdivision level n must be >= 1, got {n}")
    weights: List[Tuple[float, float, float]] = []
    for i in range(n_int + 1):
        for j in range(n_int + 1 - i):
            k = n_int - i - j
            weights.append((i / n_int, j / n_int, k / n_int))
    return weights


_DEFAULT_BARYCENTRIC_WEIGHTS = np.asarray(
    barycentric_grid(BARYCENTRIC_SUBDIVISION_N), dtype=np.float64
)


class TriangleFace(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str
    v0: Tuple[float, float, float]
    v1: Tuple[float, float, float]
    v2: Tuple[float, float, float]

    @field_validator("v0", "v1", "v2", mode="before")
    @classmethod
    def _validate_vertex(cls, v: Any, info) -> Tuple[float, float, float]:
        return _validate_point3(info.field_name, v, require_z_nonnegative=True)


class MeshRollingSphereInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    lps_class: Optional[str] = None
    sphere_radius_m: Optional[float] = None
    triangles: List[TriangleFace] = Field(default_factory=list)
    air_termination_tips: List[Tuple[float, float, float]] = Field(default_factory=list)

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str) or v not in ROLLING_SPHERE_RADIUS_M_BY_CLASS:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {tuple(ROLLING_SPHERE_RADIUS_M_BY_CLASS)}."
            )
        return v

    @field_validator("sphere_radius_m", mode="before")
    @classmethod
    def _validate_sphere_radius(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        val = _check_finite_coord("sphere_radius_m", v)
        if val <= 0.0:
            raise ValueError(f"sphere_radius_m must be > 0, got {v!r}")
        return val

    @field_validator("air_termination_tips", mode="before")
    @classmethod
    def _validate_tips_structure(cls, v: Any) -> List[Tuple[float, float, float]]:
        if not isinstance(v, (list, tuple)):
            raise ValueError(f"air_termination_tips must be a list of (x, y, z) triples, got {v!r}")
        return [
            _validate_point3(f"air_termination_tips[{idx}]", tip, require_z_nonnegative=True)
            for idx, tip in enumerate(v)
        ]

    @model_validator(mode="after")
    def _resolve_radius_and_tip_bounds(self) -> "MeshRollingSphereInput":
        has_class = self.lps_class is not None
        has_radius = self.sphere_radius_m is not None
        if has_class == has_radius:
            raise ValueError(
                "Exactly one of 'lps_class' or 'sphere_radius_m' must be provided."
            )
        if has_class:
            assert self.lps_class is not None
            self.sphere_radius_m = float(ROLLING_SPHERE_RADIUS_M_BY_CLASS[self.lps_class])

        assert self.sphere_radius_m is not None
        r = float(self.sphere_radius_m)
        for tip in self.air_termination_tips:
            tz = float(tip[2])
            if tz < 0.0 or tz > 2.0 * r:
                raise ValueError(
                    f"Rod tip height h must satisfy 0 <= h <= 2R ({2.0 * r}), got {tz}"
                )
        return self


class MeshClearanceResult(BaseModel):
    face_id: str
    centroid_x: float
    centroid_y: float
    centroid_z: float
    sphere_bottom_z_m: float
    is_protected: bool
    status: str = "EXPOSED"
    penetration_depth_m: float


class MeshRollingSphereResult(BaseModel):
    sphere_radius_m: float
    evaluated_faces_count: int
    unprotected_faces_count: int
    coverage_percentage: float
    face_clearances: List[MeshClearanceResult]
    status: str


class ArbitraryMeshRollingSphereEngine:
    """
    3D Analytical Rolling Sphere Analysis over Arbitrary Polygonal / Triangular Faceted Roof Meshes.

    Evaluates each triangular face on a uniform barycentric grid with subdivision level n = 12
    ((n + 1)(n + 2) / 2 = 91 sample points, including all three vertices, all edge midpoints,
    and the centroid) against rolling spheres of radius R resting on z = 0 and air-termination tips:
    - PROTECTED: all 91 grid points are protected.
    - PARTIALLY_EXPOSED: at least one grid point is protected, but not all.
    - EXPOSED: no grid point is protected.
    """

    @staticmethod
    def _evaluate_sample_point(
        point: np.ndarray,
        r: float,
        tips: List[np.ndarray],
    ) -> Tuple[bool, float]:
        px, py, pz = float(point[0]), float(point[1]), float(point[2])
        if pz < 0.0:
            raise ValueError(f"Target height z must be >= 0, got {pz}")
        if not tips:
            return False, 0.0

        point_protected = False
        best_sphere_z = 0.0

        for tip in tips:
            tx, ty, tz = float(tip[0]), float(tip[1]), float(tip[2])
            rho_allowed = protected_radius_at_height(r, tz, pz)
            d_horiz = math.hypot(px - tx, py - ty)

            rho_c = math.sqrt(max(0.0, 2.0 * r * tz - tz * tz))
            if tz > 0.0 and d_horiz <= rho_c:
                z_sphere = r - math.sqrt(max(0.0, r * r - (rho_c - d_horiz) ** 2))
                if z_sphere > best_sphere_z:
                    best_sphere_z = z_sphere

            max_axial_protected_z = min(tz, 2.0 * r - tz)
            if (
                pz <= tz
                and d_horiz <= rho_allowed
                and (rho_allowed > 0.0 or (d_horiz == 0.0 and pz <= max_axial_protected_z))
            ):
                point_protected = True

        return point_protected, best_sphere_z

    def evaluate_mesh_protection(self, inp: MeshRollingSphereInput) -> MeshRollingSphereResult:
        if inp.sphere_radius_m is None:
            if inp.lps_class is not None and inp.lps_class in ROLLING_SPHERE_RADIUS_M_BY_CLASS:
                r = float(ROLLING_SPHERE_RADIUS_M_BY_CLASS[inp.lps_class])
            else:
                raise ValueError(
                    "Exactly one of 'lps_class' or 'sphere_radius_m' must be provided."
                )
        else:
            r = _check_finite_coord("sphere_radius_m", inp.sphere_radius_m)
        if r <= 0.0:
            raise ValueError(f"sphere_radius_m must be > 0, got {r}")

        if not inp.triangles:
            raise ValueError("triangles must not be empty")

        validated_tips = [
            _validate_point3(f"air_termination_tips[{idx}]", tip, require_z_nonnegative=True)
            for idx, tip in enumerate(inp.air_termination_tips)
        ]
        tips = [np.array(tip, dtype=np.float64) for tip in validated_tips]
        for tip in tips:
            tz = float(tip[2])
            if tz < 0.0 or tz > 2.0 * r:
                raise ValueError(
                    f"Rod tip height h must satisfy 0 <= h <= 2R ({2.0 * r}), got {tz}"
                )

        results: List[MeshClearanceResult] = []
        unprotected_count = 0
        total_grid_pts = len(_DEFAULT_BARYCENTRIC_WEIGHTS)

        for face in inp.triangles:
            v0 = np.array(_validate_point3("face.v0", face.v0), dtype=np.float64)
            v1 = np.array(_validate_point3("face.v1", face.v1), dtype=np.float64)
            v2 = np.array(_validate_point3("face.v2", face.v2), dtype=np.float64)
            centroid = (v0 + v1 + v2) / 3.0

            vertices_mat = np.vstack((v0, v1, v2))
            sample_points = _DEFAULT_BARYCENTRIC_WEIGHTS @ vertices_mat
            evals = [self._evaluate_sample_point(pt, r, tips) for pt in sample_points]
            protected_points_count = sum(1 for pt_ok, _ in evals if pt_ok)

            if protected_points_count == total_grid_pts:
                face_status = "PROTECTED"
                is_protected = True
            elif protected_points_count > 0:
                face_status = "PARTIALLY_EXPOSED"
                is_protected = False
            else:
                face_status = "EXPOSED"
                is_protected = False

            if not is_protected:
                unprotected_count += 1

            _, centroid_sphere_z = self._evaluate_sample_point(centroid, r, tips)
            penetration = max(
                0.0,
                max(float(pt[2]) - z_s for pt, (_, z_s) in zip(sample_points, evals)),
            )

            results.append(
                MeshClearanceResult(
                    face_id=face.id,
                    centroid_x=round(float(centroid[0]), 2),
                    centroid_y=round(float(centroid[1]), 2),
                    centroid_z=round(float(centroid[2]), 2),
                    sphere_bottom_z_m=round(float(centroid_sphere_z), 2),
                    is_protected=is_protected,
                    status=face_status,
                    penetration_depth_m=round(float(penetration), 2),
                )
            )

        total_faces = len(inp.triangles)
        cov_pct = ((total_faces - unprotected_count) / total_faces) * 100.0

        return MeshRollingSphereResult(
            sphere_radius_m=r,
            evaluated_faces_count=total_faces,
            unprotected_faces_count=unprotected_count,
            coverage_percentage=round(cov_pct, 1),
            face_clearances=results,
            status="FULL_COVERAGE" if unprotected_count == 0 else "PARTIAL_EXPOSURE",
        )
