import math
import numpy as np
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

from aegislps_geometry.rolling_sphere import (
    protected_radius_at_height,
    rolling_sphere_radius_m,
)

BARYCENTRIC_SUBDIVISION_N: int = 12


def barycentric_grid(n: int = BARYCENTRIC_SUBDIVISION_N) -> List[Tuple[float, float, float]]:
    """
    Build a uniform barycentric sample grid of subdivision level n over a triangle.

    Returns (n + 1) * (n + 2) // 2 weight triples (w0, w1, w2) with w0 + w1 + w2 = 1.
    When n is a multiple of 6 (such as the default n = 12, giving 91 points), the grid
    includes all three vertices, all three edge midpoints, and the triangle centroid.
    """
    if int(n) < 1:
        raise ValueError(f"Subdivision level n must be >= 1, got {n}")
    n_int = int(n)
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
    id: str
    v0: Tuple[float, float, float]
    v1: Tuple[float, float, float]
    v2: Tuple[float, float, float]


class MeshRollingSphereInput(BaseModel):
    sphere_radius_m: float = Field(
        default_factory=lambda: rolling_sphere_radius_m(lps_class="I")
    )
    triangles: List[TriangleFace] = Field(default_factory=list)
    air_termination_tips: List[Tuple[float, float, float]] = Field(default_factory=list)


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

    Limitation:
    A finite sample grid is a numerical approximation and is not an exact geometric proof.
    For a 10 m triangle edge at n = 12, the sample spacing along edges is 10 / 12 ≈ 0.83 m.
    A very large face whose dimensions are not small compared with the sphere radius R can
    still hide a narrow exposed interior region between adjacent grid points unless subdivided.
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
        r = float(inp.sphere_radius_m)
        if r <= 0.0:
            raise ValueError(f"sphere_radius_m must be > 0, got {r}")

        tips = [np.array(tip, dtype=np.float64) for tip in inp.air_termination_tips]
        for tip in tips:
            tz = float(tip[2])
            if tz < 0.0 or tz > 2.0 * r:
                raise ValueError(f"Rod tip height h must satisfy 0 <= h <= 2R ({2.0 * r}), got {tz}")

        results: List[MeshClearanceResult] = []
        unprotected_count = 0
        total_grid_pts = len(_DEFAULT_BARYCENTRIC_WEIGHTS)

        for face in inp.triangles:
            v0 = np.array(face.v0, dtype=np.float64)
            v1 = np.array(face.v1, dtype=np.float64)
            v2 = np.array(face.v2, dtype=np.float64)
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

            results.append(MeshClearanceResult(
                face_id=face.id,
                centroid_x=round(float(centroid[0]), 2),
                centroid_y=round(float(centroid[1]), 2),
                centroid_z=round(float(centroid[2]), 2),
                sphere_bottom_z_m=round(float(centroid_sphere_z), 2),
                is_protected=is_protected,
                status=face_status,
                penetration_depth_m=round(float(penetration), 2),
            ))

        total_faces = len(inp.triangles)
        cov_pct = ((total_faces - unprotected_count) / max(1, total_faces)) * 100.0

        return MeshRollingSphereResult(
            sphere_radius_m=r,
            evaluated_faces_count=total_faces,
            unprotected_faces_count=unprotected_count,
            coverage_percentage=round(cov_pct, 1),
            face_clearances=results,
            status="FULL_COVERAGE" if unprotected_count == 0 else "PARTIAL_EXPOSURE",
        )
