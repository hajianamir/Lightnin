"""Characterization baseline generator (Step 0.1).

Records the CURRENT numerical outputs of each calculation and geometry engine
for fixed reference inputs and deterministic seeds. Write one JSON file per
engine into `tests/characterization/baseline/`.

Usage:
    python tests/characterization/generate_baseline.py
"""

from __future__ import annotations

import json
import math
from enum import Enum
from pathlib import Path
from typing import Any, Dict

import numpy as np

from aegislps_domain.models import (
    Building,
    ConductorNode,
    ConductorSegment,
    Project,
    SeparationPoint,
)
from aegislps_engine.bom_engine import BOMAndLifecycleEngine
from aegislps_engine.comprehensive_risk import (
    ComprehensiveRisk2024Engine,
    ComprehensiveRiskInput,
    IncomingServiceLine,
)
from aegislps_engine.earth_pit import EarthPitEngine, EarthPitSizingInput
from aegislps_engine.earth_rod_sizing import EarthRodSizingEngine, EarthRodSizingInput
from aegislps_engine.earthing import EarthingAssessmentInput, EarthingEngine, SoilLayerModel
from aegislps_engine.hvi_conductor import HVIConductorAssistant, HVIConductorSelectionInput
from aegislps_engine.lemp_engine import (
    InternalCableLoop,
    LEMPEngine,
    LEMPWaveformSpecification,
    ShieldingGrid,
)
from aegislps_engine.nodal import NodalCurrentSolver
from aegislps_engine.optimization import (
    DesignOptimizationEngine,
    OptimizationInput,
    ProtectedTarget,
)
from aegislps_engine.peec_thermal import (
    ConductorThermalProperties,
    PEECThermalEngine,
    SkewSegment3D,
)
from aegislps_engine.pv_module import PVArraySpecification, PVEngineeringModule
from aegislps_engine.risk import RiskAssessmentInput, RiskManagementEngine
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_engine.spd_coordination import (
    EquipmentWithstand,
    SPDCoordinationEngine,
    SPDEntry,
)
from aegislps_engine.touch_step import TouchStepAssessmentInput, TouchStepEngine
from aegislps_engine.uq_engine import UQSimulationConfig, UncertaintyQuantificationEngine
from aegislps_geometry.mesh_method import MeshMethodEngine, MeshMethodInput
from aegislps_geometry.mesh_rolling_sphere import (
    ArbitraryMeshRollingSphereEngine,
    MeshRollingSphereInput,
    TriangleFace,
)
from aegislps_geometry.protective_angle import ProtectiveAngleEngine
from aegislps_geometry.rolling_sphere import RollingSphereEngine

HERE = Path(__file__).resolve().parent
BASELINE_DIR = HERE / "baseline"


