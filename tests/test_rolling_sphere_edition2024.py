"""IEC 62305-4:2024 Table A.5 rolling sphere radius and consumer verification (Step 1.6)."""

import ast
import io
import math
from pathlib import Path
from typing import Set, Tuple

import docx
import pytest

from aegislps_domain.models import Building, Project, SeparationCalculationResult
from aegislps_engine.optimization import OptimizationInput
from aegislps_geometry.mesh_rolling_sphere import (
    ArbitraryMeshRollingSphereEngine,
    MeshRollingSphereInput,
    TriangleFace,
)
from aegislps_geometry.rolling_sphere import (
    RollingSphereEngine,
    protected_radius_at_height,
    rolling_sphere_radius_m,
)
from aegislps_reporting.docx_renderer import DOCXReportRenderer

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# 1. Table A.5 (IEC 62305-4:2024, p. 56) protection-level radii
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("lps_class", "expected_r_m"),
    [
        ("I", 313.0),
        ("II", 260.0),
        ("III", 200.0),
        ("IV", 200.0),
    ],
)
def test_table_a5_radii_by_protection_level(lps_class: str, expected_r_m: float):
    assert rolling_sphere_radius_m(lps_class) == pytest.approx(expected_r_m, abs=0.5)
    assert rolling_sphere_radius_m(lps_class=lps_class) == pytest.approx(
        expected_r_m, abs=0.5
    )
    assert rolling_sphere_radius_m(f" {lps_class.lower()} ") == pytest.approx(
        expected_r_m, abs=0.5
    )


# ---------------------------------------------------------------------------
# 2. Formula consistency r = 10 * I_0^0.65 within 0.5 m
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("i0_ka", [50.0, 100.0, 150.0, 200.0])
def test_formula_10_i_pow_065_reproduction(i0_ka: float):
    analytical_r_m = 10.0 * (i0_ka ** 0.65)
    assert rolling_sphere_radius_m(i0_ka) == pytest.approx(analytical_r_m, abs=0.5)
    assert rolling_sphere_radius_m(i0_ka=i0_ka) == pytest.approx(
        analytical_r_m, abs=0.5
    )


# ---------------------------------------------------------------------------
# 3. Invalid inputs (unknown class, current <= 0, non-finite, ambiguous)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad_class", ["", " ", "0", "V", "CLASS_I", "1", "unknown"])
def test_invalid_lps_class_raises_value_error(bad_class: str):
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(bad_class)
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(lps_class=bad_class)


@pytest.mark.parametrize(
    "bad_current",
    [0, 0.0, -1e-6, -50.0, -200.0, float("nan"), float("inf"), float("-inf")],
)
def test_non_positive_or_non_finite_current_raises_value_error(bad_current: float):
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(bad_current)
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(i0_ka=bad_current)


def test_ambiguous_or_boolean_inputs_raise_value_error():
    with pytest.raises(ValueError):
        rolling_sphere_radius_m()
    with pytest.raises(ValueError):
        rolling_sphere_radius_m("I", i0_ka=200.0)
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(lps_class="I", i0_ka=200.0)
    with pytest.raises(ValueError):
        rolling_sphere_radius_m(True)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 4. Source audit: no hardcoded 20.0 Class I rolling-sphere radius remains
# ---------------------------------------------------------------------------
def _docstring_node_ids(tree: ast.AST) -> Set[int]:
    doc_ids: Set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                doc_ids.add(id(node.body[0].value))
    return doc_ids


