"""Step 2.7-B5 verification tests (H9): domain models, separation, geometry, exporters, and API routes."""

import io
import json
import math

import ezdxf
import pytest
from fastapi.testclient import TestClient

from aegislps_api.main import app
from aegislps_domain.models import (
    Building,
    CalculationStatus,
    ConductorNode,
    ConductorSegment,
    Project,
    SeparationPoint,
)
from aegislps_engine.cad_export import GLTF3DExporter
from aegislps_engine.dxf_exporter import DXFExporter
from aegislps_engine.separation import SeparationDistanceEngine
from aegislps_geometry.mesh_method import (
    MeshMethodEngine,
    MeshMethodInput,
    RoofProtrusion,
)
from aegislps_geometry.mesh_rolling_sphere import (
    ArbitraryMeshRollingSphereEngine,
    MeshRollingSphereInput,
    TriangleFace,
    barycentric_grid,
)
from aegislps_geometry.protective_angle import ProtectiveAngleEngine
from aegislps_geometry.rolling_sphere import (
    RollingSphereEngine,
    protected_radius_at_height,
)

client = TestClient(app)


def _valid_project_dict() -> dict:
    return {
        "project_id": "b5-proj-0001",
        "name": "B5 Explicit Project",
        "lps_class": "I",
        "building": {
            "length_m": 20.0,
            "width_m": 10.0,
            "height_m": 15.0,
            "roof_type": "flat",
        },
        "nodes": [
            {
                "id": "n1",
                "x": 0.0,
                "y": 0.0,
                "z": 15.0,
                "node_type": "air_termination",
            }
        ],
        "segments": [
            {
                "id": "s1",
                "start_node_id": "n1",
                "end_node_id": "n1",
                "material": "copper",
                "cross_section_mm2": 50.0,
            }
        ],
        "separation_points": [
            {
                "id": "sp1",
                "name": "P1",
                "x": 1.0,
                "y": 1.0,
                "z": 15.0,
                "associated_node_id": "n1",
                "insulation_medium": "air",
                "physical_distance_m": 2.0,
            }
        ],
    }


# ---------------------------------------------------------------------------
# A. Domain models (packages/domain-model/aegislps_domain/models.py)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"x": 0.0, "y": 0.0, "z": -0.01, "node_type": "air_termination"},
        {"x": True, "y": 0.0, "z": 1.0, "node_type": "air_termination"},
        {"x": 0.0, "y": False, "z": 1.0, "node_type": "air_termination"},
        {"x": 0.0, "y": 0.0, "z": True, "node_type": "air_termination"},
        {"x": float("nan"), "y": 0.0, "z": 1.0, "node_type": "air_termination"},
        {"x": 0.0, "y": float("inf"), "z": 1.0, "node_type": "air_termination"},
        {"x": 0.0, "y": 0.0, "z": float("-inf"), "node_type": "air_termination"},
    ],
)
def test_a1_conductor_node_coords_reject(kwargs):
    with pytest.raises(ValueError):
        ConductorNode(**kwargs)


def test_a1_conductor_node_coords_accept():
    n_ground = ConductorNode(x=-5.0, y=3.5, z=0.0, node_type="earth_point")
    n_roof = ConductorNode(x=0.0, y=0.0, z=15.0, node_type="air_termination")
    assert n_ground.z == 0.0
    assert n_roof.z == 15.0


@pytest.mark.parametrize("bad_type", [None, "", "mast", "AIR_TERMINATION", True])
def test_a2_conductor_node_type_reject(bad_type):
    with pytest.raises(ValueError):
        ConductorNode(x=0.0, y=0.0, z=10.0, node_type=bad_type)
    with pytest.raises(ValueError):
        ConductorNode(x=0.0, y=0.0, z=10.0)


@pytest.mark.parametrize(
    "valid_type", ["air_termination", "down_conductor", "earth_point", "bonding"]
)
def test_a2_conductor_node_type_accept(valid_type):
    node = ConductorNode(x=0.0, y=0.0, z=5.0, node_type=valid_type)
    assert node.node_type == valid_type


@pytest.mark.parametrize("bad_mat", [None, "", "gold", "COPPER", True])
def test_a3_conductor_segment_material_reject(bad_mat):
    with pytest.raises(ValueError):
        ConductorSegment(
            start_node_id="n1",
            end_node_id="n2",
            material=bad_mat,
            cross_section_mm2=50.0,
        )
    with pytest.raises(ValueError):
        ConductorSegment(start_node_id="n1", end_node_id="n2", cross_section_mm2=50.0)