def serialize_value(obj: Any) -> Any:
    """Convert Pydantic models, numpy types, and containers to deterministic JSON-ready structures."""
    if hasattr(obj, "model_dump"):
        return serialize_value(obj.model_dump())
    if isinstance(obj, Enum):
        return serialize_value(obj.value)
    if isinstance(obj, dict):
        return {
            str(k): serialize_value(v)
            for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))
        }
    if isinstance(obj, np.ndarray):
        return [serialize_value(v) for v in obj.tolist()]
    if isinstance(obj, (list, tuple)):
        return [serialize_value(v) for v in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return str(val)
        if val == 0.0:
            return 0.0
        return float(f"{val:.9g}")
    return obj


def _build_separation_project(num_segments: int) -> Project:
    # Explicit former defaults for Step 2.7-B5 domain-model fields.
    segments = [
        ConductorSegment(
            id=f"seg_{i + 1}",
            start_node_id="n1",
            end_node_id="n1",
            material="copper",
            cross_section_mm2=50.0,
        )
        for i in range(num_segments)
    ]
    return Project(
        project_id="baseline-project",
        name="Baseline Project",
        lps_class="I",
        building=Building(
            length_m=20.0, width_m=10.0, height_m=15.0, roof_type="flat"
        ),
        nodes=[
            ConductorNode(
                id="n1", x=0.0, y=0.0, z=15.0, node_type="air_termination"
            )
        ],
        segments=segments,
        separation_points=[
            SeparationPoint(
                id="sp1",
                name="P1",
                x=0.0,
                y=0.0,
                z=15.0,
                associated_node_id="n1",
                insulation_medium="air",
                physical_distance_m=1.0,
            )
        ],
    )


def compute_all_snapshots() -> Dict[str, Any]:
    """Run all characterization cases and return one serialized structure per engine."""
    raw: Dict[str, Any] = {}

    # 1. SeparationDistanceEngine
    sep_engine = SeparationDistanceEngine()
    raw["separation_distance"] = {
        "segments_1": sep_engine.calculate_project(_build_separation_project(1)),
        "segments_2": sep_engine.calculate_project(_build_separation_project(2)),
    }

    # 2. EarthingEngine
    # Test fixture assumptions: explicit former defaults (peak_impulse_current_ka=100.0
    # passed explicitly per Step 2.7-B3 Decision 8; 1-rod Type A removed per Decision 1).
    earthing_engine = EarthingEngine()
    raw["earthing"] = {
        "type_b_ring": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                lps_class="I",
                soil=SoilLayerModel(rho_upper_ohm_m=100.0),
                electrode_type="type_b_ring",
                ring_radius_m=15.0,
                conductor_diameter_m=0.01,
                burial_depth_m=0.5,
                peak_impulse_current_ka=100.0,
            )
        ),
        "type_a_vertical_4_rods": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                lps_class="I",
                soil=SoilLayerModel(rho_upper_ohm_m=100.0),
                electrode_type="type_a_vertical",
                conductor_diameter_m=0.01,
                burial_depth_m=0.5,
                vertical_rod_count=4,
                vertical_rod_spacing_m=5.0,
                vertical_rod_length_m=3.0,
                peak_impulse_current_ka=100.0,
            )
        ),
        "type_a_horizontal": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                lps_class="I",
                soil=SoilLayerModel(rho_upper_ohm_m=100.0),
                electrode_type="type_a_horizontal",
                ring_radius_m=15.0,
                strip_length_m=30.0,
                conductor_diameter_m=0.01,
                burial_depth_m=0.5,
                peak_impulse_current_ka=100.0,
            )
        ),
        "foundation": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                lps_class="I",
                soil=SoilLayerModel(rho_upper_ohm_m=100.0),
                electrode_type="foundation",
                conductor_diameter_m=0.01,
                burial_depth_m=0.5,
                foundation_perimeter_m=80.0,
                foundation_area_m2=400.0,
                peak_impulse_current_ka=100.0,
            )
        ),
    }

    # 3. TouchStepEngine
    # Test fixture: explicit former defaults for characterization invariance.
    ts_engine = TouchStepEngine()
    ts_common = dict(
        lps_class="I",
        soil_resistivity_ohm_m=100.0,
        surface_layer_material="bare_soil",
        fault_duration_s=0.05,
        body_weight_kg=70.0,
        peak_impulse_current_ka=100.0,
        down_conductor_radius_m=0.005,
        earth_potential_rise_v=10000.0,
        electrode_equivalent_radius_m=2.0,
    )
    raw["touch_step"] = {
        "default": ts_engine.evaluate(TouchStepAssessmentInput(**ts_common)),
        "restricted_access_perimeter": ts_engine.evaluate(
            TouchStepAssessmentInput(
                **ts_common,
                has_restricted_access_perimeter=True,
            )
        ),
        "physical_insulation_barrier": ts_engine.evaluate(
            TouchStepAssessmentInput(
                **ts_common,
                has_physical_insulation_barrier=True,
            )
        ),
    }

    # 4. SPDCoordinationEngine
    # Test fixture: induced voltage not evaluated (lower bound) + explicit former defaults.
    raw["spd_coordination"] = SPDCoordinationEngine().evaluate_coordination(
        [
            SPDEntry(
                id="spd_1",
                spd_class="Type 1",
                technology="spark_gap",
                uc_volts=275.0,
                i_imp_ka=25.0,
                i_n_ka=20.0,
                up_kv=1.5,
                installed_lpz_boundary="LPZ 0B / 1",
                cable_length_to_downstream_m=5.0,
                lead_length_m=0.5,
            ),
            SPDEntry(
                id="spd_2",
                spd_class="Type 2",
                technology="spark_gap",
                uc_volts=275.0,
                i_imp_ka=25.0,
                i_n_ka=20.0,
                up_kv=1.5,
                installed_lpz_boundary="LPZ 0B / 1",
                cable_length_to_downstream_m=15.0,
                lead_length_m=0.5,
            ),
        ],
        EquipmentWithstand(category="Cat II", uw_kv=2.5, induced_voltage_kv=0.0),
    )

    # 5. RiskManagementEngine
    # Test fixture assumption: normal-loss structure with explicit former defaults. Not defaults.
    raw["risk_management"] = RiskManagementEngine().evaluate_r1_risk(
        RiskAssessmentInput(
            structure_length_m=30.0,
            structure_width_m=20.0,
            structure_height_m=15.0,
            ng_flashes_per_km2_year=2.5,
            environmental_cd=1.0,
            lps_class="I",
            loss_category="normal",
            fire_risk_rf=0.01,
            has_coordinated_spd=True,
            time_in_structure_hours_per_year=2190.0,
        )
    )

    # 6. ComprehensiveRisk2024Engine
    # Test fixture assumption: normal-loss structure with explicit former defaults. Not defaults.
    comp_risk_engine = ComprehensiveRisk2024Engine()
    comp_base = dict(
        structure_length_m=40.0,
        structure_width_m=25.0,
        structure_height_m=15.0,
        ng_flashes_per_km2_year=2.5,
        environmental_cd=1.0,
        lps_class="I",
        loss_category="normal",
        has_coordinated_spd=True,
        has_tws_early_warning=True,
        fire_risk_rf=0.01,
    )
    raw["comprehensive_risk"] = {
        "default": comp_risk_engine.evaluate_risk(
            ComprehensiveRiskInput(**comp_base)
        ),
        "incoming_line_transformer_unshielded": comp_risk_engine.evaluate_risk(
            ComprehensiveRiskInput(
                **comp_base,
                incoming_lines=[
                    IncomingServiceLine(transformer_present=True, shielded=False)
                ],
            )
        ),
        "incoming_line_no_transformer_shielded": comp_risk_engine.evaluate_risk(
            ComprehensiveRiskInput(
                **comp_base,
                incoming_lines=[
                    IncomingServiceLine(transformer_present=False, shielded=True)
                ],
            )
        ),
    }

    # 7. LEMPEngine
    lemp_engine = LEMPEngine()
    t_grid = np.linspace(0.0, 100.0, 1000)
    lemp_induction = {}
    heidler_1000pt = {}
    for stroke in ("first_positive_10_350", "subsequent_negative_025_100"):
        lemp_induction[stroke] = lemp_engine.calculate_lemp_induction(
            LEMPWaveformSpecification(
                stroke_type=stroke,
                peak_current_ka=100.0,
                t_end_us=100.0,
                num_time_steps=500,
            ),
            ShieldingGrid(
                is_shielded=True,
                mesh_width_w_m=5.0,
                rod_radius_m=0.005,
                material="copper_aluminium",
            ),
            InternalCableLoop(
                loop_area_m2=2.0,
                center_distance_from_down_conductor_m=3.0,
                equipment_withstand_uw_kv=1.5,
            ),
        )
        i_ka, di_dt_ka_per_us, max_di_dt = LEMPEngine.evaluate_heidler_current(
            t_grid, stroke, 100.0
        )
        heidler_1000pt[stroke] = {
            "current_ka": i_ka,
            "di_dt_ka_per_us": di_dt_ka_per_us,
            "max_di_dt_ka_per_us": max_di_dt,
        }
    raw["lemp"] = {
        "calculate_lemp_induction": lemp_induction,
        "evaluate_heidler_current_1000pt": heidler_1000pt,
    }

    # 8. ProtectiveAngleEngine
    pa_engine = ProtectiveAngleEngine()
    raw["protective_angle"] = {
        "protective_angles_deg": {
            lps_cls: {
                f"{h}m": ProtectiveAngleEngine.get_protective_angle_deg(lps_cls, float(h))
                for h in (2, 5, 10, 20, 45, 60)
                if h <= ProtectiveAngleEngine.MAX_HEIGHTS[lps_cls]
            }
            for lps_cls in ("I", "II", "III", "IV")
        },
        "cone_protected_object": pa_engine.check_object_in_cone(
            "I", 0.0, 0.0, 10.0, 0.0, 2.0, 0.0, 5.0
        ),
        "cone_exposed_object": pa_engine.check_object_in_cone(
            "I", 0.0, 0.0, 10.0, 0.0, 12.0, 0.0, 5.0
        ),
    }

    # 9. RollingSphereEngine
    rs_engine = RollingSphereEngine(20.0)
    raw["rolling_sphere"] = {
        "point_1_protected": rs_engine.check_surface_exposure(1.0, 0.0, 5.0, 0.0, 0.0, 10.0),
        "point_2_exposed_inside_radius": rs_engine.check_surface_exposure(
            10.0, 0.0, 9.0, 0.0, 0.0, 10.0
        ),
        "point_3_exposed_outside_radius": rs_engine.check_surface_exposure(
            25.0, 0.0, 2.0, 0.0, 0.0, 10.0
        ),
    }

    # 10. MeshMethodEngine (explicit former defaults)
    raw["mesh_method"] = MeshMethodEngine().validate_mesh_design(
        MeshMethodInput(
            lps_class="I",
            roof_length_m=30.0,
            roof_width_m=20.0,
            mesh_grid_dx_m=5.0,
            mesh_grid_dy_m=5.0,
            has_perimeter_conductor=True,
        )
    )

    # 11. EarthRodSizingEngine (explicit former defaults)
    raw["earth_rod_sizing"] = EarthRodSizingEngine().size_earth_rod_system(
        EarthRodSizingInput(
            lps_class="I",
            soil_resistivity_ohm_m=120.0,
            target_resistance_ohm=10.0,
            electrode_material="copper_bonded_steel",
            rod_length_per_unit_m=3.0,
            min_distance_to_building_foundation_m=1.0,
            site_boundary_length_m=40.0,
            site_boundary_width_m=25.0,
        )
    )

    # 12. EarthPitEngine (explicit former defaults)
    raw["earth_pit"] = EarthPitEngine().evaluate_earth_pit_and_backfill(
        EarthPitSizingInput(
            is_disconnect_testing_required=True,
            traffic_loading_area="pedestrian",
            electrode_rod_diameter_mm=16.0,
            auger_hole_diameter_mm=100.0,
            treatment_depth_m=3.0,
            enhancement_material="carbon_gem",
            native_soil_resistivity_ohm_m=150.0,
        )
    )

    # 13. PVEngineeringModule
    raw["pv_module"] = PVEngineeringModule().evaluate_pv_installation(
        PVArraySpecification(
            tilt_angle_deg=15.0,
            panel_count=24,
            array_length_m=12.0,
            array_width_m=6.0,
            metallic_frame_bonded=True,
            separation_to_lps_m=0.85,
            lps_class="I",
            down_conductor_length_l_m=15.0,
            insulation_medium="air",
        )
    )

    # 14. HVIConductorAssistant
    raw["hvi_conductor"] = HVIConductorAssistant().evaluate_hvi_selection(
        HVIConductorSelectionInput(
            lps_class="I",
            required_equivalent_separation_s_air_m=0.75,
            down_conductor_route_length_m=18.0,
            hvi_conductor_model="HVI_light_75",
            ambient_installation_type="outdoor_façade",
        )
    )

    # 15. BOMAndLifecycleEngine
    raw["bom_lifecycle"] = BOMAndLifecycleEngine().generate_project_bom(
        "Test", "I", 30, 20, 15, rod_count=4, down_conductor_count=4
    )

    # 16. PEECThermalEngine
    raw["peec_thermal"] = {
        "thermal_and_electrodynamic_stress": PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(
            ConductorThermalProperties(material="copper", cross_section_mm2=50.0),
            "I",
            0.1,
        ),
        "mutual_inductance_neumann_h": PEECThermalEngine.calculate_mutual_inductance_neumann(
            SkewSegment3D(start=(0.0, 0.0, 0.0), end=(5.0, 0.0, 0.0)),
            SkewSegment3D(start=(0.0, 0.5, 0.0), end=(5.0, 0.5, 0.0)),
        ),
    }

    # 17. NodalCurrentSolver (same 3-node topology as diagnostics.py)
    nodal = NodalCurrentSolver()
    nodal.build_network(
        [
            {"id": "n1", "x": 0, "y": 0, "z": 10, "node_type": "conductor"},
            {"id": "n2", "x": 0, "y": 0, "z": 0, "node_type": "conductor"},
            {"id": "n3", "x": 10, "y": 0, "z": 0, "node_type": "conductor"},
        ],
        [
            {
                "id": "s1",
                "start_node_id": "n1",
                "end_node_id": "n2",
                "cross_section_mm2": 50.0,
                "resistivity_ohm_m": 1.72e-8,
            },
            {
                "id": "s2",
                "start_node_id": "n1",
                "end_node_id": "n3",
                "cross_section_mm2": 50.0,
                "resistivity_ohm_m": 1.72e-8,
            },
        ],
    )
    raw["nodal_solver"] = nodal.calculate_current_sharing("n1", ["n2", "n3"], 100000.0)

    # 18. UncertaintyQuantificationEngine (scalar fields and histogram only; fixed seed=42)
    uq_res = UncertaintyQuantificationEngine().run_monte_carlo(
        UQSimulationConfig(
            num_samples=2000,
            random_seed=42,
            lps_class="I",
            target_clearance_d_m=1.0,
            nominal_path_length_m=15.0,
            nominal_soil_rho_ohm_m=100.0,
            ring_radius_m=15.0,
        )
    )
    raw["uq_engine"] = uq_res.model_dump(exclude={"raw_samples", "samples"})

    # 19. DesignOptimizationEngine (fixed seed=42)
    raw["design_optimization"] = DesignOptimizationEngine().optimize_air_terminations(
        OptimizationInput(
            lps_class="I",
            building_bounds=(-15.0, -10.0, 15.0, 10.0),
            roof_height_m=15.0,
            targets_to_protect=[
                ProtectedTarget(id="t1", x=-13.0, y=-8.0, z=15.0),
                ProtectedTarget(id="t2", x=13.0, y=-8.0, z=15.0),
                ProtectedTarget(id="t3", x=13.0, y=8.0, z=15.0),
                ProtectedTarget(id="t4", x=-13.0, y=8.0, z=15.0),
                ProtectedTarget(id="t5", x=0.0, y=0.0, z=16.5),
            ],
            target_sphere_radius_m=20.0,
            random_seed=42,
        )
    )

    # 20. ArbitraryMeshRollingSphereEngine
    tri_under = TriangleFace(
        id="tri_under",
        v0=(-1.0, -1.0, 2.0),
        v1=(1.0, -1.0, 2.0),
        v2=(0.0, 1.0, 2.0),
    )
    tri_far = TriangleFace(
        id="tri_far",
        v0=(50.0, 50.0, 2.0),
        v1=(52.0, 50.0, 2.0),
        v2=(51.0, 52.0, 2.0),
    )
    raw["mesh_rolling_sphere"] = ArbitraryMeshRollingSphereEngine().evaluate_mesh_protection(
        MeshRollingSphereInput(
            sphere_radius_m=20.0,
            triangles=[tri_under, tri_far],
            air_termination_tips=[(0.0, 0.0, 10.0)],
        )
    )

    return {engine_name: serialize_value(val) for engine_name, val in sorted(raw.items())}


def write_baseline(out_dir: Path = BASELINE_DIR) -> list[Path]:
    """Write one deterministic JSON file per engine into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshots = compute_all_snapshots()
    expected_files = {f"{engine_name}.json" for engine_name in snapshots}
    for existing in out_dir.glob("*.json"):
        if existing.name not in expected_files:
            existing.unlink()
    written: list[Path] = []
    for engine_name, payload in snapshots.items():
        path = out_dir / f"{engine_name}.json"
        with path.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        written.append(path)
    return written


if __name__ == "__main__":
    files = write_baseline()
    print(f"Wrote {len(files)} engine baseline files to {BASELINE_DIR}")