def test_no_hardcoded_class_i_20m_in_packages_or_calculation_engine():
    # Complete inventory of legitimate non-rolling-sphere 20.0 literals in
    # packages/ and services/calculation-engine/:
    allowed_non_rolling_sphere_files = {
        "packages/domain-model/aegislps_domain/db_models.py",         # default building_length = 20.0 m
        "packages/domain-model/aegislps_domain/models.py",            # default Building.length_m = 20.0 m
        "packages/geometry/aegislps_geometry/mesh_method.py",         # default roof_width_m & Class IV 20.0 m mesh width (out of scope)
        "packages/geometry/aegislps_geometry/protective_angle.py",    # protective angle h=20.0 m table/cap (out of scope)
        "services/calculation-engine/aegislps_engine/earth_rod_sizing.py",  # 20.0 mm min rod diameter
        "services/calculation-engine/aegislps_engine/earthing.py",    # 20.0 m l1 length formula cap
        "services/calculation-engine/aegislps_engine/lemp_engine.py",  # 20.0 * log10(...) / 20.0 dB conversion
        "services/calculation-engine/aegislps_engine/peec_thermal.py",  # 20.0 C initial conductor temperature
        "services/calculation-engine/aegislps_engine/risk.py",        # default structure_width_m = 20.0 m
        "services/calculation-engine/aegislps_engine/spd_coordination.py",  # Type 2 SPD i_n_ka = 20.0 kA
    }

    unexpected_20_literals: list[Tuple[str, int]] = []
    hardcoded_r20_strings: list[Tuple[str, int, str]] = []

    for root_rel in ("packages", "services/calculation-engine"):
        root_dir = REPO_ROOT / root_rel
        for py_path in sorted(root_dir.rglob("*.py")):
            if "build" in py_path.parts or any(
                part.endswith(".egg-info") for part in py_path.parts
            ):
                continue
            rel_path = py_path.relative_to(REPO_ROOT).as_posix()
            source = py_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel_path)
            doc_ids = _docstring_node_ids(tree)

            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and id(node) not in doc_ids:
                    if isinstance(node.value, float) and node.value == 20.0:
                        if rel_path not in allowed_non_rolling_sphere_files:
                            unexpected_20_literals.append((rel_path, node.lineno))
                    elif isinstance(node.value, str) and (
                        "R=20m" in node.value or "R = 20m" in node.value
                    ):
                        hardcoded_r20_strings.append((rel_path, node.lineno, node.value))

    assert unexpected_20_literals == []
    assert hardcoded_r20_strings == []

    # Verify runtime defaults across all consumers
    assert RollingSphereEngine().r == pytest.approx(313.0)
    assert RollingSphereEngine(lps_class="II").r == pytest.approx(260.0)
    assert RollingSphereEngine(lps_class="III").r == pytest.approx(200.0)
    assert RollingSphereEngine(lps_class="IV").r == pytest.approx(200.0)
    assert MeshRollingSphereInput().sphere_radius_m == pytest.approx(313.0)
    assert OptimizationInput().target_sphere_radius_m == pytest.approx(313.0)
    assert OptimizationInput(lps_class="II").target_sphere_radius_m == pytest.approx(260.0)
    assert OptimizationInput(lps_class="III").target_sphere_radius_m == pytest.approx(200.0)
    assert OptimizationInput(lps_class="IV").target_sphere_radius_m == pytest.approx(200.0)
    assert OptimizationInput(
        lps_class="I", target_sphere_radius_m=42.5
    ).target_sphere_radius_m == pytest.approx(42.5)


# ---------------------------------------------------------------------------
# 5. DOCX report shows 313 m for Class I (and class-specific radii for II..IV)
# ---------------------------------------------------------------------------
def _extract_all_docx_text(docx_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(docx_bytes))
    chunks = [p.text for p in doc.paragraphs if p.text]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text:
                    chunks.append(cell.text)
    return "\n".join(chunks)


def test_docx_report_renders_313m_for_class_i_and_class_radii():
    sep = [
        SeparationCalculationResult(
            separation_point_id="sp-1",
            required_distance_s_m=0.80,
            actual_distance_m=1.20,
            pass_compliance=True,
            safety_margin_m=0.40,
            lps_class="I",
            ki_used=0.08,
            kc_used=0.5,
            km_used=1.0,
            length_l_m=20.0,
            formula_trace="s = 0.08 * (0.5 / 1.0) * 20.0 = 0.800m",
        )
    ]
    earthing = {
        "actual_effective_length_m": 100.0,
        "stationary_resistance_r_ohm": 1.5,
        "impulse_impedance_z_ohm": 1.0,
    }

    for lps_class, expected_r_int in (("I", 313), ("II", 260), ("III", 200), ("IV", 200)):
        project = Project(
            name=f"Facility Class {lps_class}",
            lps_class=lps_class,
            building=Building(length_m=10.0, width_m=10.0, height_m=10.0, roof_type="flat"),
        )
        docx_bytes = DOCXReportRenderer.render_docx_report(
            project=project,
            separation_results=sep,
            earthing_result=earthing,
        )
        full_text = _extract_all_docx_text(docx_bytes)
        assert f"Rolling Sphere (R={expected_r_int}m)" in full_text
        assert "R=20m" not in full_text