@pytest.mark.parametrize("valid_mat", ["copper", "aluminium", "steel"])
def test_a3_conductor_segment_material_accept(valid_mat):
    seg = ConductorSegment(
        start_node_id="n1",
        end_node_id="n2",
        material=valid_mat,
        cross_section_mm2=50.0,
    )
    assert seg.material == valid_mat


@pytest.mark.parametrize(
    "bad_area", [0, 0.0, -50.0, True, False, float("nan"), float("inf")]
)
def test_a4_conductor_segment_cross_section_reject(bad_area):
    with pytest.raises(ValueError):
        ConductorSegment(
            start_node_id="n1",
            end_node_id="n2",
            material="copper",
            cross_section_mm2=bad_area,
        )
    with pytest.raises(ValueError):
        ConductorSegment(start_node_id="n1", end_node_id="n2", material="copper")


def test_a4_conductor_segment_cross_section_accept():
    seg = ConductorSegment(
        start_node_id="n1",
        end_node_id="n2",
        material="copper",
        cross_section_mm2=50.0,
    )
    assert seg.cross_section_mm2 == 50.0


@pytest.mark.parametrize(
    "bad_kc", [0.0, -0.5, 1.01, True, False, float("nan"), float("inf")]
)
def test_a5_conductor_segment_kc_factor_reject(bad_kc):
    with pytest.raises(ValueError):
        ConductorSegment(
            start_node_id="n1",
            end_node_id="n2",
            material="copper",
            cross_section_mm2=50.0,
            kc_factor=bad_kc,
        )


def test_a5_conductor_segment_kc_factor_accept():
    seg_default = ConductorSegment(
        start_node_id="n1",
        end_node_id="n2",
        material="copper",
        cross_section_mm2=50.0,
    )
    seg_explicit = ConductorSegment(
        start_node_id="n1",
        end_node_id="n2",
        material="copper",
        cross_section_mm2=50.0,
        kc_factor=0.44,
    )
    assert seg_default.kc_factor == 1.0
    assert seg_explicit.kc_factor == 0.44


@pytest.mark.parametrize(
    "coords",
    [
        {"x": 0.0, "y": 0.0, "z": -0.1},
        {"x": True, "y": 0.0, "z": 1.0},
        {"x": 0.0, "y": float("nan"), "z": 1.0},
        {"x": 0.0, "y": 0.0, "z": float("inf")},
    ],
)
def test_a6_separation_point_coords_reject(coords):
    with pytest.raises(ValueError):
        SeparationPoint(
            name="SP",
            associated_node_id="n1",
            insulation_medium="air",
            physical_distance_m=1.0,
            **coords,
        )


def test_a6_separation_point_coords_accept():
    sp = SeparationPoint(
        name="SP",
        x=-2.0,
        y=3.0,
        z=0.0,
        associated_node_id="n1",
        insulation_medium="air",
        physical_distance_m=1.0,
    )
    assert sp.z == 0.0


@pytest.mark.parametrize("bad_medium", [None, "", "wood", "AIR", True])
def test_a7_separation_point_insulation_medium_reject(bad_medium):
    with pytest.raises(ValueError):
        SeparationPoint(
            name="SP",
            x=0.0,
            y=0.0,
            z=10.0,
            associated_node_id="n1",
            insulation_medium=bad_medium,
            physical_distance_m=1.0,
        )
    with pytest.raises(ValueError):
        SeparationPoint(
            name="SP",
            x=0.0,
            y=0.0,
            z=10.0,
            associated_node_id="n1",
            physical_distance_m=1.0,
        )


@pytest.mark.parametrize("valid_medium", ["air", "solid", "insulating_standoff"])
def test_a7_separation_point_insulation_medium_accept(valid_medium):
    sp = SeparationPoint(
        name="SP",
        x=0.0,
        y=0.0,
        z=10.0,
        associated_node_id="n1",
        insulation_medium=valid_medium,
        physical_distance_m=1.0,
    )
    assert sp.insulation_medium == valid_medium


@pytest.mark.parametrize("bad_dist", [-0.01, -5.0, True, False, float("nan"), float("inf")])
def test_a8_separation_point_physical_distance_reject(bad_dist):
    with pytest.raises(ValueError):
        SeparationPoint(
            name="SP",
            x=0.0,
            y=0.0,
            z=10.0,
            associated_node_id="n1",
            insulation_medium="air",
            physical_distance_m=bad_dist,
        )


