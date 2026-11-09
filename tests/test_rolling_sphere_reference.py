import math
import numpy as np
import pytest

import aegislps_geometry.rolling_sphere as rs_mod
import aegislps_geometry.mesh_rolling_sphere as mrs_mod
from aegislps_geometry.rolling_sphere import RollingSphereEngine
from aegislps_geometry.mesh_rolling_sphere import (
    ArbitraryMeshRollingSphereEngine,
    MeshRollingSphereInput,
    TriangleFace,
)


def _protected_radius(R: float, h: float, z: float) -> float:
    fn = getattr(rs_mod, "protected_radius_at_height", None)
    assert fn is not None, "protected_radius_at_height is missing from aegislps_geometry.rolling_sphere"
    return fn(R, h, z)


def test_reference_points_r20_h10():
    """C.1: Reference protected radii for R=20 m, h=10 m at z=0, 2, 5, 8 m within 0.01 m."""
    expected_points = [
        (0.0, 17.3205),
        (2.0, 8.6027),
        (5.0, 4.0917),
        (8.0, 1.3205),
    ]
    engine = RollingSphereEngine(sphere_radius_m=20.0)

    for z_m, expected_rho in expected_points:
        inside = engine.check_surface_exposure(expected_rho - 0.05, 0.0, z_m, 0.0, 0.0, 10.0)
        outside = engine.check_surface_exposure(expected_rho + 0.05, 0.0, z_m, 0.0, 0.0, 10.0)
        assert inside["protected"] is True, f"Point inside boundary at z={z_m} should be protected"
        assert outside["protected"] is False, f"Point outside boundary at z={z_m} should be exposed"

    for z_m, expected_rho in expected_points:
        actual_rho = _protected_radius(20.0, 10.0, z_m)
        assert abs(actual_rho - expected_rho) <= 0.01, (
            f"At z={z_m} m: expected {expected_rho}, got {actual_rho}"
        )


def test_protected_radius_zero_for_z_above_h():
    """C.2: rho(z) = 0 for z >= h."""
    for z_m in (10.0, 10.1, 15.0, 25.0):
        assert _protected_radius(20.0, 10.0, z_m) == 0.0


def test_protected_radius_zero_at_rod_height():
    """C.3: rho(h) = 0."""
    for r_m, h_m in ((20.0, 10.0), (30.0, 15.0), (45.0, 20.0), (60.0, 25.0)):
        assert _protected_radius(r_m, h_m, h_m) == 0.0


def test_protected_radius_monotonic_non_increasing():
    """C.4: Monotonic non-increasing rho(z) on a grid from 0 to h."""
    z_grid = np.linspace(0.0, 10.0, 201)
    radii = [_protected_radius(20.0, 10.0, float(z)) for z in z_grid]
    for prev_r, next_r in zip(radii, radii[1:]):
        assert next_r <= prev_r + 1e-12


def test_protected_radius_invalid_inputs_raise_value_error():
    """C.5: ValueError for R=0, R=-1, h=-1, h=2R+0.1, z=-0.1."""
    invalid_cases = [
        (0.0, 10.0, 2.0),
        (-1.0, 10.0, 2.0),
        (20.0, -1.0, 2.0),
        (20.0, 2.0 * 20.0 + 0.1, 2.0),
        (20.0, 10.0, -0.1),
    ]
    for r_m, h_m, z_m in invalid_cases:
        with pytest.raises(ValueError):
            _protected_radius(r_m, h_m, z_m)


def test_protected_radius_accepts_h_equal_1_5_r():
    """C.6: Acceptance of h = 1.5 R (valid since 0 < h <= 2R), returning a finite number."""
    r_m = 20.0
    h_m = 1.5 * r_m  # 30.0 m
    rho_ground = _protected_radius(r_m, h_m, 0.0)
    rho_mid = _protected_radius(r_m, h_m, 5.0)
    assert math.isfinite(rho_ground) and rho_ground > 0.0
    assert math.isfinite(rho_mid) and rho_mid >= 0.0


