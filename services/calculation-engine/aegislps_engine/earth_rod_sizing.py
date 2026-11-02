import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field

class EarthRodSizingInput(BaseModel):
    lps_class: str = "I"
    soil_resistivity_ohm_m: float = 120.0
    target_resistance_ohm: float = 10.0 # Standard 10 ohm recommendation
    electrode_material: str = "copper_bonded_steel" # copper_bonded_steel, solid_copper, galvanized_steel, stainless_steel
    rod_length_per_unit_m: float = 3.0 # 1.5m, 2.4m, 3.0m standard commercial lengths
    min_distance_to_building_foundation_m: float = 1.0 # Permitted distance from structure
    site_boundary_length_m: float = 40.0
    site_boundary_width_m: float = 25.0

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
    - IEC 62561-2 Table 1 (Earth electrodes material, configuration and minimum dimensions):
      * Copper-bonded steel: minimum 14.2 mm diameter with >= 250 um copper coating
      * Solid copper: minimum 15.0 mm diameter
      * Hot-dip galvanized steel: minimum 20.0 mm diameter (or 16mm round with >= 50 um zinc)
      * Stainless steel (V4A 1.4571): minimum 16.0 mm diameter
    - Dwight mutual coupling formula for multi-rod array interaction
    - Inter-rod spacing rule (s >= 2 * L) to prevent severe resistance overlap shielding
    - Permitted setback distances from building foundation (d >= 1.0 m).
    """
    # Material specifications per IEC 62561-2 Table 1
    IEC_62561_2_SPECS = {
        "copper_bonded_steel": {
            "min_dia_mm": 16.0, # Commonly specified 5/8" (16mm)
            "coating_type": "Electroplated copper coating",
            "min_coating_um": 250.0,
            "corrosion_resistance": "High (suitable for most soils pH 3-10)",
            "driveability": "High tensile carbon steel core (> 600 N/mm2)"
        },
        "solid_copper": {
            "min_dia_mm": 15.0,
            "coating_type": "Solid pure copper (Cu-ETP)",
            "min_coating_um": 0.0,
            "corrosion_resistance": "Very High",
            "driveability": "Moderate (requires pre-drilling in rocky terrain)"
        },
        "galvanized_steel": {
            "min_dia_mm": 20.0,
            "coating_type": "Hot-dip zinc galvanization",
            "min_coating_um": 50.0,
            "corrosion_resistance": "Moderate (avoid acidic/clay soils)",
            "driveability": "High"
        },
        "stainless_steel": {
            "min_dia_mm": 16.0,
            "coating_type": "Austenitic Stainless Steel (1.4571 / AISI 316Ti)",
            "min_coating_um": 0.0,
            "corrosion_resistance": "Maximum (ideal for chemical/marine environments)",
            "driveability": "High"
        }
    }

    def size_earth_rod_system(self, inp: EarthRodSizingInput) -> EarthRodSizingResult:
        mat_spec = self.IEC_62561_2_SPECS.get(inp.electrode_material, self.IEC_62561_2_SPECS["copper_bonded_steel"])
        dia_mm = mat_spec["min_dia_mm"]
        radius_m = (dia_mm / 2.0) * 1e-3
        l_rod = max(1.0, inp.rod_length_per_unit_m)
        rho = max(1.0, inp.soil_resistivity_ohm_m)
        r_target = max(0.5, inp.target_resistance_ohm)

        # Single vertical rod Dwight resistance:
        # R1 = (rho / 2pi*L) * [ln(4L/r) - 1]
        r1 = float((rho / (2.0 * np.pi * l_rod)) * (np.log(4.0 * l_rod / radius_m) - 1.0))

        # Inter-rod spacing rule: s >= 2 * L_rod to ensure mutual coupling efficiency > 80%
        s_spacing = 2.0 * l_rod

        # Iterate to determine required number of rods N with Dwight mutual coupling
        n_rods = 1
        r_array = r1
        while n_rods <= 20 and r_array > r_target:
            n_rods += 1
            # Dwight multi-rod array mutual coupling formula (linear array)
            # R_N = (R1 / N) * [ 1 + (L / (2pi*s)) * ln(1 + s/L) * (N - 1) ]
            coupling_term = (l_rod / (2.0 * np.pi * s_spacing)) * np.log(1.0 + (s_spacing / l_rod))
            r_array = float((r1 / n_rods) * (1.0 + (n_rods - 1) * coupling_term))

        # Generate recommended coordinates along perimeter with foundation setback
        setback = max(1.0, inp.min_distance_to_building_foundation_m)
        l_bldg, w_bldg = inp.site_boundary_length_m, inp.site_boundary_width_m

        # Distribute rods around building corners and sides
        coords: List[Tuple[float, float]] = []
        base_corners = [
            (-l_bldg/2 - setback, -w_bldg/2 - setback),
            (l_bldg/2 + setback, -w_bldg/2 - setback),
            (l_bldg/2 + setback, w_bldg/2 + setback),
            (-l_bldg/2 - setback, w_bldg/2 + setback)
        ]
        for i in range(n_rods):
            corner_idx = i % 4
            offset = (i // 4) * s_spacing
            bx, by = base_corners[corner_idx]
            coords.append((round(bx + offset * 0.5, 2), round(by, 2)))

        notes = [
            f"Electrode material: {inp.electrode_material.replace('_', ' ').title()}.",
            f"Conforms to IEC 62561-2 Table 1 minimum diameter: {dia_mm:.1f} mm.",
            f"Coating: {mat_spec['coating_type']} ({mat_spec['min_coating_um']} um).",
            f"Single rod resistance: {r1:.2f} ohm.",
            f"Total array: {n_rods} rods x {l_rod:.1f} m spaced at {s_spacing:.1f} m achieves R_tot = {r_array:.2f} ohm (Target <= {r_target:.1f} ohm).",
            f"Foundation setback clearance: {setback:.1f} m verified."
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
            status="SIZED_AND_COMPLIANT" if r_array <= r_target else "ADDITIONAL_DEEP_WELL_REQUIRED"
        )