def test_a8_separation_point_physical_distance_accept():
    sp = SeparationPoint(
        name="SP",
        x=0.0,
        y=0.0,
        z=10.0,
        associated_node_id="n1",
        insulation_medium="air",
        physical_distance_m=0.0,
    )
    assert sp.physical_distance_m == 0.0


@pytest.mark.parametrize(
    "dims",
    [
        {"length_m": 0.0, "width_m": 10.0, "height_m": 15.0},
        {"length_m": 20.0, "width_m": -1.0, "height_m": 15.0},
        {"length_m": 20.0, "width_m": 10.0, "height_m": 0.0},
        {"length_m": True, "width_m": 10.0, "height_m": 15.0},
        {"length_m": float("nan"), "width_m": 10.0, "height_m": 15.0},
    ],
)
def test_a9_building_dimensions_and_project_building_reject(dims):
    with pytest.raises(ValueError):
        Building(roof_type="flat", **dims)
    with pytest.raises(ValueError):
        Building(roof_type="flat")
    with pytest.raises(ValueError):
        Project(lps_class="I")


def test_a9_building_dimensions_and_project_building_accept():
    bldg = Building(length_m=20.0, width_m=10.0, height_m=15.0, roof_type="flat")
    proj = Project(lps_class="I", building=bldg)
    assert proj.building.height_m == 15.0


@pytest.mark.parametrize("bad_roof", [None, "", "dome", "FLAT", True])
def test_a10_building_roof_type_reject(bad_roof):
    with pytest.raises(ValueError):
        Building(length_m=20.0, width_m=10.0, height_m=15.0, roof_type=bad_roof)
    with pytest.raises(ValueError):
        Building(length_m=20.0, width_m=10.0, height_m=15.0)


@pytest.mark.parametrize("valid_roof", ["flat", "gable", "hip"])
def test_a10_building_roof_type_accept(valid_roof):
    bldg = Building(length_m=20.0, width_m=10.0, height_m=15.0, roof_type=valid_roof)
    assert bldg.roof_type == valid_roof


@pytest.mark.parametrize("bad_cls", [None, "", "V", "i", 1, True])
def test_a11_project_lps_class_reject(bad_cls):
    bldg = Building(length_m=20.0, width_m=10.0, height_m=15.0, roof_type="flat")
    with pytest.raises(ValueError):
        Project(lps_class=bad_cls, building=bldg)
    with pytest.raises(ValueError):
        Project(building=bldg)


@pytest.mark.parametrize("valid_cls", ["I", "II", "III", "IV"])
def test_a11_project_lps_class_accept(valid_cls):
    bldg = Building(length_m=20.0, width_m=10.0, height_m=15.0, roof_type="flat")
    proj = Project(lps_class=valid_cls, building=bldg)
    assert proj.lps_class == valid_cls


# ---------------------------------------------------------------------------
# B. Separation distance engine (services/calculation-engine/aegislps_engine/separation.py)
# ---------------------------------------------------------------------------


def test_b2_missing_associated_node_raises_value_error():
    proj = Project.model_validate(_valid_project_dict())
    proj.separation_points[0].associated_node_id = "nonexistent_node"
    with pytest.raises(ValueError, match="not found in project nodes"):
        SeparationDistanceEngine().calculate_project(proj)


def test_b2_valid_associated_node_or_explicit_route_accepts():
    proj = Project.model_validate(_valid_project_dict())
    res = SeparationDistanceEngine().calculate_project(proj)
    assert len(res) == 1
    assert res[0].required_distance_s_m == pytest.approx(1.2)
    assert res[0].status == CalculationStatus.WARNING


def test_b3_associated_node_at_or_below_ground_raises_value_error():
    proj = Project.model_validate(_valid_project_dict())
    proj.nodes[0] = ConductorNode(
        id="n1", x=0.0, y=0.0, z=0.0, node_type="earth_point"
    )
    with pytest.raises(
        ValueError, match="associated node must be above ground for route length"
    ):
        SeparationDistanceEngine().calculate_project(proj)


