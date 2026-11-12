import numpy as np
from typing import Any, Dict, List, Tuple

# IEC 62305-3:2024, Clause 5.2.2.1, Table 2 (p. 21) & Figure 1 NOTE 1 (p. 22)
MAX_HEIGHTS: Dict[str, float] = {
    "I": 20.0,
    "II": 30.0,
    "III": 45.0,
    "IV": 60.0,
}

# Graphical reading of IEC 62305-3:2024 Figure 1 (p. 22); digitization ±1.5°.
# Points interpolated during digitization carry ±0.3° interpolation precision:
#   Class II: (15.0, 45.7), (28.0, 26.4)
#   Class III: (15.0, 54.4)
#   Class IV: (26.0, 48.5), (45.0, 34.0)
TABULATED_ANGLES: Dict[str, List[Tuple[float, float]]] = {
    "I": [
        (2.0, 70.0),
        (4.0, 63.4),
        (6.0, 56.5),
        (8.0, 50.9),
        (10.0, 45.3),
        (12.0, 40.9),
        (14.0, 36.0),
        (16.0, 31.9),
        (18.0, 27.4),
        (20.0, 22.4),
    ],
    "II": [
        (2.0, 73.4),
        (4.0, 68.1),
        (6.0, 62.5),
        (8.0, 58.2),
        (10.0, 54.1),
        (12.0, 50.7),
        (14.0, 47.3),
        (15.0, 45.7),
        (16.0, 44.2),
        (18.0, 41.1),
        (19.0, 39.7),
        (20.0, 37.9),
        (22.0, 35.3),
        (24.0, 32.4),
        (25.0, 30.4),
        (26.0, 29.4),
        (28.0, 26.4),
        (30.0, 23.3),
    ],
    "III": [
        (2.0, 76.5),
        (4.0, 72.7),
        (6.0, 68.5),
        (8.0, 64.9),
        (10.0, 61.3),
        (12.0, 58.5),
        (14.0, 55.7),
        (15.0, 54.4),
        (16.0, 53.2),
        (18.0, 50.7),
        (19.0, 49.4),
        (20.0, 47.9),
        (22.0, 45.7),
        (24.0, 43.6),
        (25.0, 42.3),
        (26.0, 41.0),
        (28.0, 38.9),
        (30.0, 36.9),
        (32.0, 35.1),
        (34.0, 33.1),
        (36.0, 31.2),
        (38.0, 29.5),
        (40.0, 27.5),
        (42.0, 25.6),
        (44.0, 23.7),
        (45.0, 23.3),
    ],
    "IV": [
        (2.0, 79.0),
        (4.0, 75.4),
        (6.0, 71.2),
        (8.0, 68.2),
        (10.0, 65.4),
        (12.0, 62.4),
        (14.0, 59.9),
        (16.0, 57.4),
        (18.0, 55.4),
        (20.0, 53.4),
        (22.0, 51.7),
        (24.0, 50.0),
        (26.0, 48.5),
        (28.0, 46.6),
        (30.0, 45.0),
        (32.0, 43.6),
        (34.0, 42.0),
        (36.0, 40.4),
        (38.0, 39.1),
        (40.0, 37.7),
        (44.0, 35.0),
        (45.0, 34.0),
        (46.0, 33.1),
        (50.0, 30.2),
        (58.0, 24.5),
        (60.0, 22.5),
    ],
}


