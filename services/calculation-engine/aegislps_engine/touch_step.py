import numpy as np
from typing import List, Optional
from pydantic import BaseModel, Field

MITIGATION_WARNING_TEXT = (
    "Mitigation flags are recommendations only. Any reduction credit requires "
    "engineer verification and is NOT applied in this calculation."
)


class TouchStepAssessmentInput(BaseModel):
    lps_class: str = "I"
    soil_resistivity_ohm_m: float = 100.0
    surface_layer_material: str = "bare_soil"  # bare_soil, gravel_5cm, asphalt_5cm, concrete
    surface_layer_thickness_m: float = 0.05
    surface_layer_resistivity_ohm_m: float = 100.0  # Override if specified
    fault_duration_s: float = 0.05  # Typical impulse duration / fast protection trip
    body_weight_kg: float = 70.0  # 50kg or 70kg IEEE 80 criterion
    peak_impulse_current_ka: float = 100.0
    down_conductor_radius_m: float = 0.005  # 10mm round down-conductor
    has_physical_insulation_barrier: bool = False  # e.g. 3m XLPE conduit 100kV
    has_restricted_access_perimeter: bool = False  # Fencing >= 3m
    earth_potential_rise_v: Optional[float] = None
    electrode_equivalent_radius_m: Optional[float] = None


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
    formula_trace: List[str]
    mitigation_credit_applied: bool
    mitigation_warning: str