def test_b1_b4_separation_kc_and_explicit_route_unchanged():
    proj = Project.model_validate(_valid_project_dict())
    proj.down_conductor_count = 2
    proj.earth_resistances_within_factor_2 = True
    proj.separation_points[0].route_length_to_bonding_m = 6.0
    res = SeparationDistanceEngine().calculate_project(proj)
    assert res[0].kc_used == pytest.approx(0.66)
    assert res[0].required_distance_s_m == pytest.approx(0.08 * 0.66 * 6.0)
    assert res[0].status == CalculationStatus.CALCULATED


# ---------------------------------------------------------------------------
# C. Geometry: rolling_sphere, mesh_method, mesh_rolling_sphere
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "args",
    [
        (0.0, 10.0, 5.0),
        (-20.0, 10.0, 5.0),
        (20.0, -0.1, 5.0),
        (20.0, 40.1, 5.0),
        (20.0, 10.0, -0.1),
        (True, 10.0, 5.0),
        (20.0, False, 5.0),
        (20.0, 10.0, True),
        (float("nan"), 10.0, 5.0),
        (20.0, float("inf"), 5.0),
    ],
)
def test_c1_protected_radius_at_height_reject(args):
    with pytest.raises(ValueError):
        protected_radius_at_height(*args)


def test_c1_protected_radius_at_height_accept():
    assert protected_radius_at_height(20.0, 10.0, 5.0) == pytest.approx(
        math.sqrt(300.0) - math.sqrt(175.0)
    )
    assert protected_radius_at_height(20.0, 0.0, 0.0) == 0.0


@pytest.mark.parametrize("bad_r", [0.0, -10.0, True, False, float("nan"), float("inf")])
def test_c2_rolling_sphere_engine_init_reject(bad_r):
    with pytest.raises(ValueError):
        RollingSphereEngine(bad_r)


def test_c2_rolling_sphere_engine_init_accept():
    assert RollingSphereEngine(30.0).r == 30.0
    assert RollingSphereEngine().r == 20.0


@pytest.mark.parametrize(
    "bad_body",
    [
        {},
        {
            "point_x": 1.0,
            "point_y": 0.0,
            "point_z": 5.0,
            "rod_x": 0.0,
            "rod_y": 0.0,
            "rod_height_m": 10.0,
        },
        {
            "lps_class": "I",
            "sphere_radius_m": 20.0,
            "point_x": 1.0,
            "point_y": 0.0,
            "point_z": 5.0,
            "rod_x": 0.0,
            "rod_y": 0.0,
            "rod_height_m": 10.0,
        },
        {
            "lps_class": "V",
            "point_x": 1.0,
            "point_y": 0.0,
            "point_z": 5.0,
            "rod_x": 0.0,
            "rod_y": 0.0,
            "rod_height_m": 10.0,
        },
        {
            "sphere_radius_m": 0.0,
            "point_x": 1.0,
            "point_y": 0.0,
            "point_z": 5.0,
            "rod_x": 0.0,
            "rod_y": 0.0,
            "rod_height_m": 10.0,
        },
    ],
)
def test_c3_rolling_sphere_route_xor_reject(bad_body):
    resp = client.post("/api/v1/calculations/rolling-sphere", json=bad_body)
    assert resp.status_code == 422


def test_c3_rolling_sphere_route_xor_accept():
    base = {
        "point_x": 1.0,
        "point_y": 0.0,
        "point_z": 5.0,
        "rod_x": 0.0,
        "rod_y": 0.0,
        "rod_height_m": 10.0,
    }
    r_cls = client.post(
        "/api/v1/calculations/rolling-sphere", json={"lps_class": "I", **base}
    )
    r_rad = client.post(
        "/api/v1/calculations/rolling-sphere", json={"sphere_radius_m": 20.0, **base}
    )
    assert r_cls.status_code == 200
    assert r_rad.status_code == 200
    assert r_cls.json() == r_rad.json()


@pytest.mark.parametrize(
    "args",
    [
        (True, 0.0, 5.0, 0.0, 0.0, 10.0),
        (1.0, 0.0, -0.1, 0.0, 0.0, 10.0),
        (1.0, 0.0, 5.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, 5.0, 0.0, 0.0, -1.0),
        (1.0, 0.0, 5.0, 0.0, 0.0, 40.1),
        (float("nan"), 0.0, 5.0, 0.0, 0.0, 10.0),
        (1.0, 0.0, 5.0, 0.0, float("inf"), 10.0),
    ],
)
def test_c4_check_surface_exposure_reject(args):
    engine = RollingSphereEngine(20.0)
    with pytest.raises(ValueError):
        engine.check_surface_exposure(*args)


