import numpy as np
from typing import Dict, List, Any

class ProtectiveAngleEngine:
    """
    Standards-Controlled Protective Angle Method Engine.

    STATUS:
    - Standards-controlled look-up; empirical curve-fitting removed.
    - Implements piece-wise linear interpolation between verified IEC 62305-3 Table 2 anchor points.
    - Strictly enforces maximum height limits (H <= 20m Class I, 30m Class II, 45m Class III, 60m Class IV).
    """
    # Standard Table 2 tabulated anchor points: (height_m, angle_deg)
    TABULATED_ANGLES = {
        "I": [(2.0, 71.0), (10.0, 45.0), (20.0, 25.0)],
        "II": [(2.0, 73.0), (10.0, 52.0), (20.0, 35.0), (30.0, 25.0)],
        "III": [(2.0, 76.0), (10.0, 60.0), (20.0, 45.0), (30.0, 35.0), (45.0, 25.0)],
        "IV": [(2.0, 78.0), (10.0, 65.0), (20.0, 53.0), (30.0, 45.0), (45.0, 35.0), (60.0, 25.0)]
    }

    MAX_HEIGHTS = {
        "I": 20.0,
        "II": 30.0,
        "III": 45.0,
        "IV": 60.0
    }

    @classmethod
    def get_protective_angle_deg(cls, lps_class: str, h_m: float) -> float:
        h = float(h_m)
        max_h = cls.MAX_HEIGHTS.get(lps_class, 20.0)
        if h > max_h or h < 0.0:
            return 0.0

        anchors = cls.TABULATED_ANGLES.get(lps_class, cls.TABULATED_ANGLES["I"])
        # Check boundary
        if h <= anchors[0][0]:
            return anchors[0][1]
        if h >= anchors[-1][0]:
            return anchors[-1][1]

        # Piece-wise linear interpolation between verified table anchors
        for i in range(len(anchors) - 1):
            h1, a1 = anchors[i]
            h2, a2 = anchors[i + 1]
            if h1 <= h <= h2:
                fraction = (h - h1) / (h2 - h1)
                return float(a1 + fraction * (a2 - a1))

        return 0.0

    def check_object_in_cone(
        self,
        lps_class: str,
        rod_tip_x: float,
        rod_tip_y: float,
        rod_tip_z: float,
        ref_plane_z: float,
        object_x: float,
        object_y: float,
        object_z: float
    ) -> Dict[str, Any]:
        h_tip = float(rod_tip_z - ref_plane_z)
        max_permitted_h = self.MAX_HEIGHTS.get(lps_class, 20.0)

        if h_tip > max_permitted_h:
            return {
                "protected": False,
                "applicable": False,
                "protective_angle_deg": 0.0,
                "reason": f"Height ({h_tip:.1f}m) exceeds IEC 62305-3 limit ({max_permitted_h}m) for Class {lps_class}. Must use Rolling Sphere."
            }

        alpha_deg = self.get_protective_angle_deg(lps_class, h_tip)
        if alpha_deg <= 0.0:
            return {
                "protected": False,
                "applicable": False,
                "protective_angle_deg": 0.0,
                "reason": "Protective angle unavailable for specified height."
            }

        delta_z = rod_tip_z - object_z
        if delta_z <= 0:
            return {
                "protected": False,
                "applicable": True,
                "protective_angle_deg": round(float(alpha_deg), 1),
                "reason": "Object elevation is at or above rod tip"
            }

        d_horiz = float(np.sqrt((object_x - rod_tip_x)**2 + (object_y - rod_tip_y)**2))
        r_cone = float(delta_z * np.tan(np.radians(alpha_deg)))
        is_protected = d_horiz <= r_cone

        return {
            "protected": bool(is_protected),
            "applicable": True,
            "protective_angle_deg": round(float(alpha_deg), 1),
            "protected_radius_at_z_m": round(r_cone, 2),
            "actual_horizontal_distance_m": round(d_horiz, 2),
            "clearance_margin_m": round(float(r_cone - d_horiz), 2),
            "status": "PROTECTED" if is_protected else "EXPOSED"
        }
