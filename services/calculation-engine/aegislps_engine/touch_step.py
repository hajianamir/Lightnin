import math
import numpy as np
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MITIGATION_WARNING_TEXT = (
    "Mitigation flags are recommendations only. Any reduction credit requires "
    "engineer verification and is NOT applied in this calculation."
)

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")
_VALID_SURFACE_MATERIALS = ("bare_soil", "gravel_5cm", "asphalt_5cm", "concrete")
_BODY_WEIGHT_COEFFICIENTS = {
    50.0: 0.116,
    70.0: 0.157,
}


def _check_positive_finite(name: str, val: object) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float, np.number)):
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    val_f = float(val)
    if not math.isfinite(val_f) or val_f <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    return val_f


class TouchStepAssessmentInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    # Unused in evaluate(); required for API consistency across LPS endpoints.
    lps_class: str
    soil_resistivity_ohm_m: float
    surface_layer_material: str  # bare_soil, gravel_5cm, asphalt_5cm, concrete
    # Default 0.05 m (5 cm) applies ONLY as the surface-layer thickness when a
    # protective surface material != "bare_soil" is selected (e.g. gravel_5cm /
    # asphalt_5cm; see IEC 62305-3:2024 Clause 8.1 / IEEE Std 80-2013 Clause 7.4).
    # For "bare_soil", IEEE Std 80-2013 Clause 8.4 states:
    # "If no protective surface layer is used, then Cs =1 and rho_s = rho."
    surface_layer_thickness_m: float = 0.05
    # Required when surface_layer_material != "bare_soil"; never overwritten by a floor.
    # IEEE Std 80-2013 Clause 12.4 / Table 7 ("Typical surface material resistivities"):
    # "Table 7 gives typical resistivity values for different types of surface material
    # measured by several different parties in different regions of the United States ...
    # These values are not valid for all types and sizes of stone in any given region.
    # Tests should be performed to determine the resistivity of the stone typically
    # purchased by the utility."
    surface_layer_resistivity_ohm_m: Optional[float] = None
    # IEEE Std 80-2013 Clause 6.1 (Eq. 7 validity domain):
    # "Because Equation (7) is based on tests limited to a range of between 0.03 s and
    # 3.0 s, it obviously is not valid for very short or long durations."
    fault_duration_s: float
    # IEEE Std 80-2013 Clauses 6.1-6.2:
    # - 50 kg is the general public value (Clause 6.1, Eq. 8: "Dalziel found that the
    #   shock energy that can be survived by 99.5% of persons weighing approximately
    #   50 kg (110 lb) results in a value of SB of 0.0135. Thus, k50 = 0.116").
    # - 70 kg applies only where population weight >= 70 kg (Clause 6.2, Eq. 9:
    #   "Users of this guide may select k = 0.157 provided that the average population
    #   weight can be expected to be at least 70 kg.").
    body_weight_kg: float
    # Unused in evaluate(); required for API schema consistency.
    peak_impulse_current_ka: float
    # Unused in evaluate(); required for API schema consistency.
    down_conductor_radius_m: float
    # Conservative defaults False (mitigation flags never apply automatic voltage credit).
    has_physical_insulation_barrier: bool = False
    has_restricted_access_perimeter: bool = False
    earth_potential_rise_v: float
    electrode_equivalent_radius_m: float

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v):
        if not isinstance(v, str) or v not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        return v

    @field_validator("surface_layer_material", mode="before")
    @classmethod
    def _validate_surface_material(cls, v):
        if not isinstance(v, str) or v not in _VALID_SURFACE_MATERIALS:
            raise ValueError(
                f"Unknown surface_layer_material {v!r}; expected one of {_VALID_SURFACE_MATERIALS}."
            )
        return v

    @field_validator(
        "has_physical_insulation_barrier",
        "has_restricted_access_perimeter",
        mode="before",
    )
    @classmethod
    def _require_strict_bool(cls, v):
        if not isinstance(v, bool):
            raise ValueError(f"Mitigation flag must be a strict boolean, got {v!r}.")
        return v

    @field_validator(
        "soil_resistivity_ohm_m",
        "peak_impulse_current_ka",
        "down_conductor_radius_m",
        "earth_potential_rise_v",
        "electrode_equivalent_radius_m",
        mode="before",
    )
    @classmethod
    def _validate_positive_fields(cls, v, info):
        return _check_positive_finite(info.field_name, v)

    @field_validator(
        "surface_layer_thickness_m",
        "surface_layer_resistivity_ohm_m",
        "fault_duration_s",
        "body_weight_kg",
        mode="before",
    )
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric touch/step parameter.")
        return v

    @field_validator("fault_duration_s")
    @classmethod
    def _validate_fault_duration(cls, v: float) -> float:
        if not math.isfinite(v) or v < 0.03 or v > 3.0:
            raise ValueError(
                f"fault_duration_s must be in [0.03, 3.0] s per IEEE Std 80-2013 Clause 6.1, got {v!r}."
            )
        return float(v)

    @field_validator("body_weight_kg")
    @classmethod
    def _validate_body_weight(cls, v: float) -> float:
        if not math.isfinite(v) or float(v) not in _BODY_WEIGHT_COEFFICIENTS:
            raise ValueError(
                f"body_weight_kg must be 50.0 or 70.0 per IEEE Std 80-2013 Clauses 6.1-6.2, got {v!r}."
            )
        return float(v)

    @model_validator(mode="after")
    def _validate_surface_layer_combination(self) -> "TouchStepAssessmentInput":
        if not math.isfinite(self.surface_layer_thickness_m) or self.surface_layer_thickness_m < 0.0:
            raise ValueError(
                f"surface_layer_thickness_m must be finite and >= 0, got {self.surface_layer_thickness_m!r}."
            )
        if self.surface_layer_resistivity_ohm_m is not None:
            _check_positive_finite(
                "surface_layer_resistivity_ohm_m",
                self.surface_layer_resistivity_ohm_m,
            )
        if self.surface_layer_material != "bare_soil":
            if self.surface_layer_thickness_m <= 0.0:
                raise ValueError(
                    f"surface_layer_thickness_m must be > 0 when surface_layer_material={self.surface_layer_material!r}, "
                    f"got {self.surface_layer_thickness_m!r}."
                )
            if self.surface_layer_resistivity_ohm_m is None:
                raise ValueError(
                    f"surface_layer_resistivity_ohm_m is required when surface_layer_material={self.surface_layer_material!r}."
                )
        return self


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
        IEEE 80-2013 Equation 27 closed-form expression for surface layer derating factor C_s
        on protective surface layers (h_surface_m > 0, rho_soil > 0, rho_surface > 0).
        """
        rho_soil_f = _check_positive_finite("rho_soil", rho_soil)
        rho_surf_f = _check_positive_finite("rho_surface", rho_surface)
        h_s_f = _check_positive_finite("h_surface_m", h_surface_m)

        if abs(rho_surf_f - rho_soil_f) < 1.0:
            return 1.0

        c_s = 1.0 - (
            0.09 * (1.0 - rho_soil_f / rho_surf_f) / (2.0 * h_s_f + 0.09)
        )
        return float(min(1.0, max(0.1, c_s)))

    def evaluate(self, inp: TouchStepAssessmentInput) -> TouchStepAssessmentResult:
        if (
            inp.earth_potential_rise_v is None
            or inp.electrode_equivalent_radius_m is None
        ):
            raise ValueError(
                "GPR required: earth_potential_rise_v and electrode_equivalent_radius_m must be provided"
            )

        gpr = _check_positive_finite("earth_potential_rise_v", inp.earth_potential_rise_v)
        r_e = _check_positive_finite(
            "electrode_equivalent_radius_m", inp.electrode_equivalent_radius_m
        )
        rho_soil = _check_positive_finite(
            "soil_resistivity_ohm_m", inp.soil_resistivity_ohm_m
        )
        _check_positive_finite(
            "peak_impulse_current_ka", inp.peak_impulse_current_ka
        )
        _check_positive_finite(
            "down_conductor_radius_m", inp.down_conductor_radius_m
        )

        if (
            not isinstance(inp.lps_class, str)
            or inp.lps_class not in _VALID_LPS_CLASSES
        ):
            raise ValueError(
                f"Unknown LPS class {inp.lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        if (
            not isinstance(inp.surface_layer_material, str)
            or inp.surface_layer_material not in _VALID_SURFACE_MATERIALS
        ):
            raise ValueError(
                f"Unknown surface_layer_material {inp.surface_layer_material!r}; "
                f"expected one of {_VALID_SURFACE_MATERIALS}."
            )

        h_s = float(inp.surface_layer_thickness_m)
        if not math.isfinite(h_s) or h_s < 0.0:
            raise ValueError(
                f"surface_layer_thickness_m must be finite and >= 0, got {inp.surface_layer_thickness_m!r}."
            )

        # Resolve surface layer resistivity and C_s without overwriting measured values
        if inp.surface_layer_material == "bare_soil":
            # IEEE Std 80-2013 Clause 8.4:
            # "If no protective surface layer is used, then Cs =1 and rho_s = rho."
            rho_surface = rho_soil
            cs = 1.0
        elif inp.surface_layer_material in ("gravel_5cm", "asphalt_5cm", "concrete"):
            if h_s <= 0.0:
                raise ValueError(
                    f"surface_layer_thickness_m must be > 0 when surface_layer_material={inp.surface_layer_material!r}, "
                    f"got {inp.surface_layer_thickness_m!r}."
                )
            if inp.surface_layer_resistivity_ohm_m is None:
                raise ValueError(
                    f"surface_layer_resistivity_ohm_m is required when surface_layer_material={inp.surface_layer_material!r}."
                )
            rho_surface = _check_positive_finite(
                "surface_layer_resistivity_ohm_m",
                inp.surface_layer_resistivity_ohm_m,
            )
            cs = self.calculate_surface_derating_cs(rho_soil, rho_surface, h_s)
        else:
            raise ValueError(
                f"Unknown surface_layer_material {inp.surface_layer_material!r}; "
                f"expected one of {_VALID_SURFACE_MATERIALS}."
            )

        # Tolerable body voltages (Dalziel / IEEE Std 80-2013 Clauses 6.1-6.2)
        t_f = float(inp.fault_duration_s)
        if not math.isfinite(t_f) or t_f < 0.03 or t_f > 3.0:
            raise ValueError(
                f"fault_duration_s must be in [0.03, 3.0] s per IEEE Std 80-2013 Clause 6.1, got {inp.fault_duration_s!r}."
            )
        weight_f = float(inp.body_weight_kg)
        if weight_f not in _BODY_WEIGHT_COEFFICIENTS:
            raise ValueError(
                f"body_weight_kg must be 50.0 or 70.0 per IEEE Std 80-2013 Clauses 6.1-6.2, got {inp.body_weight_kg!r}."
            )
        body_coeff = _BODY_WEIGHT_COEFFICIENTS[weight_f]
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

        if inp.surface_layer_material == "bare_soil" or abs(rho_surface - rho_soil) < 1.0:
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

        status = (
            "COMPLIANT"
            if (touch_controlled and step_controlled)
            else "HAZARD_DETECTED"
        )

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