def test_c4_check_surface_exposure_accept():
    res = RollingSphereEngine(20.0).check_surface_exposure(1.0, 0.0, 5.0, 0.0, 0.0, 10.0)
    assert res["protected"] is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"id": "p", "x": 0.0, "y": 0.0, "z": 10.0, "height_above_roof_m": -0.1},
        {"id": "p", "x": True, "y": 0.0, "z": 10.0, "height_above_roof_m": 0.5},
        {"id": "p", "x": 0.0, "y": 0.0, "z": 10.0, "height_above_roof_m": True},
        {"id": "p", "x": float("nan"), "y": 0.0, "z": 10.0, "height_above_roof_m": 0.5},
        {"id": "p", "x": 0.0, "y": 0.0, "z": 10.0, "height_above_roof_m": 0.5, "is_metallic": 1},
        {"id": "p", "x": 0.0, "y": 0.0, "z": 10.0, "height_above_roof_m": 0.5, "is_metallic": "true"},
    ],
)
def test_c5_c6_roof_protrusion_reject(kwargs):
    with pytest.raises(ValueError):
        RoofProtrusion(**kwargs)


def test_c5_c6_roof_protrusion_accept():
    p = RoofProtrusion(id="p1", x=1.0, y=2.0, z=15.0, height_above_roof_m=0.0)
    assert p.is_metallic is True
    p2 = RoofProtrusion(
        id="p2", x=1.0, y=2.0, z=15.0, height_above_roof_m=0.5, is_metallic=False
    )
    assert p2.is_metallic is False


@pytest.mark.parametrize(
    "override",
    [
        {"lps_class": "V"},
        {"lps_class": "i"},
        {"lps_class": True},
        {"roof_length_m": 0.0},
        {"roof_width_m": -5.0},
        {"roof_length_m": True},
        {"mesh_grid_dx_m": 0.0},
        {"mesh_grid_dy_m": -5.0},
        {"mesh_grid_dx_m": False},
        {"has_perimeter_conductor": 1},
        {"has_perimeter_conductor": "true"},
        {"has_perimeter_conductor": None},
    ],
)
def test_c7_c8_c9_c10_mesh_method_input_reject(override):
    base = {
        "lps_class": "I",
        "roof_length_m": 30.0,
        "roof_width_m": 20.0,
        "mesh_grid_dx_m": 5.0,
        "mesh_grid_dy_m": 5.0,
        "has_perimeter_conductor": True,
    }
    base.update(override)
    with pytest.raises(ValueError):
        MeshMethodInput(**base)
    with pytest.raises(ValueError):
        MeshMethodInput()


def test_c7_c8_c9_c10_mesh_method_accept():
    inp = MeshMethodInput(
        lps_class="I",
        roof_length_m=30.0,
        roof_width_m=20.0,
        mesh_grid_dx_m=5.0,
        mesh_grid_dy_m=5.0,
        has_perimeter_conductor=True,
    )
    res = MeshMethodEngine().validate_mesh_design(inp)
    assert res.status == "COMPLIANT"


@pytest.mark.parametrize("bad_n", [True, False, 0, -3, 1.5, "12"])
def test_c11_barycentric_grid_reject(bad_n):
    with pytest.raises(ValueError):
        barycentric_grid(bad_n)


def test_c11_barycentric_grid_accept():
    assert len(barycentric_grid()) == 91
    assert len(barycentric_grid(6)) == 28


@pytest.mark.parametrize(
    "bad_v0",
    [
        (0.0, 0.0, -0.1),
        (True, 0.0, 1.0),
        (float("nan"), 0.0, 1.0),
        (0.0, float("inf"), 1.0),
    ],
)
def test_c12_triangle_face_reject(bad_v0):
    with pytest.raises(ValueError):
        TriangleFace(id="t1", v0=bad_v0, v1=(1.0, 0.0, 1.0), v2=(0.0, 1.0, 1.0))


