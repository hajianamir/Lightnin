"""Step 2.7-B6 (H9): Validation, default-removal, clamp-removal, citation, and HTTP 422/200 tests
for BOM, PV, HVI, optimization, PEEC, nodal, IFC, and protective_angle Figure 1 NOTE 1 quote.
"""

from pathlib import Path
import math
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from aegislps_api.main import app
from aegislps_engine.bom_engine import BOMAndLifecycleEngine
from aegislps_engine.hvi_conductor import (
    HVIConductorAssistant,
    HVIConductorSelectionInput,
)
from aegislps_engine.ifc_importer import IFCImporter
from aegislps_engine.nodal import NodalCurrentSolver, NodeIn, SegmentIn
from aegislps_engine.optimization import (
    CandidateRod,
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
import aegislps_geometry.protective_angle as protective_angle_mod

client = TestClient(app)

VALID_IFC_BYTES = (
    b"ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\nENDSEC;\n"
    b"DATA;\n#10=IFCCARTESIANPOINT((0.,0.,0.));\n#11=IFCCARTESIANPOINT((28.,16.,12.));\nENDSEC;\n"
    b"END-ISO-10303-21;\n"
)


# ===========================================================================
# A. bom_engine.py (Rules A.1 - A.4)
# ===========================================================================


def test_a1_bom_requires_rod_and_down_conductor_counts_and_rejects_invalid():
    eng = BOMAndLifecycleEngine()
    with pytest.raises(TypeError):
        eng.generate_project_bom("Proj", "I", 30.0, 20.0, 15.0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        eng.generate_project_bom("Proj", "I", 30.0, 20.0, 15.0, rod_count=4)  # type: ignore[call-arg]

    for bad_count in (0, -2, True, False, 4.0, "4"):
        with pytest.raises(ValueError):
            eng.generate_project_bom(
                "Proj", "I", 30.0, 20.0, 15.0, bad_count, 4  # type: ignore[arg-type]
            )
        with pytest.raises(ValueError):
            eng.generate_project_bom(
                "Proj", "I", 30.0, 20.0, 15.0, 4, bad_count  # type: ignore[arg-type]
            )

    res = eng.generate_project_bom(
        "Proj", "I", 30.0, 20.0, 15.0, rod_count=6, down_conductor_count=8
    )
    rod_item = next(i for i in res.items if i.item_code == "AT-ROD-3M-CU")
    tj_item = next(i for i in res.items if i.item_code == "TEST-JOINT-CU")
    assert rod_item.quantity == 6.0
    assert tj_item.quantity == 8.0


def test_a2_bom_validates_lps_class():
    eng = BOMAndLifecycleEngine()
    for bad_cls in ("V", "i", "", "Class I", None, 1):
        with pytest.raises(ValueError):
            eng.generate_project_bom("Proj", bad_cls, 30.0, 20.0, 15.0, 4, 4)  # type: ignore[arg-type]

    for cls, exp_vis, exp_elec in (
        ("I", 1, 2),
        ("II", 1, 2),
        ("III", 2, 4),
        ("IV", 2, 4),
    ):
        res = eng.generate_project_bom("Proj", cls, 30.0, 20.0, 15.0, 4, 4)
        assert res.inspection_schedule[0].frequency_years == exp_vis
        assert res.inspection_schedule[1].frequency_years == exp_elec


def test_a3_bom_validates_dimensions_and_project_name():
    eng = BOMAndLifecycleEngine()
    for bad_dim in (0.0, -5.0, float("nan"), float("inf"), float("-inf"), True, False):
        with pytest.raises(ValueError):
            eng.generate_project_bom("Proj", "I", bad_dim, 20.0, 15.0, 4, 4)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            eng.generate_project_bom("Proj", "I", 30.0, bad_dim, 15.0, 4, 4)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            eng.generate_project_bom("Proj", "I", 30.0, 20.0, bad_dim, 4, 4)  # type: ignore[arg-type]

    for bad_name in ("", "   ", None, 123):
        with pytest.raises(ValueError):
            eng.generate_project_bom(bad_name, "I", 30.0, 20.0, 15.0, 4, 4)  # type: ignore[arg-type]

    res = eng.generate_project_bom("Substation A", "II", 25.0, 15.0, 10.0, 4, 4)
    assert res.total_components_count == 9


def test_a4_generate_bom_route_requires_all_fields():
    assert client.post("/api/v1/projects/generate-bom", json={}).status_code == 422
    assert (
        client.post(
            "/api/v1/projects/generate-bom",
            json={
                "project_name": "Test",
                "lps_class": "I",
                "building_length_m": 30.0,
                "building_width_m": 20.0,
                "building_height_m": 15.0,
            },
        ).status_code
        == 422
    )
    resp_ok = client.post(
        "/api/v1/projects/generate-bom",
        json={
            "project_name": "Test",
            "lps_class": "I",
            "building_length_m": 30.0,
            "building_width_m": 20.0,
            "building_height_m": 15.0,
            "rod_count": 4,
            "down_conductor_count": 4,
        },
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["total_components_count"] == 9


# ===========================================================================
# B. pv_module.py (Rules B.1 - B.4)
# ===========================================================================


def _valid_pv_kwargs(**overrides):
    base = {
        "tilt_angle_deg": 15.0,
        "panel_count": 24,
        "array_length_m": 12.0,
        "array_width_m": 6.0,
        "separation_to_lps_m": 0.85,
        "lps_class": "I",
        "down_conductor_length_l_m": 15.0,
        "insulation_medium": "air",
    }
    base.update(overrides)
    return base


def test_b1_pv_requires_all_physical_fields_and_checks_bonded_bool():
    with pytest.raises(ValidationError):
        PVArraySpecification()  # type: ignore[call-arg]

    for required_key in (
        "tilt_angle_deg",
        "panel_count",
        "array_length_m",
        "array_width_m",
        "separation_to_lps_m",
        "lps_class",
        "down_conductor_length_l_m",
        "insulation_medium",
    ):
        kw = _valid_pv_kwargs()
        kw.pop(required_key)
        with pytest.raises(ValidationError):
            PVArraySpecification(**kw)

    with pytest.raises(ValidationError):
        PVArraySpecification(**_valid_pv_kwargs(metallic_frame_bonded="yes"))

    spec = PVArraySpecification(**_valid_pv_kwargs())
    assert spec.metallic_frame_bonded is True


def test_b2_pv_numeric_domain_validation():
    for bad_tilt in (-0.1, 90.1, float("nan"), float("inf"), True, False):
        with pytest.raises(ValidationError):
            PVArraySpecification(**_valid_pv_kwargs(tilt_angle_deg=bad_tilt))
    assert PVArraySpecification(**_valid_pv_kwargs(tilt_angle_deg=0.0)).tilt_angle_deg == 0.0
    assert PVArraySpecification(**_valid_pv_kwargs(tilt_angle_deg=90.0)).tilt_angle_deg == 90.0

    for bad_panels in (0, -3, 24.0, True, False):
        with pytest.raises(ValidationError):
            PVArraySpecification(**_valid_pv_kwargs(panel_count=bad_panels))
    assert PVArraySpecification(**_valid_pv_kwargs(panel_count=1)).panel_count == 1

    for field in ("array_length_m", "array_width_m", "down_conductor_length_l_m"):
        for bad_val in (0.0, -1.0, float("nan"), float("inf"), True, False):
            with pytest.raises(ValidationError):
                PVArraySpecification(**_valid_pv_kwargs(**{field: bad_val}))

    for bad_sep in (-0.01, float("nan"), float("inf"), True, False):
        with pytest.raises(ValidationError):
            PVArraySpecification(**_valid_pv_kwargs(separation_to_lps_m=bad_sep))
    assert (
        PVArraySpecification(**_valid_pv_kwargs(separation_to_lps_m=0.0)).separation_to_lps_m
        == 0.0
    )


def test_b3_b4_pv_lps_class_and_insulation_medium_from_standards_repo():
    for bad_cls in ("V", "0", "", None):
        with pytest.raises(ValidationError):
            PVArraySpecification(**_valid_pv_kwargs(lps_class=bad_cls))

    for bad_med in ("oil", "vacuum", "", "AIR"):
        with pytest.raises(ValidationError):
            PVArraySpecification(**_valid_pv_kwargs(insulation_medium=bad_med))

    eng = PVEngineeringModule()
    res_air = eng.evaluate_pv_installation(PVArraySpecification(**_valid_pv_kwargs()))
    assert res_air.required_separation_s_m == 0.6
    assert res_air.actual_clearance_m == 0.85
    assert res_air.status == "ISOLATED_PASS"

    res_solid = eng.evaluate_pv_installation(
        PVArraySpecification(**_valid_pv_kwargs(insulation_medium="solid"))
    )
    assert res_solid.required_separation_s_m == 1.2

    res_standoff = eng.evaluate_pv_installation(
        PVArraySpecification(**_valid_pv_kwargs(insulation_medium="insulating_standoff"))
    )
    assert res_standoff.required_separation_s_m == round(0.08 * (0.5 / 0.7) * 15.0, 3)


# ===========================================================================
# C. hvi_conductor.py (Rules C.1 - C.4)
# ===========================================================================


def _valid_hvi_kwargs(**overrides):
    base = {
        "lps_class": "I",
        "required_equivalent_separation_s_air_m": 0.75,
        "down_conductor_route_length_m": 18.0,
        "hvi_conductor_model": "HVI_light_75",
        "ambient_installation_type": "outdoor_façade",
    }
    base.update(overrides)
    return base


def test_c1_c4_hvi_requires_all_fields_and_rejects_unknown_enums():
    with pytest.raises(ValidationError):
        HVIConductorSelectionInput()  # type: ignore[call-arg]

    for key in (
        "lps_class",
        "required_equivalent_separation_s_air_m",
        "down_conductor_route_length_m",
        "hvi_conductor_model",
        "ambient_installation_type",
    ):
        kw = _valid_hvi_kwargs()
        kw.pop(key)
        with pytest.raises(ValidationError):
            HVIConductorSelectionInput(**kw)

    for bad_cls in ("V", "i", ""):
        with pytest.raises(ValidationError):
            HVIConductorSelectionInput(**_valid_hvi_kwargs(lps_class=bad_cls))

    for bad_amb in ("indoor_riser", "buried", ""):
        with pytest.raises(ValidationError):
            HVIConductorSelectionInput(**_valid_hvi_kwargs(ambient_installation_type=bad_amb))

    for bad_model in ("HVI_unknown", "HVI_heavy_120", ""):
        with pytest.raises(ValidationError):
            HVIConductorSelectionInput(**_valid_hvi_kwargs(hvi_conductor_model=bad_model))

    assistant = HVIConductorAssistant()
    for amb in ("outdoor_façade", "outdoor_facade"):
        res = assistant.evaluate_hvi_selection(
            HVIConductorSelectionInput(**_valid_hvi_kwargs(ambient_installation_type=amb))
        )
        assert res.status == "COMPLIANT_APPROVED"


def test_c2_c3_hvi_positive_finite_lengths():
    for field in ("required_equivalent_separation_s_air_m", "down_conductor_route_length_m"):
        for bad_val in (0.0, -1.0, float("nan"), float("inf"), True, False):
            with pytest.raises(ValidationError):
                HVIConductorSelectionInput(**_valid_hvi_kwargs(**{field: bad_val}))

    res = HVIConductorAssistant().evaluate_hvi_selection(
        HVIConductorSelectionInput(
            **_valid_hvi_kwargs(
                hvi_conductor_model="HVI_standard_90",
                required_equivalent_separation_s_air_m=0.85,
                down_conductor_route_length_m=30.0,
            )
        )
    )
    assert res.is_adequate_insulation is True
    assert res.length_limit_exceeded is False


# ===========================================================================
# D. optimization.py (Rules D.1 - D.6)
# ===========================================================================


def _valid_opt_kwargs(**overrides):
    base = {
        "lps_class": "I",
        "building_bounds": (-15.0, -10.0, 15.0, 10.0),
        "roof_height_m": 15.0,
        "targets_to_protect": [ProtectedTarget(id="t1", x=0.0, y=0.0, z=15.0)],
    }
    base.update(overrides)
    return base


def test_d1_optimization_table2_radius_derivation_and_disagreement_rejection():
    expected_radii = {"I": 20.0, "II": 30.0, "III": 45.0, "IV": 60.0}
    for cls, r_m in expected_radii.items():
        inp = OptimizationInput(**_valid_opt_kwargs(lps_class=cls))
        assert inp.target_sphere_radius_m == r_m

        inp_agree = OptimizationInput(
            **_valid_opt_kwargs(lps_class=cls, target_sphere_radius_m=r_m)
        )
        assert inp_agree.target_sphere_radius_m == r_m

    with pytest.raises(ValidationError, match="Table 2"):
        OptimizationInput(
            **_valid_opt_kwargs(lps_class="I", target_sphere_radius_m=45.0)
        )

    with pytest.raises(ValidationError):
        OptimizationInput(**_valid_opt_kwargs(lps_class="V"))


def test_d2_d3_candidate_rod_and_protected_target_validation():
    for bad_cost in (-0.01, float("nan"), float("inf"), True, False):
        with pytest.raises(ValidationError):
            CandidateRod(id="r1", x=0.0, y=0.0, z=10.0, height_m=3.0, cost_units=bad_cost)
    rod_free = CandidateRod(id="r1", x=0.0, y=0.0, z=10.0, height_m=3.0, cost_units=0.0)
    assert rod_free.cost_units == 0.0

    for bad_tol in (0.0, -0.5, float("nan"), float("inf"), True, False):
        with pytest.raises(ValidationError):
            ProtectedTarget(id="t1", x=0.0, y=0.0, z=10.0, tolerance_radius_m=bad_tol)

    for bad_coord in (float("nan"), float("inf"), True, False):
        with pytest.raises(ValidationError):
            ProtectedTarget(id="t1", x=bad_coord, y=0.0, z=10.0)
        with pytest.raises(ValidationError):
            ProtectedTarget(id="t1", x=0.0, y=bad_coord, z=10.0)
        with pytest.raises(ValidationError):
            ProtectedTarget(id="t1", x=0.0, y=0.0, z=bad_coord)

    with pytest.raises(ValidationError):
        ProtectedTarget(id="t1", x=0.0, y=0.0, z=-0.1)

    t_ground = ProtectedTarget(id="t0", x=1.0, y=2.0, z=0.0)
    assert t_ground.z == 0.0
    assert t_ground.tolerance_radius_m == 0.5


def test_d4_d5_d6_optimization_bounds_targets_hyperparams_and_2r_ceiling():
    with pytest.raises(ValidationError):
        OptimizationInput()  # type: ignore[call-arg]

    with pytest.raises(ValidationError, match="targets_to_protect"):
        OptimizationInput(**_valid_opt_kwargs(targets_to_protect=[]))

    for bad_hp in (0, -1, True, False, 5.0):
        with pytest.raises(ValidationError):
            OptimizationInput(**_valid_opt_kwargs(max_candidate_rods=bad_hp))
        with pytest.raises(ValidationError):
            OptimizationInput(**_valid_opt_kwargs(iterations=bad_hp))

    for bad_seed in (-1, True, False, 1.5):
        with pytest.raises(ValidationError):
            OptimizationInput(**_valid_opt_kwargs(random_seed=bad_seed))

    assert OptimizationInput(**_valid_opt_kwargs(random_seed=0)).random_seed == 0

    # min_x >= max_x or min_y >= max_y
    with pytest.raises(ValidationError):
        OptimizationInput(**_valid_opt_kwargs(building_bounds=(10.0, -5.0, 10.0, 5.0)))
    with pytest.raises(ValidationError):
        OptimizationInput(**_valid_opt_kwargs(building_bounds=(-5.0, 5.0, 5.0, -5.0)))

    # roof_height_m + 5.0 > 2 * R (Class I: 2R = 40 m -> roof_height_m <= 35 m)
    with pytest.raises(ValidationError, match="2 \\* R"):
        OptimizationInput(**_valid_opt_kwargs(lps_class="I", roof_height_m=35.1))

    inp_boundary = OptimizationInput(
        **_valid_opt_kwargs(lps_class="I", roof_height_m=35.0, iterations=5)
    )
    res = DesignOptimizationEngine().optimize_air_terminations(inp_boundary)
    assert res.iterations_run == 5


# ===========================================================================
# E. peec_thermal.py (Rules E.1 - E.5)
# ===========================================================================


def test_e1_e2_e3_peec_material_aluminium_spelling_area_and_initial_temp():
    with pytest.raises(ValidationError):
        ConductorThermalProperties()  # type: ignore[call-arg]

    for bad_mat in ("gold", "brass", "", None):
        with pytest.raises(ValidationError):
            ConductorThermalProperties(material=bad_mat, cross_section_mm2=50.0)  # type: ignore[arg-type]

    for bad_area in (0.0, -10.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValidationError):
            ConductorThermalProperties(material="copper", cross_section_mm2=bad_area)  # type: ignore[arg-type]

    for bad_temp in (-273.15, -300.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValidationError):
            ConductorThermalProperties(
                material="copper",
                cross_section_mm2=50.0,
                initial_temperature_c=bad_temp,  # type: ignore[arg-type]
            )

    res_us = PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(
        ConductorThermalProperties(material="aluminum", cross_section_mm2=50.0),
        lps_class="II",
        parallel_conductor_spacing_m=0.2,
    )
    res_uk = PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(
        ConductorThermalProperties(material="aluminium", cross_section_mm2=50.0),
        lps_class="II",
        parallel_conductor_spacing_m=0.2,
    )
    assert res_us.adiabatic_temp_rise_delta_theta_k == res_uk.adiabatic_temp_rise_delta_theta_k
    assert res_us.final_temperature_c == res_uk.final_temperature_c
    assert res_us.peak_repulsive_force_n_per_m == res_uk.peak_repulsive_force_n_per_m


def test_e4_peec_requires_lps_class_and_spacing_without_001m_clamp():
    props = ConductorThermalProperties(material="copper", cross_section_mm2=50.0)
    with pytest.raises(TypeError):
        PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(props)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(props, "I")  # type: ignore[call-arg]

    for bad_cls in ("V", "0", ""):
        with pytest.raises(ValueError):
            PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(props, bad_cls, 0.1)

    for bad_d in (0.0, -0.05, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(
                props, "I", bad_d  # type: ignore[arg-type]
            )

    res_10mm = PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(props, "I", 0.01)
    res_5mm = PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(props, "I", 0.005)
    assert res_5mm.peak_repulsive_force_n_per_m == pytest.approx(
        2.0 * res_10mm.peak_repulsive_force_n_per_m, rel=1e-6
    )


def test_e5_peec_neumann_rejects_bad_gauss_points_nan_and_zero_length():
    seg_a = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(5.0, 0.0, 0.0))
    seg_b = SkewSegment3D(start=(0.0, 0.5, 0.0), end=(5.0, 0.5, 0.0))

    for bad_n in (0, -2, True, False, 4.5):
        with pytest.raises(ValueError):
            PEECThermalEngine.calculate_mutual_inductance_neumann(
                seg_a, seg_b, num_gauss_points=bad_n  # type: ignore[arg-type]
            )

    for bad_coord in (float("nan"), float("inf"), True):
        with pytest.raises(ValidationError):
            SkewSegment3D(start=(bad_coord, 0.0, 0.0), end=(1.0, 0.0, 0.0))  # type: ignore[arg-type]

    zero_seg = SkewSegment3D(start=(1.0, 1.0, 1.0), end=(1.0, 1.0, 1.0))
    with pytest.raises(ValueError, match="Zero-length"):
        PEECThermalEngine.calculate_mutual_inductance_neumann(zero_seg, seg_b)

    # Elementary closed-form double integral for L = 5 m parallel filaments at d = 0.5 m
    # (formula and source to be confirmed by owner):
    # M = 2e-7 * [5 * asinh(10) - sqrt(25.25) + 0.5] = 2.093235388186e-06 H.
    m_ij = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_a, seg_b, num_gauss_points=10
    )
    assert m_ij == pytest.approx(2.093235388186e-06, rel=1e-6)


def test_e6_peec_neumann_submillimeter_unclamped_and_nonconvergence_guard():
    """Step 3.4 (M2, A-d): sub-millimeter separations are unclamped; extreme proximity raises."""
    # Sub-millimeter parallel filaments (d = 0.2 mm < old 1e-3 m clamp, L = 0.1 m):
    # Converged 40-point / closed-form reference = 1.181950855797e-07 H
    # (old 1e-3 clamp under-predicted by -22.16%, returning 9.20065e-08 H).
    seg_sub_a = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(0.1, 0.0, 0.0))
    seg_sub_b = SkewSegment3D(start=(0.0, 2.0e-4, 0.0), end=(0.1, 2.0e-4, 0.0))
    m_sub = PEECThermalEngine.calculate_mutual_inductance_neumann(seg_sub_a, seg_sub_b)
    assert m_sub == pytest.approx(1.181950855797e-07, rel=1e-6)

    # Sub-millimeter parallel filaments (d = 0.5 mm < old 1e-3 m clamp, L = 1.0 m):
    # Converged 40-point / closed-form reference = 1.458909915520e-06 H
    seg_half_a = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(1.0, 0.0, 0.0))
    seg_half_b = SkewSegment3D(start=(0.0, 5.0e-4, 0.0), end=(1.0, 5.0e-4, 0.0))
    m_half = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_half_a, seg_half_b
    )
    assert m_half == pytest.approx(1.458909915520e-06, rel=1e-6)

    # Extreme aspect ratio (L = 10 m, d = 1e-7 m) exceeding panel budget raises ValueError
    # explicitly rather than silently clamping or returning an unconverged estimate.
    seg_ext_a = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(10.0, 0.0, 0.0))
    seg_ext_b = SkewSegment3D(start=(0.0, 1.0e-7, 0.0), end=(10.0, 1.0e-7, 0.0))
    with pytest.raises(ValueError, match="did not converge"):
        PEECThermalEngine.calculate_mutual_inductance_neumann(seg_ext_a, seg_ext_b)