class TouchStepEngine:
    """
    Advanced Touch & Step Potential Assessment Engine.

    Implements:
    - IEEE 80-2013 tolerable touch and step voltage limits U_touch,tol and U_step,tol
    - Closed-form surface layer derating factor C_s(h_s, rho, rho_s) (IEEE 80-2013 Eq. 27)
    - Hemispherical surface potential distribution V(x) = GPR * r_e / (r_e + x)
      for distance x >= 0 measured outward from the electrode surface
    """

    @staticmethod
    def calculate_surface_derating_cs(
        rho_soil: float, rho_surface: float, h_surface_m: float
    ) -> float:
        """
        IEEE 80-2013 Equation 27 closed-form expression for surface layer derating factor C_s.
        """
        if rho_surface <= 0 or h_surface_m <= 0 or abs(rho_surface - rho_soil) < 1.0:
            return 1.0

        c_s = 1.0 - (0.09 * (1.0 - rho_soil / rho_surface) / (2.0 * h_surface_m + 0.09))
        return float(min(1.0, max(0.1, c_s)))

    def evaluate(self, inp: TouchStepAssessmentInput) -> TouchStepAssessmentResult:
        if (
            inp.earth_potential_rise_v is None
            or inp.electrode_equivalent_radius_m is None
        ):
            raise ValueError(
                "GPR required: earth_potential_rise_v and electrode_equivalent_radius_m must be provided"
            )

        gpr = float(inp.earth_potential_rise_v)
        r_e = float(inp.electrode_equivalent_radius_m)
        if not np.isfinite(gpr) or gpr <= 0.0:
            raise ValueError(
                f"earth_potential_rise_v must be > 0, got {inp.earth_potential_rise_v}"
            )
        if not np.isfinite(r_e) or r_e <= 0.0:
            raise ValueError(
                f"electrode_equivalent_radius_m must be > 0, got {inp.electrode_equivalent_radius_m}"
            )

        # Resolve surface layer resistivity
        rho_surface = inp.surface_layer_resistivity_ohm_m
        if inp.surface_layer_material == "gravel_5cm":
            rho_surface = max(rho_surface, 3000.0)  # Wet crushed rock
        elif inp.surface_layer_material == "asphalt_5cm":
            rho_surface = max(rho_surface, 10000.0)
        elif inp.surface_layer_material == "concrete":
            rho_surface = max(rho_surface, 1000.0)
        else:
            rho_surface = inp.soil_resistivity_ohm_m

        rho_soil = float(inp.soil_resistivity_ohm_m)
        h_s = float(inp.surface_layer_thickness_m)
        cs = self.calculate_surface_derating_cs(rho_soil, rho_surface, h_s)

        # Tolerable body voltages (Dalziel / IEEE 80 criterion)
        t_f = max(0.01, float(inp.fault_duration_s))
        body_coeff = 0.157 if inp.body_weight_kg >= 70.0 else 0.116
        k_t = float(body_coeff / np.sqrt(t_f))

        u_touch_tol = float((1000.0 + 1.5 * cs * rho_surface) * k_t)
        u_step_tol = float((1000.0 + 6.0 * cs * rho_surface) * k_t)

        # Hemispherical potential at distance x from the electrode surface:
        # V(x) = GPR * r_e / (r_e + x)
        v_1m = float(gpr * r_e / (r_e + 1.0))
        v_2m = float(gpr * r_e / (r_e + 2.0))

        prospective_touch = float(gpr - v_1m)
        prospective_step = float(v_1m - v_2m)

        touch_controlled = prospective_touch <= u_touch_tol
        step_controlled = prospective_step <= u_step_tol

        margin_touch = float(u_touch_tol - prospective_touch)
        margin_step = float(u_step_tol - prospective_step)

        if rho_surface <= 0 or h_s <= 0 or abs(rho_surface - rho_soil) < 1.0:
            cs_trace = (
                f"C_s = 1.0 (guard: rho={rho_soil:.3f}, rho_s={rho_surface:.3f}, "
                f"h_s={h_s:.3f}) -> {cs:.3f}"
            )
        else:
            cs_trace = (
                f"C_s = 1 - 0.09 * (1 - rho / rho_s) / (2 * h_s + 0.09) = "
                f"1 - 0.09 * (1 - {rho_soil:.3f} / {rho_surface:.3f}) / "
                f"(2 * {h_s:.3f} + 0.09) -> {cs:.3f}"
            )

        formula_trace = [
            cs_trace,
            f"k_t = {body_coeff} / sqrt(t_f) = {body_coeff} / sqrt({t_f:.4f}) -> {k_t:.6f}",
            (
                f"U_touch,tol = (1000 + 1.5 * C_s * rho_s) * k_t = "
                f"(1000 + 1.5 * {cs:.3f} * {rho_surface:.3f}) * {k_t:.6f} -> {u_touch_tol:.2f} V"
            ),
            (
                f"U_step,tol = (1000 + 6 * C_s * rho_s) * k_t = "
                f"(1000 + 6 * {cs:.3f} * {rho_surface:.3f}) * {k_t:.6f} -> {u_step_tol:.2f} V"
            ),
            f"V(1) = GPR * r_e / (r_e + 1) = {gpr:.2f} * {r_e:.4f} / ({r_e:.4f} + 1.0) -> {v_1m:.2f} V",
            f"V(2) = GPR * r_e / (r_e + 2) = {gpr:.2f} * {r_e:.4f} / ({r_e:.4f} + 2.0) -> {v_2m:.2f} V",
            f"U_touch,prosp = GPR - V(1) = {gpr:.2f} - {v_1m:.2f} -> {prospective_touch:.2f} V",
            f"U_step,prosp = V(1) - V(2) = {v_1m:.2f} - {v_2m:.2f} -> {prospective_step:.2f} V",
        ]

        mitigations: List[str] = []
        if inp.has_physical_insulation_barrier:
            mitigations.append(
                "Physical barrier flagged: credit requires engineer verification"
            )
        if inp.has_restricted_access_perimeter:
            mitigations.append(
                "Restricted access perimeter flagged: credit requires engineer verification"
            )
        if not touch_controlled:
            mitigations.append(
                "Install high-voltage XLPE insulating conduit (100 kV, 1.2/50us) over lower 3m of down conductor"
            )
            mitigations.append(
                "Apply a 5cm layer of asphalt (resistivity >= 10 kOhm.m) within 3m radius"
            )
            mitigations.append(
                "Erect physical barrier/fence restricting public access within 3m"
            )
        if not step_controlled:
            mitigations.append(
                "Lay 10cm crushed rock/gravel layer (resistivity >= 3 kOhm.m) over earth electrode zone"
            )
            mitigations.append(
                "Install equipotential earth mesh ring buried at 0.5m depth around perimeter"
            )

        status = "COMPLIANT" if (touch_controlled and step_controlled) else "HAZARD_DETECTED"

        return TouchStepAssessmentResult(
            tolerable_touch_voltage_v=round(u_touch_tol, 1),
            tolerable_step_voltage_v=round(u_step_tol, 1),
            prospective_touch_voltage_v=round(prospective_touch, 1),
            prospective_step_voltage_v=round(prospective_step, 1),
            surface_derating_factor_cs=round(cs, 3),
            touch_hazard_controlled=touch_controlled,
            step_hazard_controlled=step_controlled,
            touch_safety_margin_v=round(margin_touch, 1),
            step_safety_margin_v=round(margin_step, 1),
            status=status,
            recommended_mitigations=mitigations,
            formula_trace=formula_trace,
            mitigation_credit_applied=False,
            mitigation_warning=MITIGATION_WARNING_TEXT,
        )