def test_c12_triangle_face_accept():
    tri = TriangleFace(
        id="t1", v0=(0.0, 0.0, 0.0), v1=(1.0, 0.0, 2.0), v2=(0.0, 1.0, 2.0)
    )
    assert tri.v0 == (0.0, 0.0, 0.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"lps_class": "I", "sphere_radius_m": 20.0},
        {"sphere_radius_m": 0.0},
        {"sphere_radius_m": -5.0},
        {"sphere_radius_m": True},
        {"lps_class": "V"},
        {"sphere_radius_m": 20.0, "air_termination_tips": [(0.0, 0.0, -1.0)]},
        {"sphere_radius_m": 20.0, "air_termination_tips": [(0.0, 0.0, 40.1)]},
        {"sphere_radius_m": 20.0, "air_termination_tips": [(True, 0.0, 10.0)]},
    ],
)
def test_c13_c14_mesh_rolling_sphere_input_reject(kwargs):
    with pytest.raises(ValueError):
        MeshRollingSphereInput(**kwargs)


def test_c13_c14_c15_mesh_rolling_sphere_empty_triangles_and_accept():
    tri = TriangleFace(
        id="t1", v0=(-1.0, -1.0, 2.0), v1=(1.0, -1.0, 2.0), v2=(0.0, 1.0, 2.0)
    )
    inp_empty = MeshRollingSphereInput(
        lps_class="I", triangles=[], air_termination_tips=[(0.0, 0.0, 10.0)]
    )
    with pytest.raises(ValueError, match="triangles must not be empty"):
        ArbitraryMeshRollingSphereEngine().evaluate_mesh_protection(inp_empty)

    inp_cls = MeshRollingSphereInput(
        lps_class="I", triangles=[tri], air_termination_tips=[(0.0, 0.0, 10.0)]
    )
    inp_rad = MeshRollingSphereInput(
        sphere_radius_m=20.0, triangles=[tri], air_termination_tips=[(0.0, 0.0, 10.0)]
    )
    r_cls = ArbitraryMeshRollingSphereEngine().evaluate_mesh_protection(inp_cls)
    r_rad = ArbitraryMeshRollingSphereEngine().evaluate_mesh_protection(inp_rad)
    assert r_cls == r_rad
    assert r_cls.status == "FULL_COVERAGE"


# ---------------------------------------------------------------------------
# D. Protective angle (packages/geometry/aegislps_geometry/protective_angle.py)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "args",
    [
        ("BAD", 0.0, 0.0, 10.0, 0.0, 2.0, 0.0, 5.0),
        ("I", True, 0.0, 10.0, 0.0, 2.0, 0.0, 5.0),
        ("I", 0.0, 0.0, float("nan"), 0.0, 2.0, 0.0, 5.0),
        ("I", 0.0, 0.0, 10.0, 10.0, 2.0, 0.0, 5.0),  # h_tip == 0
        ("I", 0.0, 0.0, 8.0, 10.0, 2.0, 0.0, 5.0),  # h_tip < 0
    ],
)
def test_d1_d2_protective_angle_cone_reject(args):
    with pytest.raises(ValueError):
        ProtectiveAngleEngine().check_object_in_cone(*args)


def test_d1_d2_d3_protective_angle_cone_accept_and_over_hmax_kept():
    pa = ProtectiveAngleEngine()
    res_ok = pa.check_object_in_cone("I", 0.0, 0.0, 10.0, 0.0, 2.0, 0.0, 5.0)
    assert res_ok["applicable"] is True
    assert res_ok["protected"] is True

    res_over = pa.check_object_in_cone("I", 0.0, 0.0, 25.0, 0.0, 2.0, 0.0, 5.0)
    assert res_over == {
        "protected": False,
        "applicable": False,
        "protective_angle_deg": 0.0,
        "reason": "Height (25.0m) exceeds IEC 62305-3 limit (20.0m) for Class I. Must use Rolling Sphere.",
    }


# ---------------------------------------------------------------------------
# E. Exporters (cad_export.py, dxf_exporter.py)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "dims",
    [
        (0.0, 10.0, 15.0),
        (20.0, -1.0, 15.0),
        (20.0, 10.0, 0.0),
        (True, 10.0, 15.0),
        (float("nan"), 10.0, 15.0),
    ],
)
def test_e1_gltf_exporter_reject(dims):
    with pytest.raises(ValueError):
        GLTF3DExporter.export_gltf_scene(*dims, [])


def test_e1_gltf_exporter_accept():
    s = GLTF3DExporter.export_gltf_scene(20.0, 10.0, 15.0, [{"x": 0.0, "y": 0.0}])
    parsed = json.loads(s)
    assert parsed["asset"]["version"] == "2.0"