# ===========================================================================
# F. nodal.py (Rules F.1 - F.6)
# ===========================================================================


def _two_branch_network():
    nodes = [
        NodeIn(id="n1", x=0.0, y=0.0, z=10.0, node_type="air_termination"),
        NodeIn(id="n2", x=0.0, y=0.0, z=0.0, node_type="earth_point"),
        NodeIn(id="n3", x=10.0, y=0.0, z=0.0, node_type="earth_point"),
    ]
    segments = [
        SegmentIn(
            id="s1",
            start_node_id="n1",
            end_node_id="n2",
            cross_section_mm2=50.0,
            resistivity_ohm_m=1.72e-8,
        ),
        SegmentIn(
            id="s2",
            start_node_id="n1",
            end_node_id="n3",
            cross_section_mm2=50.0,
            resistivity_ohm_m=1.72e-8,
        ),
    ]
    return nodes, segments


def test_f1_nodal_frequency_validation():
    for bad_freq in (0.0, -250.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            NodalCurrentSolver(equivalent_frequency_khz=bad_freq)  # type: ignore[arg-type]

    solver = NodalCurrentSolver()
    assert solver.freq_hz == pytest.approx(250e3)


def test_f2_f3_nodal_typed_models_no_silent_defaults_or_zsurge_clamp():
    with pytest.raises(ValidationError):
        NodeIn.model_validate({"id": "n1", "x": 0.0, "y": 0.0, "z": 10.0})
    with pytest.raises(ValidationError):
        NodeIn.model_validate(
            {"id": "n1", "x": 0.0, "y": 0.0, "z": 10.0, "node_type": "invalid_role"}
        )
    with pytest.raises(ValidationError):
        SegmentIn.model_validate({"id": "s1", "start_node_id": "n1", "end_node_id": "n2"})
    with pytest.raises(ValidationError):
        SegmentIn.model_validate(
            {
                "id": "s1",
                "start_node_id": "n1",
                "end_node_id": "n2",
                "cross_section_mm2": 0.0,
                "resistivity_ohm_m": 1.72e-8,
            }
        )
    with pytest.raises(ValidationError):
        SegmentIn.model_validate(
            {
                "id": "s1",
                "start_node_id": "n1",
                "end_node_id": "n2",
                "cross_section_mm2": 50.0,
                "resistivity_ohm_m": 0.0,
            }
        )

    # z_surge = 0.0 rejected in build_network (no max(1e-4, z_surge) clamp)
    nodes, _ = _two_branch_network()
    solver = NodalCurrentSolver()
    with pytest.raises(ValueError, match="z_surge"):
        solver.build_network(
            nodes,
            [
                SegmentIn(
                    id="s1",
                    start_node_id="n1",
                    end_node_id="n2",
                    cross_section_mm2=50.0,
                    resistivity_ohm_m=1.72e-8,
                    z_surge=0.0,
                )
            ],
        )

    # Unclamped small positive z_surge = 1e-6 (< 1e-4) preserved faithfully
    solver.build_network(
        nodes,
        [
            SegmentIn(
                id="s1",
                start_node_id="n1",
                end_node_id="n2",
                cross_section_mm2=50.0,
                resistivity_ohm_m=1.72e-8,
                z_surge=1e-6,
            ),
            SegmentIn(
                id="s2",
                start_node_id="n1",
                end_node_id="n3",
                cross_section_mm2=50.0,
                resistivity_ohm_m=1.72e-8,
                z_surge=3e-6,
            ),
        ],
    )
    res = solver.calculate_current_sharing("n1", ["n2", "n3"], 1000.0)
    assert res["kc_factors"]["s1"] == pytest.approx(0.75, rel=1e-6)
    assert res["kc_factors"]["s2"] == pytest.approx(0.25, rel=1e-6)


def test_f4_f5_f6_nodal_topology_errors_disconnected_diagnostic_and_current():
    nodes, segments = _two_branch_network()
    solver = NodalCurrentSolver()

    # F.4: Unknown node ID on segment raises ValueError
    with pytest.raises(ValueError, match="unknown end_node_id"):
        solver.build_network(
            nodes,
            [
                SegmentIn(
                    id="s_bad",
                    start_node_id="n1",
                    end_node_id="n_missing",
                    cross_section_mm2=50.0,
                    resistivity_ohm_m=1.72e-8,
                )
            ],
        )

    # F.4: Zero-length segment (coincident coordinates) raises ValueError
    coincident_nodes = [
        NodeIn(id="a", x=1.0, y=2.0, z=3.0, node_type="conductor"),
        NodeIn(id="b", x=1.0, y=2.0, z=3.0, node_type="conductor"),
    ]
    with pytest.raises(ValueError, match="zero or non-positive length"):
        solver.build_network(
            coincident_nodes,
            [
                SegmentIn(
                    id="s_zero",
                    start_node_id="a",
                    end_node_id="b",
                    cross_section_mm2=50.0,
                    resistivity_ohm_m=1.72e-8,
                )
            ],
        )

    # F.5: Invalid references raise ValueError
    solver.build_network(nodes, segments)
    with pytest.raises(ValueError, match="Injection node"):
        solver.calculate_current_sharing("n_unknown", ["n2"], 100000.0)
    with pytest.raises(ValueError, match="non-empty"):
        solver.calculate_current_sharing("n1", [], 100000.0)
    with pytest.raises(ValueError, match="Earth node"):
        solver.calculate_current_sharing("n1", ["n_unknown_earth"], 100000.0)

    # F.5: Valid disconnected graph returns converged=False diagnostic
    disc_solver = NodalCurrentSolver()
    disc_solver.build_network(
        [
            NodeIn(id="inj", x=0.0, y=0.0, z=10.0, node_type="air_termination"),
            NodeIn(id="e1", x=0.0, y=0.0, z=0.0, node_type="earth_point"),
        ],
        [],
    )
    disc_res = disc_solver.calculate_current_sharing("inj", ["e1"], 100000.0)
    assert disc_res["converged"] is False
    assert any("galvanically isolated" in w for w in disc_res["warnings"])

    # F.6: total_injection_current_a required, > 0, not bool, no max(1.0, ...) clamp
    with pytest.raises(TypeError):
        solver.calculate_current_sharing("n1", ["n2", "n3"])  # type: ignore[call-arg]
    for bad_i in (0.0, -50.0, float("nan"), float("inf"), True, False):
        with pytest.raises(ValueError):
            solver.calculate_current_sharing("n1", ["n2", "n3"], bad_i)  # type: ignore[arg-type]

    sub_amp_res = solver.calculate_current_sharing("n1", ["n2", "n3"], 0.25)
    assert sub_amp_res["converged"] is True
    assert sub_amp_res["total_earth_current_a"] == pytest.approx(0.25, rel=1e-6)
    assert sum(sub_amp_res["kc_factors"].values()) == pytest.approx(1.0, rel=1e-6)


# ===========================================================================
# G. ifc_importer.py (Rule G.1)
# ===========================================================================


def test_g1_ifc_importer_rejects_empty_and_non_step_headers():
    for bad_bytes in (b"", b"   \n\t  ", b"not an ifc file", b"%PDF-1.7\n"):
        with pytest.raises(ValueError):
            IFCImporter.parse_ifc_building_elements(bad_bytes)

    res = IFCImporter.parse_ifc_building_elements(VALID_IFC_BYTES)
    assert res["parsed"] is True
    assert res["detected_building"] == {
        "length_m": 28.0,
        "width_m": 16.0,
        "height_m": 12.0,
        "roof_type": None,
    }


# ===========================================================================
# H. protective_angle.py (Rule H.1)
# ===========================================================================


def test_h1_protective_angle_figure_1_note_1_verbatim_quote():
    src = Path(protective_angle_mod.__file__).read_text(encoding="utf-8")
    expected_quote = (
        "The protection angle method is not applicable beyond the values marked with • in this Figure 1."
    )
    assert expected_quote in src
    assert "■" not in src


# ===========================================================================
# Criterion D: HTTP 422 / 200 probes across all 7 Step 2.7-B6 endpoints
# ===========================================================================


def test_criterion_d_all_seven_b6_endpoints_422_and_200():
    json_endpoints = [
        "/api/v1/projects/generate-bom",
        "/api/v1/calculations/pv-clearance",
        "/api/v1/calculations/hvi-selection",
        "/api/v1/optimization/optimize-rods",
        "/api/v1/calculations/peec-thermal",
        "/api/v1/calculations/nodal-kc",
    ]
    for ep in json_endpoints:
        r_empty = client.post(ep, json={})
        assert r_empty.status_code == 422, f"{ep} returned {r_empty.status_code}"

    # IFC missing file / empty file / non-IFC file -> 422, never 500
    assert client.post("/api/v1/imports/ifc").status_code == 422
    assert (
        client.post(
            "/api/v1/imports/ifc",
            files={"file": ("empty.ifc", b"", "application/octet-stream")},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/imports/ifc",
            files={"file": ("bad.ifc", b"NOT-IFC-CONTENT", "application/octet-stream")},
        ).status_code
        == 422
    )

    # Engine-level / domain-invalid 422 checks
    assert (
        client.post(
            "/api/v1/optimization/optimize-rods",
            json={
                "lps_class": "I",
                "building_bounds": [-15.0, -10.0, 15.0, 10.0],
                "roof_height_m": 15.0,
                "targets_to_protect": [{"id": "t1", "x": 0.0, "y": 0.0, "z": 15.0}],
                "target_sphere_radius_m": 45.0,  # disagrees with Class I (20 m)
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/calculations/nodal-kc",
            json={
                "nodes": [{"id": "n1", "x": 0.0, "y": 0.0, "z": 10.0, "node_type": "conductor"}],
                "segments": [
                    {
                        "id": "s1",
                        "start_node_id": "n1",
                        "end_node_id": "n_missing",
                        "cross_section_mm2": 50.0,
                        "resistivity_ohm_m": 1.72e-8,
                    }
                ],
                "injection_node": "n1",
                "earth_nodes": ["n1"],
                "total_injection_current_a": 100000.0,
            },
        ).status_code
        == 422
    )

    # Valid 200 probes on all 7 endpoints
    assert (
        client.post(
            "/api/v1/projects/generate-bom",
            json={
                "project_name": "Test",
                "lps_class": "I",
                "building_length_m": 30.0,
                "building_width_m": 20.0,
                "building_height_m": 15.0,
                "rod_count": 4,
                "down_conductor_count": 4,
            },
        ).status_code
        == 200
    )
    assert (
        client.post("/api/v1/calculations/pv-clearance", json=_valid_pv_kwargs()).status_code
        == 200
    )
    assert (
        client.post("/api/v1/calculations/hvi-selection", json=_valid_hvi_kwargs()).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/optimization/optimize-rods",
            json={
                "lps_class": "I",
                "building_bounds": [-15.0, -10.0, 15.0, 10.0],
                "roof_height_m": 15.0,
                "targets_to_protect": [{"id": "t1", "x": 0.0, "y": 0.0, "z": 15.0}],
                "iterations": 10,
                "random_seed": 42,
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/calculations/peec-thermal",
            json={
                "props": {"material": "copper", "cross_section_mm2": 50.0},
                "lps_class": "I",
                "parallel_conductor_spacing_m": 0.1,
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/calculations/nodal-kc",
            json={
                "nodes": [
                    {"id": "n1", "x": 0.0, "y": 0.0, "z": 10.0, "node_type": "conductor"},
                    {"id": "n2", "x": 0.0, "y": 0.0, "z": 0.0, "node_type": "conductor"},
                    {"id": "n3", "x": 10.0, "y": 0.0, "z": 0.0, "node_type": "conductor"},
                ],
                "segments": [
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
                "injection_node": "n1",
                "earth_nodes": ["n2", "n3"],
                "total_injection_current_a": 100000.0,
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/imports/ifc",
            files={"file": ("building.ifc", VALID_IFC_BYTES, "application/octet-stream")},
        ).status_code
        == 200
    )
