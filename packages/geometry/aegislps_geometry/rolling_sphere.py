import math
from typing import Dict, Optional
import numpy as np


# Source: IEC 62305-3:2024, Clause 5.2.2.1, Table 2 (p. 21),
# "Values of rolling sphere radius, mesh size and protection angle
# corresponding to the class of LPS":
#   Class I   : r = 20 m  (mesh cell size w_m = 5 x 5 m)
#   Class II  : r = 30 m  (mesh cell size w_m = 10 x 10 m)
#   Class III : r = 45 m  (mesh cell size w_m = 15 x 15 m)
#   Class IV  : r = 60 m  (mesh cell size w_m = 20 x 20 m)
# Protection angle: see Figure 1 of IEC 62305-3:2024, Clause 5.2.2.1.
# Table 2 note: one dimension of the mesh cell may be increased by up to +25 %,
# provided the mesh cell perimeter is not increased (recorded as reference note only).
ROLLING_SPHERE_RADIUS_M_BY_CLASS: Dict[str, float] = {
    "I": 20.0,
    "II": 30.0,
    "III": 45.0,
    "IV": 60.0,
}


def rolling_sphere_radius_m(
    lps_class: Optional[str] = None,
    *,
    current_ka: Optional[float] = None,
) -> float:
    """
    Return the rolling-sphere radius r [m] for the given LPS class per
    IEC 62305-3:2024, Clause 5.2.2.1, Table 2 (p. 21).

    Valid classes are 'I' (20 m), 'II' (30 m), 'III' (45 m), and 'IV' (60 m).
    Raises ValueError on unknown class, non-positive or unsupported current input,
    NaN/infinite values, or boolean inputs.
    """
    if isinstance(lps_class, bool) or isinstance(current_ka, bool):
        raise ValueError("Boolean input is not valid for rolling_sphere_radius_m.")

    if current_ka is not None:
        if not isinstance(current_ka, (int, float)):
            raise ValueError("current_ka must be a finite positive number.")
        c_val = float(current_ka)
        if not math.isfinite(c_val) or c_val <= 0.0:
            raise ValueError(f"current_ka must be finite and > 0, got {current_ka!r}.")
        raise ValueError(
            "IEC 62305-3:2024, Clause 5.2.2.1, Table 2 specifies rolling-sphere "
            "radius by LPS class ('I', 'II', 'III', 'IV'), not by current."
        )

    if lps_class is None:
        raise ValueError("lps_class is required ('I', 'II', 'III', 'IV').")

    if isinstance(lps_class, (int, float)):
        num_val = float(lps_class)
        if not math.isfinite(num_val):
            raise ValueError(f"NaN or infinite input is not valid: {lps_class!r}.")
        if num_val <= 0.0:
            raise ValueError(f"Non-positive numeric/current input is not valid: {lps_class!r}.")
        raise ValueError(
            "lps_class must be a string ('I', 'II', 'III', 'IV') per "
            "IEC 62305-3:2024, Clause 5.2.2.1, Table 2."
        )

    if not isinstance(lps_class, str):
        raise ValueError(
            f"lps_class must be a string ('I', 'II', 'III', 'IV'), got {type(lps_class).__name__}."
        )

    cls = lps_class.strip().upper()
    if cls not in ROLLING_SPHERE_RADIUS_M_BY_CLASS:
        raise ValueError(
            f"Unknown LPS class {lps_class!r}. Expected one of 'I', 'II', 'III', 'IV'."
        )

    return float(ROLLING_SPHERE_RADIUS_M_BY_CLASS[cls])


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
        R > 0, 0 <= h <= 2 * R, z >= 0 (all finite, non-boolean).
        Raises ValueError if R <= 0, h < 0, h > 2 * R, z < 0, NaN/inf, or bool.

    Reference values (R = 20 m, h = 10 m):
        rho(0) = 17.3205 m
        rho(2) =  8.6027 m
        rho(5) =  4.0917 m
        rho(8) =  1.3205 m
    """
    if isinstance(R, bool) or isinstance(h, bool) or isinstance(z, bool):
        raise ValueError("Boolean input is not valid for protected_radius_at_height.")

    r_val = float(R)
    h_val = float(h)
    z_val = float(z)

    if not (math.isfinite(r_val) and math.isfinite(h_val) and math.isfinite(z_val)):
        raise ValueError(f"Inputs R, h, z must be finite numbers, got ({R}, {h}, {z})")
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
    3D Analytical Rolling Sphere Engine for IEC 62305-3:2024 protection assessment.
    Determines surface exposure and clearance without depending on WebGL rendering.

    Default sphere radius corresponds to LPS Class I (20 m) from
    IEC 62305-3:2024, Clause 5.2.2.1, Table 2 (p. 21).
    """
    def __init__(
        self,
        sphere_radius_m: Optional[float] = None,
        *,
        lps_class: Optional[str] = None,
    ):
        if sphere_radius_m is not None and lps_class is not None:
            raise ValueError("Specify either sphere_radius_m or lps_class, not both.")
        if sphere_radius_m is None:
            cls = "I" if lps_class is None else lps_class
            r_val = rolling_sphere_radius_m(cls)
        else:
            if isinstance(sphere_radius_m, bool):
                raise ValueError("Boolean input is not valid for sphere_radius_m.")
            r_val = float(sphere_radius_m)
            if not math.isfinite(r_val) or r_val <= 0.0:
                raise ValueError(f"sphere_radius_m must be finite and > 0, got {sphere_radius_m}")
        self.r = r_val

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
