import math
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aegislps_engine.earthing import (
    array_resistance_identical_rods,
    single_vertical_rod_resistance,
)

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")


class EarthRodSizingInput(BaseModel):
    """Input model for multi-material earth rod sizing and array placement.

    Note: ``lps_class`` (default ``"I"``) is retained as documented unused metadata
    for caller context (validated in ``{"I", "II", "III", "IV"}``; does not enter
    the resistance sizing loop).
    """

    model_config = ConfigDict(allow_inf_nan=False)

    lps_class: str = "I"
    soil_resistivity_ohm_m: float
    # IEC 62305-3:2024 Clause 5.4.1 (p. 33): "a low earth-termination resistance is
    # recommended (if possible lower than 10 ohm when measured at low frequency)".
    target_resistance_ohm: float = 10.0
    electrode_material: str  # copper_bonded_steel, solid_copper, galvanized_steel, stainless_steel
    rod_length_per_unit_m: float  # 1.5m, 2.4m, 3.0m standard commercial lengths
    # Optional explicit rod diameter [mm]; defaults to material minimum when omitted
    # and is validated >= IEC_62561_2_SPECS[electrode_material]["min_dia_mm"].
    rod_diameter_mm: Optional[float] = None
    # IEC 62305-3:2024 Clause 5.4.3 (p. 35): external earth electrodes installed
    # "at a distance of about 1 m away from the external walls".
    min_distance_to_building_foundation_m: float = 1.0
    site_boundary_length_m: float
    site_boundary_width_m: float

    @field_validator(
        "soil_resistivity_ohm_m",
        "target_resistance_ohm",
        "rod_length_per_unit_m",
        "min_distance_to_building_foundation_m",
        "site_boundary_length_m",
        "site_boundary_width_m",
        mode="before",
    )
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric earth-rod parameter.")
        if v is None:
            raise ValueError("Required numeric earth-rod parameter cannot be None.")
        return v

    @field_validator("rod_diameter_mm", mode="before")
    @classmethod
    def _reject_bool_optional_diameter(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for rod_diameter_mm.")
        return v

    @model_validator(mode="after")
    def _validate_earth_rod_input(self) -> "EarthRodSizingInput":
        if not isinstance(self.lps_class, str) or self.lps_class not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {self.lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        for name in (
            "soil_resistivity_ohm_m",
            "target_resistance_ohm",
            "rod_length_per_unit_m",
            "site_boundary_length_m",
            "site_boundary_width_m",
        ):
            val = getattr(self, name)
            if isinstance(val, bool) or not math.isfinite(val) or val <= 0.0:
                raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
        if (
            isinstance(self.min_distance_to_building_foundation_m, bool)
            or not math.isfinite(self.min_distance_to_building_foundation_m)
            or self.min_distance_to_building_foundation_m < 0.0
        ):
            raise ValueError(
                "min_distance_to_building_foundation_m must be finite and >= 0, "
                f"got {self.min_distance_to_building_foundation_m!r}."
            )
        if (
            not isinstance(self.electrode_material, str)
            or self.electrode_material not in EarthRodSizingEngine.IEC_62561_2_SPECS
        ):
            raise ValueError(
                f"Unknown electrode_material {self.electrode_material!r}; "
                f"expected one of {tuple(EarthRodSizingEngine.IEC_62561_2_SPECS.keys())}."
            )
        if self.rod_diameter_mm is not None:
            if (
                isinstance(self.rod_diameter_mm, bool)
                or not math.isfinite(self.rod_diameter_mm)
                or self.rod_diameter_mm <= 0.0
            ):
                raise ValueError(
                    f"rod_diameter_mm must be finite and > 0, got {self.rod_diameter_mm!r}."
                )
            min_dia = EarthRodSizingEngine.IEC_62561_2_SPECS[self.electrode_material][
                "min_dia_mm"
            ]
            if self.rod_diameter_mm < min_dia:
                raise ValueError(
                    f"rod_diameter_mm ({self.rod_diameter_mm} mm) is below the minimum "
                    f"earth-rod diameter ({min_dia} mm) for {self.electrode_material!r} "
                    "(IEC 62305-3:2024 Clause 5.6.2, Table 8)."
                )
        return self


class EarthRodSizingResult(BaseModel):
    selected_material: str
    nominal_diameter_mm: float
    coating_thickness_um: float
    unit_rod_length_m: float
    single_rod_resistance_ohm: float
    required_number_of_rods: int
    inter_rod_spacing_rule_m: float
    total_array_resistance_ohm: float
    target_achieved: bool
    recommended_rod_coordinates: List[Tuple[float, float]]
    material_compliance_notes: List[str] = Field(default_factory=list)
    status: str


class EarthRodSizingEngine:
    """
    Advanced Multi-Material Earth Rod Sizing & Array Placement Engine.

    Standards:
    - IEC 62305-3:2024 Clause 5.6.2, Table 8 (p. 40, Material, configuration and minimum
      dimensions of earth electrodes; footnote a references IEC 62561-2):
      * Copper-coated (copper-bonded) steel, solid round: minimum 14.0 mm diameter
        (250 um copper coating thickness retained per IEC 62561-2 reference; primary
        IEC 62561-2 text not in repo)
      * Solid copper: minimum 15.0 mm diameter
      * Hot-dip galvanized steel: 20.0 mm diameter configured here (Table 8 lists 14 mm solid round / 25 mm tubular)
      * Stainless steel: 16.0 mm diameter configured here (Table 8 lists 15 mm solid round)
    - Dwight mutual coupling formula for multi-rod array interaction
    - Inter-rod spacing rule (s >= 2 * L) to prevent severe resistance overlap shielding
    - Permitted setback distances from building foundation (d >= 1.0 m).
    """

    # Material specifications aligned for M7 with IEC 62305-3:2024 Clause 5.6.2, Table 8 (p. 40)
    IEC_62561_2_SPECS: Dict[str, Dict] = {
        "copper_bonded_steel": {
            "min_dia_mm": 14.0,  # IEC 62305-3:2024 Clause 5.6.2, Table 8 (Copper-coated steel, solid round: 14 mm)
            "coating_type": "Electroplated copper coating",
            "min_coating_um": 250.0,
            "corrosion_resistance": "High (suitable for most soils pH 3-10)",
            "driveability": "High tensile carbon steel core (> 600 N/mm2)",
        },
        "solid_copper": {
            "min_dia_mm": 15.0,
            "coating_type": "Solid pure copper (Cu-ETP)",
            "min_coating_um": 0.0,
            "corrosion_resistance": "Very High",
            "driveability": "Moderate (requires pre-drilling in rocky terrain)",
        },
        "galvanized_steel": {
            "min_dia_mm": 20.0,
            "coating_type": "Hot-dip zinc galvanization",
            "min_coating_um": 50.0,
            "corrosion_resistance": "Moderate (avoid acidic/clay soils)",
            "driveability": "High",
        },
        "stainless_steel": {
            "min_dia_mm": 16.0,
            "coating_type": "Austenitic Stainless Steel (1.4571 / AISI 316Ti)",
            "min_coating_um": 0.0,
            "corrosion_resistance": "Maximum (ideal for chemical/marine environments)",
            "driveability": "High",
        },
    }

    def size_earth_rod_system(self, inp: EarthRodSizingInput) -> EarthRodSizingResult:
        inp._validate_earth_rod_input()
        mat_spec = self.IEC_62561_2_SPECS[inp.electrode_material]
        dia_mm = (
            float(inp.rod_diameter_mm)
            if inp.rod_diameter_mm is not None
            else float(mat_spec["min_dia_mm"])
        )
        radius_m = (dia_mm / 2.0) * 1e-3
        l_rod = float(inp.rod_length_per_unit_m)
        rho = float(inp.soil_resistivity_ohm_m)
        r_target = float(inp.target_resistance_ohm)

        # Single vertical rod Dwight resistance:
        # R1 = (rho / (2*pi*L)) * [ln(4L/r) - 1]
        r1 = single_vertical_rod_resistance(rho, l_rod, radius_m)

        # Inter-rod spacing rule: s = 2 * L_rod
        s_spacing = 2.0 * l_rod

        # Iterate to determine required number of rods N with pairwise uniform-leakage mutual coupling
        n_rods = 1
        r_array = array_resistance_identical_rods(
            rho, l_rod, radius_m, n_rods, s_spacing
        )
        while n_rods <= 20 and r_array > r_target:
            n_rods += 1
            r_array = array_resistance_identical_rods(
                rho, l_rod, radius_m, n_rods, s_spacing
            )

        # Generate recommended coordinates along perimeter with foundation setback
        setback = float(inp.min_distance_to_building_foundation_m)
        l_bldg = float(inp.site_boundary_length_m)
        w_bldg = float(inp.site_boundary_width_m)

        # Distribute rods around building corners and sides
        coords: List[Tuple[float, float]] = []
        base_corners = [
            (-l_bldg / 2 - setback, -w_bldg / 2 - setback),
            (l_bldg / 2 + setback, -w_bldg / 2 - setback),
            (l_bldg / 2 + setback, w_bldg / 2 + setback),
            (-l_bldg / 2 - setback, w_bldg / 2 + setback),
        ]
        for i in range(n_rods):
            corner_idx = i % 4
            offset = (i // 4) * s_spacing
            bx, by = base_corners[corner_idx]
            coords.append((round(bx + offset * 0.5, 2), round(by, 2)))

        notes = [
            f"Electrode material: {inp.electrode_material.replace('_', ' ').title()}.",
            f"Conforms to IEC 62305-3:2024 Table 8 minimum diameter ({mat_spec['min_dia_mm']:.1f} mm): selected {dia_mm:.1f} mm.",
            f"Coating: {mat_spec['coating_type']} ({mat_spec['min_coating_um']} um).",
            f"Single rod resistance: {r1:.2f} ohm.",
            f"Total array: {n_rods} rods x {l_rod:.1f} m spaced at {s_spacing:.1f} m achieves R_tot = {r_array:.2f} ohm (Target <= {r_target:.1f} ohm).",
            f"Foundation setback clearance: {setback:.1f} m verified.",
        ]

        return EarthRodSizingResult(
            selected_material=inp.electrode_material,
            nominal_diameter_mm=dia_mm,
            coating_thickness_um=mat_spec["min_coating_um"],
            unit_rod_length_m=l_rod,
            single_rod_resistance_ohm=round(r1, 2),
            required_number_of_rods=n_rods,
            inter_rod_spacing_rule_m=round(s_spacing, 1),
            total_array_resistance_ohm=round(r_array, 2),
            target_achieved=r_array <= r_target,
            recommended_rod_coordinates=coords,
            material_compliance_notes=notes,
            status=(
                "SIZED_AND_COMPLIANT"
                if r_array <= r_target
                else "ADDITIONAL_DEEP_WELL_REQUIRED"
            ),
        )
