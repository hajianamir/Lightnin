import numpy as np
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

class TriangleFace(BaseModel):
    id: str
    v0: Tuple[float, float, float]
    v1: Tuple[float, float, float]
    v2: Tuple[float, float, float]

class MeshRollingSphereInput(BaseModel):
    sphere_radius_m: float = 20.0 # Class I default 20m
    triangles: List[TriangleFace] = Field(default_factory=list)
    air_termination_tips: List[Tuple[float, float, float]] = Field(default_factory=list)

class MeshClearanceResult(BaseModel):
    face_id: str
    centroid_x: float
    centroid_y: float
    centroid_z: float
    sphere_bottom_z_m: float
    is_protected: bool
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

    Evaluates:
    - Geometric contact conditions between a sphere of radius R and arbitrary 3D triangular faces.
    - Sagitta penetration depths across sloped, pitched, multi-level, and irregular geometric roofs.
    - Identification of vulnerable protrusions and uncovered building surface regions.
    """
    def evaluate_mesh_protection(self, inp: MeshRollingSphereInput) -> MeshRollingSphereResult:
        r = float(inp.sphere_radius_m)
        tips = [np.array(tip, dtype=np.float64) for tip in inp.air_termination_tips]
        results = []
        unprotected_count = 0

        for face in inp.triangles:
            v0 = np.array(face.v0, dtype=np.float64)
            v1 = np.array(face.v1, dtype=np.float64)
            v2 = np.array(face.v2, dtype=np.float64)
            centroid = (v0 + v1 + v2) / 3.0

            # Find closest air-termination tip
            min_dist_to_tip = 1e9
            closest_tip_z = centroid[2]
            for tip in tips:
                d_horiz = np.sqrt((centroid[0] - tip[0])**2 + (centroid[1] - tip[1])**2)
                if d_horiz < min_dist_to_tip:
                    min_dist_to_tip = d_horiz
                    closest_tip_z = tip[2]

            # Evaluate rolling sphere sagitta resting on rod tip
            if min_dist_to_tip <= r and len(tips) > 0:
                sphere_bottom_z = closest_tip_z - (r - np.sqrt(max(0.0, r**2 - min_dist_to_tip**2)))
                is_protected = bool(centroid[2] <= sphere_bottom_z)
                penetration = float(max(0.0, centroid[2] - sphere_bottom_z))
            else:
                sphere_bottom_z = 0.0
                is_protected = False
                penetration = float(centroid[2])

            if not is_protected:
                unprotected_count += 1

            results.append(MeshClearanceResult(
                face_id=face.id,
                centroid_x=round(float(centroid[0]), 2),
                centroid_y=round(float(centroid[1]), 2),
                centroid_z=round(float(centroid[2]), 2),
                sphere_bottom_z_m=round(float(sphere_bottom_z), 2),
                is_protected=is_protected,
                penetration_depth_m=round(penetration, 2)
            ))

        total_faces = len(inp.triangles)
        cov_pct = ((total_faces - unprotected_count) / max(1, total_faces)) * 100.0

        return MeshRollingSphereResult(
            sphere_radius_m=r,
            evaluated_faces_count=total_faces,
            unprotected_faces_count=unprotected_count,
            coverage_percentage=round(cov_pct, 1),
            face_clearances=results,
            status="FULL_COVERAGE" if unprotected_count == 0 else "PARTIAL_EXPOSURE"
        )
