import math
import numpy as np
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

RING_METHOD_LABEL = (
    "Sunde equivalent-radius form (approximate; primary-source confirmation pending)"
)

STRIP_MODEL_BOUNDARY_NOTE = (
    "round-conductor equivalent (k = 2 - ln 2); flat-strip model not implemented"
)

MULTI_ROD_METHOD_LABEL = (
    "Dwight self-resistance + pairwise mutual "
    "(uniform-leakage, equal-current; primary-source confirmation pending)"
)

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")
_VALID_ELECTRODE_TYPES = (
    "type_a_vertical",
    "type_a_horizontal",
    "type_b_ring",
    "foundation",
)

# IEC 62305-1:2024 Table 3 (p. 26), "Maximum values of lightning parameters according to LPLs",
# First positive short stroke (T1/T2 = 10/350 us), peak current I [kA]:
#   LPL I = 200 kA, LPL II = 150 kA, LPL III = 100 kA, LPL IV = 100 kA.
LPL_FIRST_POSITIVE_PEAK_CURRENT_KA: Dict[str, float] = {
    "I": 200.0,
    "II": 150.0,
    "III": 100.0,
    "IV": 100.0,
}


def _check_positive_finite_float(name: str, val: object) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float, np.number)):
        raise ValueError(f"{name} must be a finite number > 0, got {val!r}.")
    val_f = float(val)
    if not math.isfinite(val_f) or val_f <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    return val_f


def single_vertical_rod_resistance(rho: float, L: float, a: float) -> float:
    """Single vertical rod resistance R1 = (rho / (2*pi*L)) * [ln(4*L/a) - 1]."""
    if (
        isinstance(rho, bool)
        or isinstance(L, bool)
        or isinstance(a, bool)
        or not (np.isfinite(rho) and np.isfinite(L) and np.isfinite(a))
        or rho <= 0.0
        or L <= 0.0
        or a <= 0.0
    ):
        raise ValueError(
            f"rho, L, and a must be finite and > 0, got rho={rho!r}, L={L!r}, a={a!r}."
        )
    return float((rho / (2.0 * np.pi * L)) * (np.log((4.0 * L) / a) - 1.0))


def mutual_resistance_rods(rho: float, L: float, s: float) -> float:
    """
    Pairwise mutual resistance between two identical vertical rods of length L at spacing s
    under uniform current leakage:
        R_m(s) = (rho / (pi * L^2)) * [L * asinh(L / s) - sqrt(L^2 + s^2) + s]
    """
    if (
        isinstance(rho, bool)
        or isinstance(L, bool)
        or isinstance(s, bool)
        or not (np.isfinite(rho) and np.isfinite(L) and np.isfinite(s))
        or rho <= 0.0
        or L <= 0.0
        or s <= 0.0
    ):
        raise ValueError(
            f"rho, L, and s must be finite and > 0, got rho={rho!r}, L={L!r}, s={s!r}."
        )
    rho_f = float(rho)
    l_f = float(L)
    s_f = float(s)
    return float(
        (rho_f / (np.pi * l_f * l_f))
        * (l_f * np.arcsinh(l_f / s_f) - np.sqrt(l_f * l_f + s_f * s_f) + s_f)
    )


