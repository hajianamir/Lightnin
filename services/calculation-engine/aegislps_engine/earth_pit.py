import math
import numpy as np
from typing import Dict, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_VALID_TRAFFIC_LOADING_AREAS = ("pedestrian", "car_park", "roadway_heavy")


class EarthPitSizingInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    # IEC 62305-3:2024 Clause 5.3.6 (p. 33): "At the connection of the earth termination,
    # a test joint should be fitted on each down conductor, except in the case of natural
    # down conductors combined with foundation earth electrodes."
    is_disconnect_testing_required: bool = True
    traffic_loading_area: str  # pedestrian (A15), car_park (B125), roadway_heavy (D400)
    electrode_rod_diameter_mm: float
    auger_hole_diameter_mm: float  # Borehole diameter if backfill used (> electrode_rod_diameter_mm)
    treatment_depth_m: float  # Depth of backfill column
    enhancement_material: str  # carbon_gem (GEM), sodium_bentonite, chemical_salts, native_backfill
    native_soil_resistivity_ohm_m: float

    @field_validator("is_disconnect_testing_required", mode="before")
    @classmethod
    def _require_strict_bool(cls, v):
        if not isinstance(v, bool):
            raise ValueError(
                f"is_disconnect_testing_required must be a strict boolean, got {v!r}."
            )
        return v

    @field_validator(
        "electrode_rod_diameter_mm",
        "auger_hole_diameter_mm",
        "treatment_depth_m",
        "native_soil_resistivity_ohm_m",
        mode="before",
    )
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric earth-pit parameter.")
        if v is None:
            raise ValueError("Required numeric earth-pit parameter cannot be None.")
        return v

    @model_validator(mode="after")
    def _validate_earth_pit_input(self) -> "EarthPitSizingInput":
        if not isinstance(self.is_disconnect_testing_required, bool):
            raise ValueError(
                f"is_disconnect_testing_required must be a strict boolean, got {self.is_disconnect_testing_required!r}."
            )
        if (
            not isinstance(self.traffic_loading_area, str)
            or self.traffic_loading_area not in _VALID_TRAFFIC_LOADING_AREAS
        ):
            raise ValueError(
                f"Unknown traffic_loading_area {self.traffic_loading_area!r}; "
                f"expected one of {_VALID_TRAFFIC_LOADING_AREAS}."
            )
        for name in (
            "electrode_rod_diameter_mm",
            "auger_hole_diameter_mm",
            "treatment_depth_m",
            "native_soil_resistivity_ohm_m",
        ):
            val = getattr(self, name)
            if isinstance(val, bool) or not math.isfinite(val) or val <= 0.0:
                raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
        if self.auger_hole_diameter_mm <= self.electrode_rod_diameter_mm:
            raise ValueError(
                f"auger_hole_diameter_mm ({self.auger_hole_diameter_mm}) must be > "
                f"electrode_rod_diameter_mm ({self.electrode_rod_diameter_mm})."
            )
        if (
            not isinstance(self.enhancement_material, str)
            or self.enhancement_material not in EarthPitEngine.BACKFILL_PROPERTIES
        ):
            raise ValueError(
                f"Unknown enhancement_material {self.enhancement_material!r}; "
                f"expected one of {tuple(EarthPitEngine.BACKFILL_PROPERTIES.keys())}."
            )
        return self


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
    rho_c_unsourced_assumption: bool
    rho_c_assumption_note: str
    status: str
    engineering_specifications: List[str] = Field(default_factory=list)


