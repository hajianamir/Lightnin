import numpy as np

class RollingSphereEngine:
    """
    3D Analytical Rolling Sphere Engine for IEC 62305-3 protection assessment.
    Determines surface exposure and clearance without depending on WebGL rendering.
    """
    def __init__(self, sphere_radius_m: float = 20.0): # 20m for Class I
        self.r = sphere_radius_m

    def check_surface_exposure(self, point_x: float, point_y: float, point_z: float,
                               rod_x: float, rod_y: float, rod_height_m: float) -> dict:
        """
        Calculates if a target rooftop point is protected under a rolling sphere of radius R resting on an air-termination rod.
        Sphere touches rod tip (rod_x, rod_y, rod_height_m) and reference ground/roof plane.
        """
        d_horiz = np.sqrt((point_x - rod_x)**2 + (point_y - rod_y)**2)

        if d_horiz > self.r:
            return {"protected": False, "clearance_z_m": 0.0, "reason": "Horizontal distance exceeds sphere radius"}

        # Height of protective sphere bottom surface at distance d_horiz
        # Sphere center height z_c when resting on rod tip is rod_height_m - r + sqrt(r^2 - 0) if on ground,
        # Or under protective cone profile z_protect = rod_height_m - (r - sqrt(r^2 - d_horiz^2))
        z_protect = rod_height_m - (self.r - np.sqrt(max(0.0, self.r**2 - d_horiz**2)))

        is_protected = point_z <= z_protect
        return {
            "protected": bool(is_protected),
            "clearance_z_m": float(max(0.0, z_protect - point_z)),
            "protective_height_z_m": float(z_protect)
        }