def array_resistance_identical_rods(
    rho: float, L: float, a: float, n: int, s: float
) -> float:
    """
    Linear array resistance of n identical vertical rods of length L and radius a at equal
    spacing s under the equal-current approximation:
        R_n = (1 / n^2) * [n * R_1 + 2 * sum_{k=1}^{n-1} (n - k) * R_m(k * s)]
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an integer >= 1, got {n!r}.")
    r1 = single_vertical_rod_resistance(rho, L, a)
    if n == 1:
        if isinstance(s, bool) or not np.isfinite(s) or s <= 0.0:
            raise ValueError(f"s must be finite and > 0, got {s!r}.")
        return r1
    pair_sum = sum(
        (n - k) * mutual_resistance_rods(rho, L, k * float(s))
        for k in range(1, n)
    )
    return float((n * r1 + 2.0 * pair_sum) / float(n * n))


def _validate_soil_layer_model(soil: "SoilLayerModel") -> None:
    if not isinstance(soil.is_two_layer, bool):
        raise ValueError(
            f"is_two_layer must be a strict boolean, got {soil.is_two_layer!r}."
        )
    rho1 = _check_positive_finite_float("rho_upper_ohm_m", soil.rho_upper_ohm_m)

    if soil.h_upper_m is not None:
        _check_positive_finite_float("h_upper_m", soil.h_upper_m)
    if soil.rho_lower_ohm_m is not None:
        _check_positive_finite_float("rho_lower_ohm_m", soil.rho_lower_ohm_m)

    if soil.is_two_layer:
        if soil.h_upper_m is None:
            raise ValueError("h_upper_m is required when is_two_layer=True.")
        if soil.rho_lower_ohm_m is None:
            raise ValueError("rho_lower_ohm_m is required when is_two_layer=True.")
        rho2 = _check_positive_finite_float("rho_lower_ohm_m", soil.rho_lower_ohm_m)
        ratio = rho1 / rho2
        if not math.isfinite(ratio) or ratio <= 0.0:
            raise ValueError(
                f"Soil resistivity ratio rho_upper_ohm_m / rho_lower_ohm_m is not valid: {ratio!r}."
            )


class SoilLayerModel(BaseModel):
    is_two_layer: bool = False
    rho_upper_ohm_m: float
    h_upper_m: Optional[float] = None
    rho_lower_ohm_m: Optional[float] = None

    @field_validator("is_two_layer", mode="before")
    @classmethod
    def _require_strict_bool(cls, v):
        if not isinstance(v, bool):
            raise ValueError(f"is_two_layer must be a strict boolean, got {v!r}.")
        return v

    @field_validator("rho_upper_ohm_m", "h_upper_m", "rho_lower_ohm_m", mode="before")
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric soil parameter.")
        return v

    @model_validator(mode="after")
    def _validate_soil(self) -> "SoilLayerModel":
        _validate_soil_layer_model(self)
        return self


def _validate_earthing_input(inp: "EarthingAssessmentInput") -> None:
    if not isinstance(inp.lps_class, str) or inp.lps_class not in _VALID_LPS_CLASSES:
        raise ValueError(
            f"Unknown LPS class {inp.lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
        )
    if inp.soil is None or not isinstance(inp.soil, SoilLayerModel):
        raise ValueError("soil (SoilLayerModel) is required.")
    _validate_soil_layer_model(inp.soil)

    if (
        not isinstance(inp.electrode_type, str)
        or inp.electrode_type not in _VALID_ELECTRODE_TYPES
    ):
        raise ValueError(
            f"Unknown electrode_type {inp.electrode_type!r}; expected one of {_VALID_ELECTRODE_TYPES}."
        )

    _check_positive_finite_float("conductor_diameter_m", inp.conductor_diameter_m)
    _check_positive_finite_float("burial_depth_m", inp.burial_depth_m)

    if inp.ring_radius_m is not None:
        _check_positive_finite_float("ring_radius_m", inp.ring_radius_m)
    if inp.vertical_rod_length_m is not None:
        _check_positive_finite_float(
            "vertical_rod_length_m", inp.vertical_rod_length_m
        )
    if inp.vertical_rod_spacing_m is not None:
        _check_positive_finite_float(
            "vertical_rod_spacing_m", inp.vertical_rod_spacing_m
        )
    if inp.vertical_rod_count is not None:
        if (
            isinstance(inp.vertical_rod_count, bool)
            or not isinstance(inp.vertical_rod_count, int)
            or inp.vertical_rod_count < 1
        ):
            raise ValueError(
                f"vertical_rod_count must be an integer >= 1, got {inp.vertical_rod_count!r}."
            )
    if inp.foundation_perimeter_m is not None:
        _check_positive_finite_float(
            "foundation_perimeter_m", inp.foundation_perimeter_m
        )
    if inp.foundation_area_m2 is not None:
        _check_positive_finite_float("foundation_area_m2", inp.foundation_area_m2)

    if inp.electrode_type == "type_b_ring":
        if inp.ring_radius_m is None:
            raise ValueError(
                "ring_radius_m is required when electrode_type == 'type_b_ring'."
            )
    elif inp.electrode_type == "type_a_vertical":
        if inp.vertical_rod_length_m is None:
            raise ValueError(
                "vertical_rod_length_m is required when electrode_type == 'type_a_vertical'."
            )
        if inp.vertical_rod_count is None:
            raise ValueError(
                "vertical_rod_count is required when electrode_type == 'type_a_vertical'."
            )
        if inp.vertical_rod_spacing_m is None:
            raise ValueError(
                "vertical_rod_spacing_m is required when electrode_type == 'type_a_vertical'."
            )
        # IEC 62305-3:2024 Clause 5.4.2.2 (p. 34):
        # "In Type A arrangements, the total number of earth electrodes shall be not less than two."
        if inp.vertical_rod_count < 2:
            raise ValueError(
                f"vertical_rod_count must be >= 2 for electrode_type='type_a_vertical' "
                f"(IEC 62305-3:2024 Clause 5.4.2.2), got {inp.vertical_rod_count!r}."
            )
    elif inp.electrode_type == "foundation":
        if inp.foundation_perimeter_m is None:
            raise ValueError(
                "foundation_perimeter_m is required when electrode_type == 'foundation'."
            )
        if inp.foundation_area_m2 is None:
            raise ValueError(
                "foundation_area_m2 is required when electrode_type == 'foundation'."
            )

    if inp.peak_impulse_current_ka is not None:
        _check_positive_finite_float(
            "peak_impulse_current_ka", inp.peak_impulse_current_ka
        )


class EarthingAssessmentInput(BaseModel):
    lps_class: str
    soil: SoilLayerModel
    electrode_type: str  # type_a_vertical, type_a_horizontal, type_b_ring, foundation
    ring_radius_m: Optional[float] = None
    strip_length_m: Optional[float] = None
    conductor_diameter_m: float
    # IEC 62305-3:2024 Clause 5.4.3 (p. 35): Type B ring "should preferably be buried at a depth
    # of at least 0,5 m" and Type A "shall be installed at a depth at least 0,5 m" (with NOTE 1
    # exemption in inspection housings or below high-resistance material).
    burial_depth_m: float = 0.5
    vertical_rod_length_m: Optional[float] = None
    vertical_rod_count: Optional[int] = None
    vertical_rod_spacing_m: Optional[float] = None
    foundation_perimeter_m: Optional[float] = None
    foundation_area_m2: Optional[float] = None
    # When omitted, derived from lps_class per IEC 62305-1:2024 Table 3 (p. 26), first positive
    # short stroke (10/350 us) peak current I [kA]: I=200.0, II=150.0, III=100.0, IV=100.0.
    peak_impulse_current_ka: Optional[float] = None

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class_field(cls, v):
        if not isinstance(v, str) or v not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        return v

    @field_validator("electrode_type", mode="before")
    @classmethod
    def _validate_electrode_type_field(cls, v):
        if not isinstance(v, str) or v not in _VALID_ELECTRODE_TYPES:
            raise ValueError(
                f"Unknown electrode_type {v!r}; expected one of {_VALID_ELECTRODE_TYPES}."
            )
        return v

    @field_validator(
        "ring_radius_m",
        "strip_length_m",
        "conductor_diameter_m",
        "burial_depth_m",
        "vertical_rod_length_m",
        "vertical_rod_spacing_m",
        "foundation_perimeter_m",
        "foundation_area_m2",
        "peak_impulse_current_ka",
        mode="before",
    )
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric earthing parameter.")
        return v

    @field_validator("vertical_rod_count", mode="before")
    @classmethod
    def _validate_rod_count_type(cls, v):
        if v is None:
            return v
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"vertical_rod_count must be an integer, got {v!r}.")
        return v

    @model_validator(mode="after")
    def _validate_all(self) -> "EarthingAssessmentInput":
        _validate_earthing_input(self)
        if self.peak_impulse_current_ka is None:
            self.peak_impulse_current_ka = LPL_FIRST_POSITIVE_PEAK_CURRENT_KA[
                self.lps_class
            ]
        return self


class EarthingAssessmentResult(BaseModel):
    lps_class: str
    effective_soil_resistivity_ohm_m: float
    minimum_length_l1_m: float
    actual_effective_length_m: float
    stationary_resistance_r_ohm: float
    impulse_impedance_z_ohm: float
    impulse_efficiency_factor: float
    meets_iec_l1_requirement: bool
    meets_recommended_10_ohm: bool
    status: str
    method_details: str
    warnings: List[str] = Field(default_factory=list)


class EarthingEngine:
    """
    Advanced IEC 62305-3 Section 5.4 & IEEE 80 Earthing Analysis Engine.

    Includes:
    - Dwight vertical-rod formulation, Sunde horizontal-strip formulation,
      buried ring via Sunde equivalent-radius form (approximate; primary-source confirmation pending),
      and Laurent & Nieman foundation mesh
    - Mutual coupling and array shielding efficiency factors for multiple vertical rods
    - Two-layer soil apparent resistivity modeling via Sunde reflection coefficient
    - Non-linear soil ionization impulse impedance reduction (Z_p) under high lightning currents
    """

    @staticmethod
    def calculate_apparent_resistivity(
        soil: SoilLayerModel, electrode_depth_m: float
    ) -> float:
        """
        Calculates apparent soil resistivity for two-layer stratification using reflection coefficient k.
        """
        _validate_soil_layer_model(soil)
        depth = _check_positive_finite_float("electrode_depth_m", electrode_depth_m)

        if not soil.is_two_layer:
            return float(soil.rho_upper_ohm_m)

        assert soil.rho_lower_ohm_m is not None and soil.h_upper_m is not None
        rho1 = float(soil.rho_upper_ohm_m)
        rho2 = float(soil.rho_lower_ohm_m)
        h = float(soil.h_upper_m)
        rho_ratio = rho1 / rho2
        if not math.isfinite(rho_ratio) or rho_ratio <= 0.0:
            raise ValueError(
                f"Soil resistivity ratio rho_upper_ohm_m / rho_lower_ohm_m is not valid: {rho_ratio!r}."
            )

        # Reflection factor k = (rho2 - rho1) / (rho2 + rho1)
        k = (rho2 - rho1) / (rho2 + rho1)

        # Sunde integration approximation for shallow electrodes
        ratio = depth / h
        apparent_rho = rho1 * (1.0 + k * (1.0 - np.exp(-1.8 * ratio)))
        return float(apparent_rho)

    @staticmethod
    def get_iec_min_length_l1(lps_class: str, rho: float) -> float:
        """
        IEC 62305-3:2024 Clause 5.4.2.2, Figure 5 (p. 34) minimum length l1 (m)
        as a function of soil resistivity rho (ohm.m) and LPS Class.
        Graphical reading of Figure 5; tolerance ±0.5 m.
        - Figure 5 NOTE 1: Classes III and IV are independent of soil resistivity (5.0 m).
        - Figure 5 NOTE 4: Figure 5 is defined for 0 < rho <= 3000 ohm.m (no extrapolation).
        """
        if not isinstance(lps_class, str) or lps_class not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        if isinstance(rho, bool) or not isinstance(rho, (int, float, np.number)):
            raise ValueError(
                f"Soil resistivity rho must be a finite positive number, got {rho!r}."
            )
        rho_f = float(rho)
        if not np.isfinite(rho_f) or rho_f <= 0.0:
            raise ValueError(
                f"Soil resistivity rho must be finite and > 0 ohm.m, got {rho!r}."
            )
        if rho_f > 3000.0:
            raise ValueError(
                f"Soil resistivity rho={rho_f} ohm.m exceeds IEC 62305-3:2024 Figure 5 domain "
                f"(rho <= 3000 ohm.m; see 5.4.2.2 NOTE 4)."
            )
        if lps_class == "I":
            return 5.0 if rho_f <= 500.0 else float(0.03 * rho_f - 10.0)
        if lps_class == "II":
            return (
                5.0
                if rho_f <= 800.0
                else float(5.0 + (rho_f - 800.0) * (43.5 / 2200.0))
            )
        return 5.0

    def evaluate_earthing_system(
        self, inp: EarthingAssessmentInput
    ) -> EarthingAssessmentResult:
        _validate_earthing_input(inp)
        rho = self.calculate_apparent_resistivity(inp.soil, inp.burial_depth_m)
        l1 = self.get_iec_min_length_l1(inp.lps_class, rho)
        warnings: List[str] = []

        r_cond = float(inp.conductor_diameter_m) / 2.0
        h_depth = float(inp.burial_depth_m)

        if inp.electrode_type == "type_b_ring":
            assert inp.ring_radius_m is not None
            r_ring = float(inp.ring_radius_m)
            effective_len = float(2.0 * np.pi * r_ring)
            # Sunde equivalent-radius form (approximate; primary-source confirmation pending):
            # R_ring = (rho / (pi^2 * D)) * ln(4 * D / sqrt(2 * a * h))
            d_ring = 2.0 * r_ring
            equiv_radius = np.sqrt(2.0 * r_cond * h_depth)
            r_dc = float(
                (rho / ((np.pi ** 2) * d_ring))
                * np.log((4.0 * d_ring) / equiv_radius)
            )
            trace = f"Type B Ring (R_ring={r_ring}m, depth={h_depth}m, {RING_METHOD_LABEL}): R_stat={r_dc:.4f} ohm"
            warnings.append(RING_METHOD_LABEL)

        elif inp.electrode_type == "type_a_vertical":
            assert (
                inp.vertical_rod_length_m is not None
                and inp.vertical_rod_count is not None
                and inp.vertical_rod_spacing_m is not None
            )
            l_rod = float(inp.vertical_rod_length_m)
            n_rods = int(inp.vertical_rod_count)
            s_spacing = float(inp.vertical_rod_spacing_m)
            effective_len = float(n_rods * l_rod)

            r_dc = array_resistance_identical_rods(rho, l_rod, r_cond, n_rods, s_spacing)
            method_label = (
                MULTI_ROD_METHOD_LABEL if n_rods > 1 else "Dwight + Mutual Coupling"
            )
            trace = f"Type A Vertical ({n_rods} rods x {l_rod}m, spacing={s_spacing}m, {method_label}): R_stat={r_dc:.2f} ohm"

        elif inp.electrode_type == "type_a_horizontal":
            if (
                inp.strip_length_m is None
                or isinstance(inp.strip_length_m, bool)
                or not np.isfinite(inp.strip_length_m)
                or inp.strip_length_m <= 0.0
            ):
                raise ValueError(
                    f"strip_length_m must be provided and > 0 for electrode_type='type_a_horizontal', got {inp.strip_length_m!r}."
                )
            l_strip = float(inp.strip_length_m)
            effective_len = float(l_strip)
            # Sunde form. Exactly equivalent to the round-conductor form
            #   R = rho/(2*pi*L) * [ln(2L^2/(d*h)) - (2 - ln 2)],  d = conductor_diameter_m.
            # Flat-strip (width-based, k = 1) model is NOT implemented.
            equiv_radius = np.sqrt(2.0 * r_cond * h_depth)
            r_dc = float(
                (rho / (np.pi * l_strip))
                * (np.log(2.0 * l_strip / equiv_radius) - 1.0)
            )
            trace = f"Type A Horizontal Strip (L={l_strip}m, depth={h_depth}m, Sunde formula): R_stat={r_dc:.2f} ohm"

        elif inp.electrode_type == "foundation":
            assert (
                inp.foundation_perimeter_m is not None
                and inp.foundation_area_m2 is not None
            )
            perim = float(inp.foundation_perimeter_m)
            area = float(inp.foundation_area_m2)
            effective_len = float(perim)
            # Laurent & Nieman formulation for foundation mesh:
            # R = rho / (4 * r_equiv) + rho / perim where r_equiv = sqrt(Area / pi)
            r_equiv = np.sqrt(area / np.pi)
            r_dc = float((rho / (4.0 * r_equiv)) + (rho / perim))
            trace = f"Foundation Mesh (Perim={perim}m, Area={area}m2, Laurent formula): R_stat={r_dc:.2f} ohm"

        else:
            raise ValueError(
                f"Unknown electrode_type {inp.electrode_type!r}; expected one of {_VALID_ELECTRODE_TYPES}."
            )

        # High-Current Impulse Impedance Reduction (Soil Ionization under Lightning Impulse)
        # Corson / Bellaschi soil ionization model: Z_p = R_dc / sqrt(1 + I / I_g)
        # Critical ionization current I_g = (E_c * rho) / (2 * pi * R_dc^2) where E_c ~ 300-400 kV/m
        e_critical = 300e3  # V/m dielectric breakdown of soil
        peak_ka = (
            float(inp.peak_impulse_current_ka)
            if inp.peak_impulse_current_ka is not None
            else LPL_FIRST_POSITIVE_PEAK_CURRENT_KA[inp.lps_class]
        )
        i_peak = peak_ka * 1e3
        i_critical = max(
            100.0, (e_critical * rho) / (2.0 * np.pi * max(0.1, r_dc ** 2))
        )

        # Impulse coefficient A_i = Z_p / R_dc
        impulse_factor = float(1.0 / np.sqrt(1.0 + (i_peak / i_critical)))
        z_impulse = float(r_dc * impulse_factor)

        meets_l1 = effective_len >= l1
        meets_10 = r_dc <= 10.0

        if not meets_l1:
            warnings.append(
                f"Electrode effective length ({effective_len:.1f}m) is below mandatory IEC 62305-3 l1 requirement ({l1:.1f}m)"
            )
        if not meets_10:
            warnings.append(
                f"Stationary resistance ({r_dc:.2f} ohm) exceeds standard 10 ohm recommendation"
            )

        status = (
            "PASS"
            if (meets_l1 and meets_10)
            else ("WARNING" if meets_l1 else "NON_COMPLIANT")
        )
        r_stat_out = (
            float(r_dc)
            if inp.electrode_type in ("type_b_ring", "type_a_horizontal")
            else round(float(r_dc), 2)
        )

        return EarthingAssessmentResult(
            lps_class=inp.lps_class,
            effective_soil_resistivity_ohm_m=round(float(rho), 2),
            minimum_length_l1_m=round(float(l1), 2),
            actual_effective_length_m=round(float(effective_len), 2),
            stationary_resistance_r_ohm=r_stat_out,
            impulse_impedance_z_ohm=round(float(z_impulse), 2),
            impulse_efficiency_factor=round(float(impulse_factor), 3),
            meets_iec_l1_requirement=meets_l1,
            meets_recommended_10_ohm=meets_10,
            status=status,
            method_details=trace,
            warnings=warnings,
        )
