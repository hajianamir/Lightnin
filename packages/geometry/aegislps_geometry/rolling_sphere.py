import math
import numpy as np


def protected_radius_at_height(R: float, h: float, z: float) -> float:
    """
    Calculate the horizontal protected radius rho(z) at height z around a vertical
    air-termination rod of tip height h under a rolling sphere of radius R touching
    both the ground plane (z = 0) and the rod tip.

    Formula:
        rho_c  = sqrt(2 * R * h - h^2)
        rho(z) = sqrt(2 * R * h - h^2) - sqrt(2 * R * z - z^2)   for 0 <= z <= h
        rho(z) = 0.0                                              for z >= h

    Domain:
        R > 0, 0 <= h <= 2 * R, z >= 0.
        Raises ValueError if R <= 0, h < 0, h > 2 * R, or z < 0.

    Reference values (R = 20 m, h = 10 m):
        rho(0) = 17.3205 m
        rho(2) =  8.6027 m
        rho(5) =  4.0917 m
        rho(8) =  1.3205 m
    """
    r_val = float(R)
    h_val = float(h)
    z_val = float(z)

    if r_val <= 0.0:
        raise ValueError(f"Sphere radius R must be > 0, got {R}")
    if h_val < 0.0 or h_val > 2.0 * r_val:
        raise ValueError(f"Rod tip height h must satisfy 0 <= h <= 2R ({2.0 * r_val}), got {h}")
    if z_val < 0.0:
        raise ValueError(f"Target height z must be >= 0, got {z}")

    if z_val >= h_val or h_val == 0.0:
        return 0.0

    rho_c = math.sqrt(max(0.0, 2.0 * r_val * h_val - h_val * h_val))
    offset = math.sqrt(max(0.0, 2.0 * r_val * z_val - z_val * z_val))
    return float(max(0.0, rho_c - offset))


class RollingSphereEngine:
    """
    3D Analytical Rolling Sphere Engine for IEC 62305-3 protection assessment.
    Determines surface exposure and clearance without depending on WebGL rendering.
    """
    def __init__(self, sphere_radius_m: float = 20.0):  # 20m for Class I
        if float(sphere_radius_m) <= 0.0:
            raise ValueError(f"sphere_radius_m must be > 0, got {sphere_radius_m}")
        self.r = float(sphere_radius_m)

    def check_surface_exposure(self, point_x: float, point_y: float, point_z: float,
                               rod_x: float, rod_y: float, rod_height_m: float) -> dict:
        """
        Calculates if a target rooftop point is protected under a rolling sphere of radius R
        resting on the reference ground plane (z = 0) and touching an air-termination rod tip
        (rod_x, rod_y, rod_height_m).
        """
        r_val = float(self.r)
        h_val = float(rod_height_m)
        z_val = float(point_z)

        rho_allowed = protected_radius_at_height(r_val, h_val, z_val)
        d_horiz = float(np.hypot(point_x - rod_x, point_y - rod_y))

        rho_c = math.sqrt(max(0.0, 2.0 * r_val * h_val - h_val * h_val))
        if h_val > 0.0 and d_horiz <= rho_c:
            z_protect = r_val - math.sqrt(max(0.0, r_val * r_val - (rho_c - d_horiz) ** 2))
        else:
            z_protect = 0.0

        max_axial_protected_z = min(h_val, 2.0 * r_val - h_val)
        is_protected = (
            z_val <= h_val
            and d_horiz <= rho_allowed
            and (rho_allowed > 0.0 or (d_horiz == 0.0 and z_val <= max_axial_protected_z))
        )

        return {
            "protected": bool(is_protected),
            "clearance_z_m": float(max(0.0, z_protect - z_val)),
            "protective_height_z_m": float(z_protect),
        }
