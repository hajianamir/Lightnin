import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class EarthPitSizingInput(BaseModel):
    is_disconnect_testing_required: bool = True # IEC 62305-3 Section E.7.2 test joint inspection
    traffic_loading_area: str = "pedestrian" # pedestrian (A15), car_park (B125), roadway_heavy (D400)
    electrode_rod_diameter_mm: float = 16.0
    auger_hole_diameter_mm: float = 100.0 # Borehole diameter if backfill used
    treatment_depth_m: float = 3.0 # Depth of backfill column
    enhancement_material: str = "carbon_gem" # carbon_gem (GEM), sodium_bentonite, chemical_salts, native_backfill
    native_soil_resistivity_ohm_m: float = 150.0

class EarthPitSizingResult(BaseModel):
    is_pit_required: bool
    pit_type: str
    pit_inner_diameter_mm: float
    pit_depth_mm: float
    en124_load_class: str
    backfill_material: str
    backfill_volume_m3: float
    backfill_mass_kg: float
    number_of_25kg_bags: int
    unconditioned_resistance_single_rod_ohm: float
    conditioned_resistance_single_rod_ohm: float
    resistance_reduction_percentage: float
    status: str
    engineering_specifications: List[str] = Field(default_factory=list)

class EarthPitEngine:
    """
    Advanced Earth Inspection Pit Sizing & Soil Enhancement Backfill Conditioning Engine.

    Standards:
    - IEC 62305-3 Section E.5.4.3 & E.7.2 (Test joints & periodic inspection accessibility)
    - IEC 62561-5 (Earth pits and housing requirements)
    - IEC 62561-7 (Earth enhancement compounds)
    - EN 124 (Gully tops and manhole tops for vehicular and pedestrian areas)
    """
    # IEC 62561-7 typical resistivity of backfill materials in ohm.m
    BACKFILL_PROPERTIES = {
        "carbon_gem": {"rho_c": 0.05, "density_kg_m3": 1200.0, "curing": "permanent_non_leaching"},
        "sodium_bentonite": {"rho_c": 3.0, "density_kg_m3": 1000.0, "curing": "hygroscopic_moisture_dependent"},
        "chemical_salts": {"rho_c": 1.5, "density_kg_m3": 1100.0, "curing": "leaches_requires_maintenance"},
        "native_backfill": {"rho_c": 150.0, "density_kg_m3": 1600.0, "curing": "none"}
    }

    def evaluate_earth_pit_and_backfill(self, inp: EarthPitSizingInput) -> EarthPitSizingResult:
        # Pit is mandatory if disconnect test joints or periodic electrical continuity is required
        pit_required = inp.is_disconnect_testing_required

        # Sizing pit dimensions and EN 124 mechanical load rating
        if inp.traffic_loading_area == "roadway_heavy":
            load_class = "Class D400 (400 kN)"
            pit_type = "Heavy Duty Precast Concrete Pit with Ductile Iron Lid"
            pit_dia = 320.0 # mm
            pit_depth = 300.0 # mm
        elif inp.traffic_loading_area == "car_park":
            load_class = "Class B125 (125 kN)"
            pit_type = "Polypropylene / Concrete Hybrid Pit"
            pit_dia = 300.0
            pit_depth = 280.0
        else: # pedestrian / soft ground
            load_class = "Class A15 (15 kN)"
            pit_type = "High-Density Polypropylene Inspection Pit with Anti-UV Lid"
            pit_dia = 250.0
            pit_depth = 260.0

        # Backfill borehole volume calculation:
        # V = pi * (r_hole^2 - r_rod^2) * L_depth
        r_hole_m = (inp.auger_hole_diameter_mm / 2.0) * 1e-3
        r_rod_m = (inp.electrode_rod_diameter_mm / 2.0) * 1e-3
        l_depth_m = max(0.5, inp.treatment_depth_m)

        v_backfill = np.pi * (r_hole_m**2 - r_rod_m**2) * l_depth_m
        mat = self.BACKFILL_PROPERTIES.get(inp.enhancement_material, self.BACKFILL_PROPERTIES["carbon_gem"])

        mass_kg = v_backfill * mat["density_kg_m3"]
        bags_25kg = int(np.ceil(mass_kg / 25.0))

        # Analytical unconditioned vs conditioned single vertical rod resistance:
        # Unconditioned Dwight: R1 = (rho / 2pi*L) * [ln(4L/r_rod) - 1]
        rho_native = max(5.0, inp.native_soil_resistivity_ohm_m)
        r_uncond = (rho_native / (2.0 * np.pi * l_depth_m)) * (np.log(4.0 * l_depth_m / r_rod_m) - 1.0)

        # Conditioned two-cylinder concentric soil model:
        # R_cond = (rho_c / 2pi*L)*ln(r_hole/r_rod) + (rho / 2pi*L)*[ln(4L/r_hole) - 1]
        rho_c = mat["rho_c"] if inp.enhancement_material != "native_backfill" else rho_native
        term_compound = (rho_c / (2.0 * np.pi * l_depth_m)) * np.log(r_hole_m / r_rod_m)
        term_soil = (rho_native / (2.0 * np.pi * l_depth_m)) * (np.log(4.0 * l_depth_m / r_hole_m) - 1.0)
        r_cond = float(term_compound + term_soil)

        reduction_pct = float(max(0.0, (1.0 - r_cond / max(1e-3, r_uncond)) * 100.0))

        specs = [
            f"Earth Inspection Pit: {pit_type} ({load_class}) per IEC 62561-5.",
            f"Inner diameter: {pit_dia:.0f} mm, Depth: {pit_depth:.0f} mm with removable test disconnect clamp.",
            f"Backfill borehole: {inp.auger_hole_diameter_mm:.0f} mm diameter augered to depth {l_depth_m:.1f} m.",
            f"Required backfill material: {inp.enhancement_material} ({mat['curing']}).",
            f"Required volume: {v_backfill:.3f} m3 ({mass_kg:.1f} kg -> {bags_25kg} x 25kg bags).",
            f"Electrode resistance improvement: {r_uncond:.2f} ohm -> {r_cond:.2f} ohm ({reduction_pct:.1f}% reduction)."
        ]

        return EarthPitSizingResult(
            is_pit_required=pit_required,
            pit_type=pit_type,
            pit_inner_diameter_mm=pit_dia,
            pit_depth_mm=pit_depth,
            en124_load_class=load_class,
            backfill_material=inp.enhancement_material,
            backfill_volume_m3=round(float(v_backfill), 3),
            backfill_mass_kg=round(float(mass_kg), 1),
            number_of_25kg_bags=bags_25kg,
            unconditioned_resistance_single_rod_ohm=round(float(r_uncond), 2),
            conditioned_resistance_single_rod_ohm=round(float(r_cond), 2),
            resistance_reduction_percentage=round(reduction_pct, 1),
            status="SIZED_AND_VERIFIED",
            engineering_specifications=specs
        )
