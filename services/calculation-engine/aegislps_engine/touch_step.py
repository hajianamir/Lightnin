import numpy as np
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class TouchStepAssessmentInput(BaseModel):
    lps_class: str = "I"
    soil_resistivity_ohm_m: float = 100.0
    surface_layer_material: str = "bare_soil" # bare_soil, gravel_5cm, asphalt_5cm, concrete
    surface_layer_thickness_m: float = 0.05
    surface_layer_resistivity_ohm_m: float = 100.0 # Override if specified
    fault_duration_s: float = 0.05 # Typical impulse duration / fast protection trip
    body_weight_kg: float = 70.0 # 50kg or 70kg IEEE 80 criterion
    peak_impulse_current_ka: float = 100.0
    down_conductor_radius_m: float = 0.005 # 10mm round down-conductor
    has_physical_insulation_barrier: bool = False # e.g. 3m XLPE conduit 100kV
    has_restricted_access_perimeter: bool = False # Fencing >= 3m

class TouchStepAssessmentResult(BaseModel):
    tolerable_touch_voltage_v: float
    tolerable_step_voltage_v: float
    prospective_touch_voltage_v: float
    prospective_step_voltage_v: float
    surface_derating_factor_cs: float
    touch_hazard_controlled: bool
    step_hazard_controlled: bool
    touch_safety_margin_v: float
    step_safety_margin_v: float
    status: str
    recommended_mitigations: List[str] = Field(default_factory=list)

class TouchStepEngine:
    """
    Advanced Touch & Step Potential Assessment Engine.

    Implements:
    - IEEE 80-2013 & IEC 62305-3 Section 8 criteria for touch and step potentials
    - Non-linear surface layer derating factor C_s(h_s, rho, rho_s)
    - Hemispherical current dispersion potential distribution V(r)
    - Explicit evaluation of tolerable limits U_touch,tol and U_step,tol
    """
    @staticmethod
    def calculate_surface_derating_cs(rho_soil: float, rho_surface: float, h_surface_m: float) -> float:
        """
        IEEE 80-2013 Equation 27 for surface layer derating factor C_s.
        """
        if rho_surface <= 0 or h_surface_m <= 0 or abs(rho_surface - rho_soil) < 1.0:
            return 1.0

        # Reflection factor K = (rho_soil - rho_surface) / (rho_soil + rho_surface)
        k = (rho_soil - rho_surface) / (rho_soil + rho_surface)

        # Series summation approximation
        sum_terms = 0.0
        for n in range(1, 10):
            sum_terms += (k ** n) / np.sqrt(1.0 + (2.0 * n * h_surface_m / 0.08) ** 2)

        c_s = 1.0 - (0.09 * (1.0 - rho_soil / rho_surface) / (2.0 * h_surface_m + 0.09))
        return float(min(1.0, max(0.1, c_s)))

    def evaluate(self, inp: TouchStepAssessmentInput) -> TouchStepAssessmentResult:
        # Resolve surface layer resistivity
        rho_surface = inp.surface_layer_resistivity_ohm_m
        if inp.surface_layer_material == "gravel_5cm":
            rho_surface = max(rho_surface, 3000.0) # Wet crushed rock
        elif inp.surface_layer_material == "asphalt_5cm":
            rho_surface = max(rho_surface, 10000.0)
        elif inp.surface_layer_material == "concrete":
            rho_surface = max(rho_surface, 1000.0)
        else:
            rho_surface = inp.soil_resistivity_ohm_m

        cs = self.calculate_surface_derating_cs(inp.soil_resistivity_ohm_m, rho_surface, inp.surface_layer_thickness_m)

        # Tolerable body voltages (Dalziel / IEEE 80 criterion for 70kg body weight)
        # R_body = 1000 ohm. Foot resistance R_foot = 3 * C_s * rho_s
        # U_touch,tol = (1000 + 1.5 * C_s * rho_s) * (0.157 / sqrt(t_f))
        t_f = max(0.01, inp.fault_duration_s)
        k_t = 0.157 / np.sqrt(t_f) if inp.body_weight_kg >= 70.0 else 0.116 / np.sqrt(t_f)

        u_touch_tol = (1000.0 + 1.5 * cs * rho_surface) * k_t
        u_step_tol = (1000.0 + 6.0 * cs * rho_surface) * k_t

        # Prospective potentials from hemispherical injection at earth electrode
        # V(r) = (I * rho) / (2 * pi * r)
        i_a = inp.peak_impulse_current_ka * 1e3
        rho_ground = inp.soil_resistivity_ohm_m

        # Touch potential at 1 meter reach distance from down conductor base
        # U_touch_prospective = V_conductor - V(r=1m)
        r_cond = max(0.005, inp.down_conductor_radius_m)
        v_conductor = (i_a * rho_ground) / (2.0 * np.pi * r_cond * 10.0) # Attenuated by earth system impedance
        v_reach_1m = (i_a * rho_ground) / (2.0 * np.pi * 1.0 * 10.0)

        # Prospective touch and step voltages
        prospective_touch = max(0.0, v_conductor - v_reach_1m)
        prospective_step = max(0.0, (i_a * rho_ground / (20.0 * np.pi)) * (1.0 / 1.0 - 1.0 / 2.0))

        # Mitigation credit: physical barrier or insulation reduces prospective voltage to negligible level
        if inp.has_physical_insulation_barrier:
            prospective_touch = 0.0
            prospective_step = min(prospective_step, u_step_tol * 0.5)
        if inp.has_restricted_access_perimeter:
            prospective_touch = 0.0
            prospective_step = 0.0

        touch_controlled = prospective_touch <= u_touch_tol
        step_controlled = prospective_step <= u_step_tol

        margin_touch = float(u_touch_tol - prospective_touch)
        margin_step = float(u_step_tol - prospective_step)

        mitigations = []
        if not touch_controlled:
            mitigations.append("Install high-voltage XLPE insulating conduit (100 kV, 1.2/50us) over lower 3m of down conductor")
            mitigations.append("Apply a 5cm layer of asphalt (resistivity >= 10 kOhm.m) within 3m radius")
            mitigations.append("Erect physical barrier/fence restricting public access within 3m")
        if not step_controlled:
            mitigations.append("Lay 10cm crushed rock/gravel layer (resistivity >= 3 kOhm.m) over earth electrode zone")
            mitigations.append("Install equipotential earth mesh ring buried at 0.5m depth around perimeter")

        status = "COMPLIANT" if (touch_controlled and step_controlled) else "HAZARD_DETECTED"

        return TouchStepAssessmentResult(
            tolerable_touch_voltage_v=round(float(u_touch_tol), 1),
            tolerable_step_voltage_v=round(float(u_step_tol), 1),
            prospective_touch_voltage_v=round(float(prospective_touch), 1),
            prospective_step_voltage_v=round(float(prospective_step), 1),
            surface_derating_factor_cs=round(float(cs), 3),
            touch_hazard_controlled=touch_controlled,
            step_hazard_controlled=step_controlled,
            touch_safety_margin_v=round(margin_touch, 1),
            step_safety_margin_v=round(margin_step, 1),
            status=status,
            recommended_mitigations=mitigations
        )