@pytest.mark.parametrize(
    "args",
    [
        (0.0, 10.0, []),
        (20.0, -5.0, []),
        (True, 10.0, []),
        (20.0, 10.0, [{"x": 1.0}]),  # missing y
        (20.0, 10.0, [{"y": 1.0}]),  # missing x
        (20.0, 10.0, [{}]),
        (20.0, 10.0, [{"x": True, "y": 1.0}]),
        (20.0, 10.0, [{"x": float("nan"), "y": 1.0}]),
    ],
)
def test_e2_dxf_exporter_reject(args):
    with pytest.raises(ValueError):
        DXFExporter.export_2d_plan(*args)


def test_e2_dxf_exporter_accept():
    raw = DXFExporter.export_2d_plan(20.0, 10.0, [{"x": 3.0, "y": 4.0}])
    doc = ezdxf.read(io.StringIO(raw.decode("utf-8")))
    circles = list(doc.modelspace().query("CIRCLE"))
    assert len(circles) == 1
    assert circles[0].dxf.center.x == pytest.approx(3.0)
    assert circles[0].dxf.center.y == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# F. API route wiring (services/api/aegislps_api/main.py)
# ---------------------------------------------------------------------------


def test_f1_f2_http_probes_422_and_200():
    proj = _valid_project_dict()

    # Empty / invalid requests -> 422 (never 500)
    assert client.post("/api/v1/calculations/separation-distance", json={}).status_code == 422
    assert client.post("/api/v1/calculations/rolling-sphere", json={}).status_code == 422
    assert (
        client.post(
            "/api/v1/calculations/protective-angle",
            params={
                "lps_class": "I",
                "rod_tip_x": 0.0,
                "rod_tip_y": 0.0,
                "rod_tip_z": 5.0,
                "ref_plane_z": 5.0,
                "object_x": 1.0,
                "object_y": 0.0,
                "object_z": 2.0,
            },
        ).status_code
        == 422
    )
    assert client.post("/api/v1/calculations/mesh-method", json={}).status_code == 422
    assert client.post("/api/v1/calculations/mesh-rolling-sphere", json={}).status_code == 422
    assert (
        client.post(
            "/api/v1/calculations/mesh-rolling-sphere",
            json={"lps_class": "I", "triangles": [], "air_termination_tips": []},
        ).status_code
        == 422
    )
    assert client.post("/api/v1/exports/gltf", json={}).status_code == 422
    assert client.post("/api/v1/exports/dxf", json={}).status_code == 422
    assert client.post("/api/v1/reports/docx", json={}).status_code == 422
    assert client.post("/api/v1/reports/pdf", json={}).status_code == 422
    assert client.post("/api/v1/projects/compute-checksum", json={}).status_code == 422

    # Valid explicit requests -> 200
    assert client.post("/api/v1/calculations/separation-distance", json=proj).status_code == 200
    assert (
        client.post(
            "/api/v1/calculations/rolling-sphere",
            json={
                "lps_class": "I",
                "point_x": 1.0,
                "point_y": 0.0,
                "point_z": 5.0,
                "rod_x": 0.0,
                "rod_y": 0.0,
                "rod_height_m": 10.0,
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/calculations/protective-angle",
            params={
                "lps_class": "I",
                "rod_tip_x": 0.0,
                "rod_tip_y": 0.0,
                "rod_tip_z": 10.0,
                "ref_plane_z": 0.0,
                "object_x": 2.0,
                "object_y": 0.0,
                "object_z": 5.0,
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/calculations/mesh-method",
            json={
                "lps_class": "I",
                "roof_length_m": 30.0,
                "roof_width_m": 20.0,
                "mesh_grid_dx_m": 5.0,
                "mesh_grid_dy_m": 5.0,
                "has_perimeter_conductor": True,
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/calculations/mesh-rolling-sphere",
            json={
                "lps_class": "I",
                "triangles": [
                    {
                        "id": "t1",
                        "v0": [-1.0, -1.0, 2.0],
                        "v1": [1.0, -1.0, 2.0],
                        "v2": [0.0, 1.0, 2.0],
                    }
                ],
                "air_termination_tips": [[0.0, 0.0, 10.0]],
            },
        ).status_code
        == 200
    )
    assert client.post("/api/v1/exports/gltf", json=proj).status_code == 200
    assert client.post("/api/v1/exports/dxf", json=proj).status_code == 200
    assert client.post("/api/v1/reports/docx", json=proj).status_code == 200
    assert client.post("/api/v1/reports/pdf", json=proj).status_code == 200
    assert client.post("/api/v1/projects/compute-checksum", json=proj).status_code == 200