def test_mesh_protected_and_partially_exposed_triangles():
    """C.7: One triangle fully inside protected zone -> PROTECTED; one with one vertex outside -> PARTIALLY_EXPOSED."""
    engine = ArbitraryMeshRollingSphereEngine()
    # At R=20 m, h=10 m, z=2 m: protected radius rho(2) = 8.6027 m
    tri_inside = TriangleFace(
        id="tri-inside",
        v0=(1.0, 0.0, 2.0),
        v1=(2.0, 1.0, 2.0),
        v2=(1.0, 2.0, 2.0),
    )
    tri_one_out = TriangleFace(
        id="tri-one-vertex-out",
        v0=(1.0, 0.0, 2.0),
        v1=(2.0, 1.0, 2.0),
        v2=(10.0, 0.0, 2.0),  # d=10.0 m > 8.6027 m; centroid=(4.33, 0.33, 2.0) is inside
    )
    res = engine.evaluate_mesh_protection(
        MeshRollingSphereInput(
            sphere_radius_m=20.0,
            triangles=[tri_inside, tri_one_out],
            air_termination_tips=[(0.0, 0.0, 10.0)],
        )
    )

    assert getattr(res.face_clearances[0], "status", None) == "PROTECTED"
    assert res.face_clearances[0].is_protected is True
    assert getattr(res.face_clearances[1], "status", None) == "PARTIALLY_EXPOSED"
    assert res.face_clearances[1].is_protected is False


def test_mesh_c1b_regression_centroid_inside_vertex_outside():
    """C.8: C1b regression — centroid inside protected zone but one vertex outside must NOT be PROTECTED."""
    engine = ArbitraryMeshRollingSphereEngine()
    # Centroid = (4.0, 0.0, 2.0) is inside both new (8.60 m) and old (16.0 m) zones,
    # while v2 = (18.0, 0.0, 2.0) is outside both zones.
    tri_c1b = TriangleFace(
        id="tri-c1b",
        v0=(-3.0, 2.0, 2.0),
        v1=(-3.0, -2.0, 2.0),
        v2=(18.0, 0.0, 2.0),
    )
    res = engine.evaluate_mesh_protection(
        MeshRollingSphereInput(
            sphere_radius_m=20.0,
            triangles=[tri_c1b],
            air_termination_tips=[(0.0, 0.0, 10.0)],
        )
    )

    face = res.face_clearances[0]
    assert face.is_protected is False
    assert getattr(face, "status", None) != "PROTECTED"
    assert getattr(face, "status", None) == "PARTIALLY_EXPOSED"


def test_mesh_nonconvex_edge_counterexample():
    """2.a: Sloped triangle whose 3 vertices and centroid are protected, but edge midpoint (12.9, 0, 1) is exposed."""
    engine = ArbitraryMeshRollingSphereEngine()
    tri = TriangleFace(
        id="tri-nonconvex-edge",
        v0=(17.3, 0.0, 0.0),
        v1=(8.5, 0.0, 2.0),
        v2=(0.0, 0.0, 2.0),
    )
    res = engine.evaluate_mesh_protection(
        MeshRollingSphereInput(
            sphere_radius_m=20.0,
            triangles=[tri],
            air_termination_tips=[(0.0, 0.0, 10.0)],
        )
    )

    face = res.face_clearances[0]
    assert face.status == "PARTIALLY_EXPOSED"
    assert face.is_protected is False
    assert res.unprotected_faces_count == 1
    assert res.status == "PARTIAL_EXPOSURE"