class EarthPitEngine:
    """
    Advanced Earth Inspection Pit Sizing & Soil Enhancement Backfill Conditioning Engine.

    Standards:
    - IEC 62305-3:2024 Clause 5.3.6 & Annex D.5.3.6 / D.7 (Test joints & periodic inspection accessibility)
    - IEC 62561-5 (Earth pits and housing requirements)
    - IEC 62561-7 (Earth enhancement compounds — test/qualification standard; does not supply the fixed rho_c values below)
    - EN 124 (Gully tops and manhole tops for vehicular and pedestrian areas)
    """

    # Step 6.1 (M6): None of the four rho_c values below has a primary or secondary
    # source in `packages/standards-data` or `docs/` (IEC 62561-7 text is not in the
    # repository). Each entry is explicitly flagged as an unsourced assumption.
    BACKFILL_PROPERTIES: Dict[str, Dict] = {
        "carbon_gem": {
            "rho_c": 0.05,  # Unsourced assumption (ohm.m); no source in standards-data or docs/ (M6)
            "rho_c_unsourced_assumption": True,
            "density_kg_m3": 1200.0,
            "curing": "permanent_non_leaching",
        },
        "sodium_bentonite": {
            "rho_c": 3.0,  # Unsourced assumption (ohm.m); no source in standards-data or docs/ (M6)
            "rho_c_unsourced_assumption": True,
            "density_kg_m3": 1000.0,
            "curing": "hygroscopic_moisture_dependent",
        },
        "chemical_salts": {
            "rho_c": 1.5,  # Unsourced assumption (ohm.m); no source in standards-data or docs/ (M6)
            "rho_c_unsourced_assumption": True,
            "density_kg_m3": 1100.0,
            "curing": "leaches_requires_maintenance",
        },
        "native_backfill": {
            "rho_c": 150.0,  # Unsourced assumption placeholder (ohm.m); evaluate_earth_pit_and_backfill uses native_soil_resistivity_ohm_m (M6)
            "rho_c_unsourced_assumption": True,
            "density_kg_m3": 1600.0,
            "curing": "none",
        },
    }

    def evaluate_earth_pit_and_backfill(
        self, inp: EarthPitSizingInput
    ) -> EarthPitSizingResult:
        inp._validate_earth_pit_input()

        # Pit is mandatory if disconnect test joints or periodic electrical continuity is required
        pit_required = inp.is_disconnect_testing_required

        # Sizing pit dimensions and EN 124 mechanical load rating
        if inp.traffic_loading_area == "roadway_heavy":
            load_class = "Class D400 (400 kN)"
            pit_type = "Heavy Duty Precast Concrete Pit with Ductile Iron Lid"
            pit_dia = 320.0  # mm
            pit_depth = 300.0  # mm
        elif inp.traffic_loading_area == "car_park":
            load_class = "Class B125 (125 kN)"
            pit_type = "Polypropylene / Concrete Hybrid Pit"
            pit_dia = 300.0
            pit_depth = 280.0
        elif inp.traffic_loading_area == "pedestrian":
            load_class = "Class A15 (15 kN)"
            pit_type = "High-Density Polypropylene Inspection Pit with Anti-UV Lid"
            pit_dia = 250.0
            pit_depth = 260.0
        else:
            raise ValueError(
                f"Unknown traffic_loading_area {inp.traffic_loading_area!r}; "
                f"expected one of {_VALID_TRAFFIC_LOADING_AREAS}."
            )

        # Backfill borehole volume calculation:
        # V = pi * (r_hole^2 - r_rod^2) * L_depth
        r_hole_m = (float(inp.auger_hole_diameter_mm) / 2.0) * 1e-3
        r_rod_m = (float(inp.electrode_rod_diameter_mm) / 2.0) * 1e-3
        l_depth_m = float(inp.treatment_depth_m)

        v_backfill = np.pi * (r_hole_m ** 2 - r_rod_m ** 2) * l_depth_m
        mat = self.BACKFILL_PROPERTIES[inp.enhancement_material]

        mass_kg = v_backfill * mat["density_kg_m3"]
        bags_25kg = int(np.ceil(mass_kg / 25.0))

        # Analytical unconditioned vs conditioned single vertical rod resistance:
        # Unconditioned Dwight: R1 = (rho / 2pi*L) * [ln(4L/r_rod) - 1]
        rho_native = float(inp.native_soil_resistivity_ohm_m)
        r_uncond = (rho_native / (2.0 * np.pi * l_depth_m)) * (
            np.log(4.0 * l_depth_m / r_rod_m) - 1.0
        )

        # Conditioned two-cylinder concentric soil model:
        # R_cond = (rho_c / 2pi*L)*ln(r_hole/r_rod) + (rho / 2pi*L)*[ln(4L/r_hole) - 1]
        rho_c = (
            mat["rho_c"]
            if inp.enhancement_material != "native_backfill"
            else rho_native
        )
        term_compound = (rho_c / (2.0 * np.pi * l_depth_m)) * np.log(r_hole_m / r_rod_m)
        term_soil = (rho_native / (2.0 * np.pi * l_depth_m)) * (
            np.log(4.0 * l_depth_m / r_hole_m) - 1.0
        )
        r_cond = float(term_compound + term_soil)

        reduction_pct = float(max(0.0, (1.0 - r_cond / max(1e-3, r_uncond)) * 100.0))

        specs = [
            f"Earth Inspection Pit: {pit_type} ({load_class}) per IEC 62561-5.",
            f"Inner diameter: {pit_dia:.0f} mm, Depth: {pit_depth:.0f} mm with removable test disconnect clamp.",
            f"Backfill borehole: {inp.auger_hole_diameter_mm:.0f} mm diameter augered to depth {l_depth_m:.1f} m.",
            f"Required backfill material: {inp.enhancement_material} ({mat['curing']}).",
            f"Required volume: {v_backfill:.3f} m3 ({mass_kg:.1f} kg -> {bags_25kg} x 25kg bags).",
            f"Electrode resistance improvement: {r_uncond:.2f} ohm -> {r_cond:.2f} ohm ({reduction_pct:.1f}% reduction).",
        ]

        if inp.enhancement_material == "native_backfill":
            rho_c_note = (
                "Unsourced assumption (M6): BACKFILL_PROPERTIES['native_backfill']['rho_c'] = "
                "150.0 ohm.m has no source in standards-data or docs/; calculation uses "
                f"caller native_soil_resistivity_ohm_m = {rho_native} ohm.m."
            )
        else:
            rho_c_note = (
                f"Unsourced assumption (M6): backfill resistivity rho_c = {mat['rho_c']} ohm.m "
                f"for '{inp.enhancement_material}' has no source in standards-data or docs/."
            )

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
            rho_c_unsourced_assumption=bool(mat["rho_c_unsourced_assumption"]),
            rho_c_assumption_note=rho_c_note,
            status="SIZED_AND_VERIFIED",
            engineering_specifications=specs,
        )