class ProtectiveAngleEngine:
    """
    Standards-Controlled Protective Angle Method Engine.

    Graphical reading of IEC 62305-3:2024 Figure 1 (p. 22); digitization ±1.5°.
    Uses piecewise-linear interpolation between consecutive digitized anchors as an
    approximation of the smooth Figure 1 curves.
    - Figure 1 NOTE 3: the protection angle does not change for 0 < h < 2 m (returns alpha(2 m)).
    - Figure 1 NOTE 1 & Table 2 (p. 21): not applicable for h > MAX_HEIGHTS[class]
      (20 m Class I, 30 m Class II, 45 m Class III, 60 m Class IV).
    """

    TABULATED_ANGLES = TABULATED_ANGLES
    MAX_HEIGHTS = MAX_HEIGHTS

    @classmethod
    def get_protective_angle_deg(cls, lps_class: str, h_m: float) -> float:
        """
        Return protection angle alpha (degrees) for `lps_class` at reference height `h_m` (m).

        Graphical reading of IEC 62305-3:2024 Figure 1 (p. 22); digitization ±1.5°.
        Piecewise-linear interpolation between consecutive anchors approximates the smooth curve.
        """
        if not isinstance(lps_class, str) or lps_class not in cls.TABULATED_ANGLES:
            raise ValueError(
                f"Unknown LPS class {lps_class!r}; expected one of {tuple(cls.TABULATED_ANGLES)}."
            )
        if isinstance(h_m, bool) or not isinstance(h_m, (int, float, np.number)):
            raise ValueError(f"Reference height h_m must be a finite positive number, got {h_m!r}.")
        h = float(h_m)
        if not np.isfinite(h) or h <= 0.0:
            raise ValueError(f"Reference height h_m must be finite and > 0 m, got {h_m!r}.")

        max_h = cls.MAX_HEIGHTS[lps_class]
        if h > max_h:
            raise ValueError(
                f"Reference height h_m={h} m exceeds IEC 62305-3:2024 Figure 1 maximum height "
                f"h_max={max_h} m for LPS Class {lps_class}."
            )

        anchors = cls.TABULATED_ANGLES[lps_class]
        if h <= anchors[0][0]:
            return float(anchors[0][1])

        for i in range(len(anchors) - 1):
            h1, a1 = anchors[i]
            h2, a2 = anchors[i + 1]
            if h == h1:
                return float(a1)
            if h == h2:
                return float(a2)
            if h1 < h < h2:
                fraction = (h - h1) / (h2 - h1)
                return float(a1 + fraction * (a2 - a1))

        return float(anchors[-1][1])

    def check_object_in_cone(
        self,
        lps_class: str,
        rod_tip_x: float,
        rod_tip_y: float,
        rod_tip_z: float,
        ref_plane_z: float,
        object_x: float,
        object_y: float,
        object_z: float,
    ) -> Dict[str, Any]:
        if not isinstance(lps_class, str) or lps_class not in self.MAX_HEIGHTS:
            raise ValueError(
                f"Unknown LPS class {lps_class!r}; expected one of {tuple(self.MAX_HEIGHTS)}."
            )

        coords: Dict[str, float] = {}
        for name, val in (
            ("rod_tip_x", rod_tip_x),
            ("rod_tip_y", rod_tip_y),
            ("rod_tip_z", rod_tip_z),
            ("ref_plane_z", ref_plane_z),
            ("object_x", object_x),
            ("object_y", object_y),
            ("object_z", object_z),
        ):
            if isinstance(val, bool) or not isinstance(val, (int, float, np.number)):
                raise ValueError(
                    f"{name} must be a finite number, not bool; got {val!r}."
                )
            fval = float(val)
            if not np.isfinite(fval):
                raise ValueError(f"{name} must be finite, got {val!r}.")
            coords[name] = fval

        h_tip = float(coords["rod_tip_z"] - coords["ref_plane_z"])
        if not np.isfinite(h_tip) or h_tip <= 0.0:
            raise ValueError(
                f"h_tip = rod_tip_z - ref_plane_z must be finite and > 0 m, got {h_tip!r}."
            )

        max_permitted_h = self.MAX_HEIGHTS[lps_class]
        if h_tip > max_permitted_h:
            return {
                "protected": False,
                "applicable": False,
                "protective_angle_deg": 0.0,
                "reason": (
                    f"Height ({h_tip:.1f}m) exceeds IEC 62305-3 limit ({max_permitted_h}m) "
                    f"for Class {lps_class}. Must use Rolling Sphere."
                ),
            }

        alpha_deg = self.get_protective_angle_deg(lps_class, h_tip)

        delta_z = coords["rod_tip_z"] - coords["object_z"]
        if delta_z <= 0:
            return {
                "protected": False,
                "applicable": True,
                "protective_angle_deg": round(float(alpha_deg), 1),
                "reason": "Object elevation is at or above rod tip",
            }

        d_horiz = float(
            np.sqrt(
                (coords["object_x"] - coords["rod_tip_x"]) ** 2
                + (coords["object_y"] - coords["rod_tip_y"]) ** 2
            )
        )
        r_cone = float(delta_z * np.tan(np.radians(alpha_deg)))
        is_protected = d_horiz <= r_cone

        return {
            "protected": bool(is_protected),
            "applicable": True,
            "protective_angle_deg": round(float(alpha_deg), 1),
            "protected_radius_at_z_m": round(r_cone, 2),
            "actual_horizontal_distance_m": round(d_horiz, 2),
            "clearance_margin_m": round(float(r_cone - d_horiz), 2),
            "status": "PROTECTED" if is_protected else "EXPOSED",
        }
