import math
import numpy as np
import pytest

import aegislps_geometry.rolling_sphere as rs_mod
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
