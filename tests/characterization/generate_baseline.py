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
from aegislps_engine.optimization import DesignOptimizationEngine, OptimizationInput
from aegislps_engine.peec_thermal import (
    ConductorThermalProperties,
    PEECThermalEngine,
    SkewSegment3D,
)
from aegislps_engine.pv_module import PVArraySpecification, PVEngineeringModule
from aegislps_engine.risk import RiskAssessmentInput, RiskManagementEngine
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_engine.spd_coordination import SPDCoordinationEngine, SPDEntry
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
    segments = [
        ConductorSegment(id=f"seg_{i + 1}", start_node_id="n1", end_node_id="n1")
        for i in range(num_segments)
    ]
    return Project(
        project_id="baseline-project",
        name="Baseline Project",
        lps_class="I",
        building=Building(height_m=15.0),
        nodes=[ConductorNode(id="n1", x=0.0, y=0.0, z=15.0)],
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
    earthing_engine = EarthingEngine()
    raw["earthing"] = {
        "type_b_ring": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                electrode_type="type_b_ring",
                ring_radius_m=15.0,
                soil=SoilLayerModel(rho_upper_ohm_m=100.0),
            )
        ),
        "type_a_vertical_1_rod": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                electrode_type="type_a_vertical",
                vertical_rod_count=1,
                vertical_rod_spacing_m=5.0,
                vertical_rod_length_m=3.0,
            )
        ),
        "type_a_vertical_4_rods": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                electrode_type="type_a_vertical",
                vertical_rod_count=4,
                vertical_rod_spacing_m=5.0,
                vertical_rod_length_m=3.0,
            )
        ),
        "type_a_horizontal": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(
                electrode_type="type_a_horizontal",
                ring_radius_m=15.0,
                strip_length_m=30.0,
            )
        ),
        "foundation": earthing_engine.evaluate_earthing_system(
            EarthingAssessmentInput(electrode_type="foundation")
        ),
    }

    # 3. TouchStepEngine
    ts_engine = TouchStepEngine()
    raw["touch_step"] = {
        "default": ts_engine.evaluate(
            TouchStepAssessmentInput(
                earth_potential_rise_v=10000.0,
                electrode_equivalent_radius_m=2.0,
            )
        ),
        "restricted_access_perimeter": ts_engine.evaluate(
            TouchStepAssessmentInput(
                has_restricted_access_perimeter=True,
                earth_potential_rise_v=10000.0,
                electrode_equivalent_radius_m=2.0,
            )
        ),
        "physical_insulation_barrier": ts_engine.evaluate(
            TouchStepAssessmentInput(
                has_physical_insulation_barrier=True,
                earth_potential_rise_v=10000.0,
                electrode_equivalent_radius_m=2.0,
            )
        ),
    }

    # 4. SPDCoordinationEngine
    raw["spd_coordination"] = SPDCoordinationEngine().evaluate_coordination(
        [
            SPDEntry(
                id="spd_1",
                spd_class="Type 1",
                technology="spark_gap",
                cable_length_to_downstream_m=5.0,
            ),
            SPDEntry(
                id="spd_2",
                spd_class="Type 2",
            ),
        ]
    )

    # 5. RiskManagementEngine
    raw["risk_management"] = RiskManagementEngine().evaluate_r1_risk(RiskAssessmentInput())

    # 6. ComprehensiveRisk2024Engine
    comp_risk_engine = ComprehensiveRisk2024Engine()
    raw["comprehensive_risk"] = {
        "default": comp_risk_engine.evaluate_risk(ComprehensiveRiskInput()),
        "incoming_line_transformer_unshielded": comp_risk_engine.evaluate_risk(
            ComprehensiveRiskInput(
                incoming_lines=[
                    IncomingServiceLine(transformer_present=True, shielded=False)
                ]
            )
        ),
        "incoming_line_no_transformer_shielded": comp_risk_engine.evaluate_risk(
            ComprehensiveRiskInput(
                incoming_lines=[
                    IncomingServiceLine(transformer_present=False, shielded=True)
                ]
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
            ShieldingGrid(mesh_width_w_m=5.0),
            InternalCableLoop(),
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

    # 10. MeshMethodEngine
    raw["mesh_method"] = MeshMethodEngine().validate_mesh_design(MeshMethodInput())

    # 11. EarthRodSizingEngine
    raw["earth_rod_sizing"] = EarthRodSizingEngine().size_earth_rod_system(
        EarthRodSizingInput()
    )

    # 12. EarthPitEngine
    raw["earth_pit"] = EarthPitEngine().evaluate_earth_pit_and_backfill(
        EarthPitSizingInput()
    )

    # 13. PVEngineeringModule
    raw["pv_module"] = PVEngineeringModule().evaluate_pv_installation(
        PVArraySpecification()
    )

    # 14. HVIConductorAssistant
    raw["hvi_conductor"] = HVIConductorAssistant().evaluate_hvi_selection(
        HVIConductorSelectionInput()
    )

    # 15. BOMAndLifecycleEngine
    raw["bom_lifecycle"] = BOMAndLifecycleEngine().generate_project_bom(
        "Test", "I", 30, 20, 15
    )

    # 16. PEECThermalEngine
    raw["peec_thermal"] = {
        "thermal_and_electrodynamic_stress": PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(
            ConductorThermalProperties(material="copper", cross_section_mm2=50.0), "I"
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
            {"id": "n1", "x": 0, "y": 0, "z": 10},
            {"id": "n2", "x": 0, "y": 0, "z": 0},
            {"id": "n3", "x": 10, "y": 0, "z": 0},
        ],
        [
            {"id": "s1", "start_node_id": "n1", "end_node_id": "n2"},
            {"id": "s2", "start_node_id": "n1", "end_node_id": "n3"},
        ],
    )
    raw["nodal_solver"] = nodal.calculate_current_sharing("n1", ["n2", "n3"])

    # 18. UncertaintyQuantificationEngine (scalar fields and histogram only; fixed seed=42)
    uq_res = UncertaintyQuantificationEngine().run_monte_carlo(
        UQSimulationConfig(random_seed=42)
    )
    raw["uq_engine"] = uq_res.model_dump(exclude={"raw_samples", "samples"})

    # 19. DesignOptimizationEngine (fixed seed=42)
    raw["design_optimization"] = DesignOptimizationEngine().optimize_air_terminations(
        OptimizationInput(random_seed=42)
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