# ---------------------------------------------------------------------------
# 6. Analytical geometry verification on a 10 x 10 x 10 m building at R = 313 m
# ---------------------------------------------------------------------------
def test_10x10x10_building_analytical_rolling_sphere_at_r313():
    r_m = rolling_sphere_radius_m("I")
    assert r_m == pytest.approx(313.0)
    rs = RollingSphereEngine()

    # Part A: 10 m vertical corner mast (x=0, y=0, h=10 m <= R=313 m)
    # Analytical formula: rho(z) = sqrt(2*R*h - h^2) - sqrt(2*R*z - z^2)
    h_mast_m = 10.0
    hand_rho_c = math.sqrt(2.0 * 313.0 * 10.0 - 10.0 ** 2)  # sqrt(6160) = 78.48566748...
    assert hand_rho_c == pytest.approx(math.sqrt(6160.0), abs=1e-12)

    for z_m in (0.0, 2.0, 5.0, 8.0, 9.5):
        expected_rho = math.sqrt(2.0 * r_m * h_mast_m - h_mast_m ** 2) - math.sqrt(
            2.0 * r_m * z_m - z_m ** 2
        )
        computed_rho = protected_radius_at_height(r_m, h_mast_m, z_m)
        assert computed_rho == pytest.approx(expected_rho, abs=1e-3)

        # Probe RollingSphereEngine.check_surface_exposure straddling rho(z) within +-5e-4 m (< 1e-3 m)
        inside = rs.check_surface_exposure(
            expected_rho - 5e-4, 0.0, z_m, 0.0, 0.0, h_mast_m
        )
        outside = rs.check_surface_exposure(
            expected_rho + 5e-4, 0.0, z_m, 0.0, 0.0, h_mast_m
        )
        on_boundary = rs.check_surface_exposure(
            expected_rho, 0.0, z_m, 0.0, 0.0, h_mast_m
        )
        assert inside["protected"] is True
        assert outside["protected"] is False
        assert on_boundary["protective_height_z_m"] == pytest.approx(z_m, abs=1e-3)

    # Part B: 10 x 10 x 10 m building roof (z = 10 m) with 2 m rod on corner (0, 0) -> tip h = 12 m
    # Analytical roof protected radius: sqrt(2*313*12 - 144) - sqrt(2*313*10 - 100)
    #   = sqrt(7368) - sqrt(6160) = 85.83705494 - 78.48566748 = 7.35138745 m
    h_tip_m = 12.0
    z_roof_m = 10.0
    expected_roof_rho = math.sqrt(7368.0) - math.sqrt(6160.0)
    assert protected_radius_at_height(r_m, h_tip_m, z_roof_m) == pytest.approx(
        expected_roof_rho, abs=1e-3
    )

    # Roof center (5, 5, 10) at d = sqrt(50) = 7.0711 m < 7.3514 m -> protected
    assert rs.check_surface_exposure(5.0, 5.0, z_roof_m, 0.0, 0.0, h_tip_m)[
        "protected"
    ] is True
    # Adjacent roof corner (10, 0, 10) at d = 10.0 m > 7.3514 m -> exposed
    assert rs.check_surface_exposure(10.0, 0.0, z_roof_m, 0.0, 0.0, h_tip_m)[
        "protected"
    ] is False
    # Opposite roof corner (10, 10, 10) at d = 14.1421 m > 7.3514 m -> exposed
    assert rs.check_surface_exposure(10.0, 10.0, z_roof_m, 0.0, 0.0, h_tip_m)[
        "protected"
    ] is False

    # Verify ArbitraryMeshRollingSphereEngine default Class I radius (313 m) on the 10 x 10 x 10 m roof
    near_corner_tri = TriangleFace(
        id="roof_near_rod",
        v0=(0.0, 0.0, z_roof_m),
        v1=(5.0, 0.0, z_roof_m),
        v2=(0.0, 5.0, z_roof_m),
    )
    far_corner_tri = TriangleFace(
        id="roof_far_corner",
        v0=(10.0, 10.0, z_roof_m),
        v1=(8.0, 10.0, z_roof_m),
        v2=(10.0, 8.0, z_roof_m),
    )
    mesh_res = ArbitraryMeshRollingSphereEngine().evaluate_mesh_protection(
        MeshRollingSphereInput(
            triangles=[near_corner_tri, far_corner_tri],
            air_termination_tips=[(0.0, 0.0, h_tip_m)],
        )
    )
    assert mesh_res.sphere_radius_m == pytest.approx(313.0)
    assert mesh_res.face_clearances[0].is_protected is True
    assert mesh_res.face_clearances[1].is_protected is False
