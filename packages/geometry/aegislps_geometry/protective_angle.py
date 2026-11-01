import numpy as np

class ProtectiveAngleEngine:
    """
    IEC 62305-3 Section 5.2.2 Protective Angle Method Engine.
    Calculates protective cone angle alpha based on LPS class and tip height H.
    """
    @staticmethod
    def get_protective_angle_deg(lps_class: str, height_above_ref_plane_m: float) -> float:
        """
        Evaluates protection angle alpha according to IEC 62305-3 Table 2 / Figure 1.
        Angles decrease non-linearly with increasing height H.
        """
        h = max(0.5, height_above_ref_plane_m)
        if lps_class == "I":
            # Class I: alpha ranges from ~70 deg (h=2m) to ~20 deg (h=20m)
            return float(max(0.0, 75.0 - 2.8 * h))
        elif lps_class == "II":
            return float(max(0.0, 78.0 - 2.2 * h))
        else: # Class III & IV
            return float(max(0.0, 82.0 - 1.5 * h))

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
    ) -> dict:
        h_rod = rod_tip_z - ref_plane_z
        alpha_deg = self.get_protective_angle_deg(lps_class, h_rod)
        alpha_rad = np.radians(alpha_deg)

        # Distance from rod axis
        d_horiz = np.sqrt((object_x - rod_tip_x)**2 + (object_y - rod_tip_y)**2)

        # Max protected horizontal radius at object height z
        # r(z) = (rod_tip_z - object_z) * tan(alpha)
        delta_z = rod_tip_z - object_z
        if delta_z < 0:
            return {"protected": False, "reason": "Object height exceeds air termination tip"}

        r_protected = delta_z * np.tan(alpha_rad)
        is_protected = d_horiz <= r_protected

        return {
            "protected": bool(is_protected),
            "protective_angle_deg": round(float(alpha_deg), 1),
            "protected_radius_at_z_m": round(float(r_protected), 2),
            "actual_horizontal_distance_m": round(float(d_horiz), 2),
            "clearance_margin_m": round(float(r_protected - d_horiz), 2)
        }
