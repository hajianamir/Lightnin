import math
from typing import Dict, Optional, Union
import numpy as np


# Source: IEC 62305-4:2024, Annex A, Table A.5 (p. 56) — Rolling sphere radius r
# corresponding to peak current I_0 by protection level:
#   Protection level I      : I_0 = 200 kA -> r = 313 m
#   Protection level II     : I_0 = 150 kA -> r = 260 m
#   Protection level III-IV : I_0 = 100 kA -> r = 200 m
# Note: Table A.5 cites IEC 62305-1:2024 Clause A.4 (electrogeometric model,
# r = 10 * I^0.65). Clause A.4 of IEC 62305-1:2024 has NOT been read directly;
# therefore protection-level lookups and tabulated currents return exact Table A.5
# radii, while r = 10 * I^0.65 is documented as a note and evaluated only when an
# explicit non-tabulated positive current i0_ka is supplied.
IEC_62305_4_2024_CLASS_I0_KA: Dict[str, float] = {
    "I": 200.0,
    "II": 150.0,
    "III": 100.0,
    "IV": 100.0,
}

IEC_62305_4_2024_TABLE_A5_RADII_M: Dict[str, float] = {
    "I": 313.0,
    "II": 260.0,
    "III": 200.0,
    "IV": 200.0,
}

_TABLE_A5_RADIUS_BY_I0_KA: Dict[float, float] = {
    200.0: 313.0,
    150.0: 260.0,
    100.0: 200.0,
}


def rolling_sphere_radius_m(
    lps_class_or_i0: Optional[Union[str, float]] = None,
    *,
    lps_class: Optional[str] = None,
    i0_ka: Optional[float] = None,
) -> float:
    """Return rolling sphere radius r [m] per IEC 62305-4:2024 Table A.5 (p. 56).

    Accepts either a protection level (`"I"`, `"II"`, `"III"`, `"IV"`) or a
    lightning peak current `i0_ka` [kA] (positional or keyword, mutually exclusive).

    Protection-level mapping (IEC 62305-4:2024, Table A.5):
      - `"I"`   -> I_0 = 200 kA -> r = 313.0 m
      - `"II"`  -> I_0 = 150 kA -> r = 260.0 m
      - `"III"` -> I_0 = 100 kA -> r = 200.0 m
      - `"IV"`  -> I_0 = 100 kA -> r = 200.0 m

    Note on formula `r = 10 * I^0.65`:
      Table A.5 references IEC 62305-1:2024 Clause A.4 (electrogeometric model).
      Because IEC 62305-1:2024 Clause A.4 has not been verified directly from the
      2024 Part 1 text, protection levels and tabulated currents {100, 150, 200} kA
      return exact Table A.5 radii, while non-tabulated positive `i0_ka` values
      evaluate `10.0 * (i0_ka ** 0.65)`.
    """
    provided_count = (
        (lps_class_or_i0 is not None)
        + (lps_class is not None)
        + (i0_ka is not None)
    )
    if provided_count == 0:
        raise ValueError(
            "Provide either lps_class ('I', 'II', 'III', 'IV') or positive i0_ka."
        )
    if provided_count > 1:
        raise ValueError(
            "Specify only one of positional lps_class_or_i0, lps_class, or i0_ka."
        )

    if lps_class_or_i0 is not None:
        if isinstance(lps_class_or_i0, bool):
            raise ValueError("Boolean input is not valid for rolling_sphere_radius_m.")
        if isinstance(lps_class_or_i0, str):
            lps_class = lps_class_or_i0
        elif isinstance(lps_class_or_i0, (int, float)):
            i0_ka = float(lps_class_or_i0)
        else:
            raise ValueError(
                f"Unsupported input type {type(lps_class_or_i0).__name__} for rolling_sphere_radius_m."
            )

    if lps_class is not None:
        if not isinstance(lps_class, str):
            raise ValueError("lps_class must be a string ('I', 'II', 'III', 'IV').")
        cls = lps_class.strip().upper()
        if cls not in IEC_62305_4_2024_TABLE_A5_RADII_M:
            raise ValueError(
                f"Unknown LPS class {lps_class!r}. Expected one of 'I', 'II', 'III', 'IV'."
            )
        return IEC_62305_4_2024_TABLE_A5_RADII_M[cls]

    assert i0_ka is not None
    if isinstance(i0_ka, bool) or not isinstance(i0_ka, (int, float)):
        raise ValueError("i0_ka must be a finite positive float or int in kA.")
    current_ka = float(i0_ka)
    if not math.isfinite(current_ka) or current_ka <= 0.0:
        raise ValueError(f"i0_ka must be > 0 kA, got {i0_ka!r}.")

    for tab_i0, tab_r in _TABLE_A5_RADIUS_BY_I0_KA.items():
        if abs(current_ka - tab_i0) <= 1e-9:
            return tab_r

    return 10.0 * (current_ka ** 0.65)


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
    3D Analytical Rolling Sphere Engine for IEC 62305 protection assessment.
    Determines surface exposure and clearance without depending on WebGL rendering.
    """
    def __init__(
        self,
        sphere_radius_m: Optional[float] = None,
        *,
        lps_class: str = "I",
    ):
        if sphere_radius_m is None:
            sphere_radius_m = rolling_sphere_radius_m(lps_class=lps_class)
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