def test_counterexample_edge_midpoint_exposed_public_api():
    """2.b: Verify via public API that (12.9, 0, 1) on the v0-v1 edge is exposed while vertices and centroid are protected."""
    rs_engine = RollingSphereEngine(sphere_radius_m=20.0)
    for px, py, pz in ((17.3, 0.0, 0.0), (8.5, 0.0, 2.0), (0.0, 0.0, 2.0), (8.6, 0.0, 4.0 / 3.0)):
        assert rs_engine.check_surface_exposure(px, py, pz, 0.0, 0.0, 10.0)["protected"] is True

    rho_at_z1 = _protected_radius(20.0, 10.0, 1.0)
    assert abs(rho_at_z1 - 11.0755) <= 0.01
    assert 12.9 > rho_at_z1
    mid_exposure = rs_engine.check_surface_exposure(12.9, 0.0, 1.0, 0.0, 0.0, 10.0)
    assert mid_exposure["protected"] is False


def test_mesh_fully_protected_small_triangle():
    """2.c: Small triangle near rod axis is PROTECTED with FULL_COVERAGE."""
    engine = ArbitraryMeshRollingSphereEngine()
    tri = TriangleFace(
        id="tri-small-protected",
        v0=(0.5, 0.0, 1.0),
        v1=(0.0, 0.5, 1.0),
        v2=(-0.5, 0.0, 1.0),
    )
    res = engine.evaluate_mesh_protection(
        MeshRollingSphereInput(
            sphere_radius_m=20.0,
            triangles=[tri],
            air_termination_tips=[(0.0, 0.0, 10.0)],
        )
    )

    assert res.face_clearances[0].status == "PROTECTED"
    assert res.face_clearances[0].is_protected is True
    assert res.unprotected_faces_count == 0
    assert res.status == "FULL_COVERAGE"


def test_mesh_partially_protected_flat_triangle():
    """2.d: Flat triangle at z=1 with one vertex at d=0 and one at d=19 -> PARTIALLY_EXPOSED."""
    engine = ArbitraryMeshRollingSphereEngine()
    tri = TriangleFace(
        id="tri-flat-partial",
        v0=(0.0, 0.0, 1.0),
        v1=(19.0, 0.0, 1.0),
        v2=(0.0, 1.0, 1.0),
    )
    res = engine.evaluate_mesh_protection(
        MeshRollingSphereInput(
            sphere_radius_m=20.0,
            triangles=[tri],
            air_termination_tips=[(0.0, 0.0, 10.0)],
        )
    )

    assert res.face_clearances[0].status == "PARTIALLY_EXPOSED"
    assert res.face_clearances[0].is_protected is False


def test_mesh_fully_exposed_triangle():
    """2.e: Triangle with all vertices at d=30 m, z=1 m -> EXPOSED."""
    engine = ArbitraryMeshRollingSphereEngine()
    tri = TriangleFace(
        id="tri-all-exposed",
        v0=(30.0, 0.0, 1.0),
        v1=(30.0 * math.cos(0.1), 30.0 * math.sin(0.1), 1.0),
        v2=(30.0 * math.cos(0.2), 30.0 * math.sin(0.2), 1.0),
    )
    res = engine.evaluate_mesh_protection(
        MeshRollingSphereInput(
            sphere_radius_m=20.0,
            triangles=[tri],
            air_termination_tips=[(0.0, 0.0, 10.0)],
        )
    )

    assert res.face_clearances[0].status == "EXPOSED"
    assert res.face_clearances[0].is_protected is False


def test_barycentric_grid_size_and_special_points():
    """2.f: barycentric_grid(12) has 91 points including all 3 vertices, all 3 edge midpoints, and centroid."""
    grid_fn = getattr(mrs_mod, "barycentric_grid", None)
    assert grid_fn is not None, "barycentric_grid helper is missing from aegislps_geometry.mesh_rolling_sphere"
    grid = grid_fn(12)
    assert len(grid) == 91

    required_points = [
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.5, 0.5, 0.0),
        (0.5, 0.0, 0.5),
        (0.0, 0.5, 0.5),
        (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0),
    ]
    for req in required_points:
        assert any(np.allclose(pt, req, atol=1e-12) for pt in grid), f"Missing {req} in barycentric_grid(12)"

