import io
import docx
from fastapi.testclient import TestClient

from aegislps_api.main import app
from aegislps_domain.models import Building, Project, SeparationCalculationResult
from aegislps_reporting.docx_renderer import DOCXReportRenderer

client = TestClient(app)


def _valid_project_payload(name: str = "API Test Project", lps_class: str = "I") -> dict:
    return {
        "name": name,
        "lps_class": lps_class,
        "building": {"length_m": 20, "width_m": 10, "height_m": 15, "roof_type": "flat"},
        "nodes": [{"id": "n1", "x": 0, "y": 0, "z": 15, "node_type": "air_termination"}],
        "segments": [],
        "separation_points": [
            {
                "id": "sp1",
                "name": "Test Point",
                "x": 1,
                "y": 1,
                "z": 15,
                "associated_node_id": "n1",
                "insulation_medium": "air",
                "physical_distance_m": 2.0,
            }
        ],
    }


def _assert_value_error_422(response) -> str:
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body
    assert isinstance(body["detail"], str)
    assert len(body["detail"]) > 0
    return body["detail"]


def test_separation_distance_invalid_lps_class_returns_422():
    payload = _valid_project_payload(lps_class="INVALID")
    response = client.post("/api/v1/calculations/separation-distance", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body, dict) and "detail" in body
    assert isinstance(body["detail"], list) and len(body["detail"]) == 1
    assert body["detail"][0]["loc"] == ["body", "lps_class"]
    assert "INVALID" in body["detail"][0]["msg"]

    # Engine-level missing associated_node_id ValueError still maps via B1 handler
    bad_node_payload = _valid_project_payload(lps_class="I")
    bad_node_payload["separation_points"][0]["associated_node_id"] = "missing_node"
    detail = _assert_value_error_422(
        client.post("/api/v1/calculations/separation-distance", json=bad_node_payload)
    )
    assert "missing_node" in detail


def test_rolling_sphere_negative_point_z_returns_422():
    payload = {
        "lps_class": "I",
        "point_x": 1.0,
        "point_y": 0.0,
        "point_z": -1.0,
        "rod_x": 0.0,
        "rod_y": 0.0,
        "rod_height_m": 15.0,
    }
    response = client.post("/api/v1/calculations/rolling-sphere", json=payload)
    detail = _assert_value_error_422(response)
    assert "-1.0" in detail


def test_protective_angle_invalid_lps_class_returns_422():
    # Scalar endpoint parameters bind as query params; values adapted from
    # tests/test_protective_angle_figure1.py::test_unknown_lps_class_raises_value_error.
    params = {
        "lps_class": "BAD",
        "rod_tip_x": 0.0,
        "rod_tip_y": 0.0,
        "rod_tip_z": 10.0,
        "ref_plane_z": 0.0,
        "object_x": 2.0,
        "object_y": 0.0,
        "object_z": 5.0,
    }
    response = client.post("/api/v1/calculations/protective-angle", params=params)
    detail = _assert_value_error_422(response)
    assert "BAD" in detail


def test_earthing_invalid_lps_class_returns_422():
    # Shape from tests/test_earthing_and_spd.py::test_earthing_type_b_ring_dwight
    payload = {
        "lps_class": "BAD",
        "soil": {"rho_upper_ohm_m": 100.0},
        "electrode_type": "type_b_ring",
        "ring_radius_m": 15.0,
        "conductor_diameter_m": 0.01,
        "burial_depth_m": 0.5,
    }
    response = client.post("/api/v1/calculations/earthing", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body, dict) and "detail" in body
    assert isinstance(body["detail"], list) and len(body["detail"]) == 1
    assert body["detail"][0]["loc"] == ["body", "lps_class"]
    assert "BAD" in body["detail"][0]["msg"]

    # Engine-level Figure 5 domain ValueError (> 3000 ohm.m) still maps via B1 handler
    payload_fig5 = {**payload, "lps_class": "I", "soil": {"rho_upper_ohm_m": 3500.0}}
    detail = _assert_value_error_422(
        client.post("/api/v1/calculations/earthing", json=payload_fig5)
    )
    assert "3500.0" in detail


def test_touch_step_empty_body_returns_422():
    response = client.post("/api/v1/calculations/touch-step", json={})
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body, dict) and "detail" in body
    assert isinstance(body["detail"], list) and len(body["detail"]) >= 1
    missing_locs = {tuple(err["loc"]) for err in body["detail"]}
    assert ("body", "earth_potential_rise_v") in missing_locs
    assert ("body", "electrode_equivalent_radius_m") in missing_locs


def test_touch_step_negative_gpr_returns_422():
    # Shape from tests/test_earthing_and_spd.py::test_touch_and_step_hazard_control_dalziel
    payload = {
        "lps_class": "I",
        "soil_resistivity_ohm_m": 100.0,
        "surface_layer_material": "bare_soil",
        "fault_duration_s": 0.05,
        "body_weight_kg": 70.0,
        "peak_impulse_current_ka": 100.0,
        "down_conductor_radius_m": 0.005,
        "has_physical_insulation_barrier": False,
        "earth_potential_rise_v": -100,
        "electrode_equivalent_radius_m": 2.0,
    }
    response = client.post("/api/v1/calculations/touch-step", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body, dict) and "detail" in body
    assert isinstance(body["detail"], list) and len(body["detail"]) == 1
    assert body["detail"][0]["loc"] == ["body", "earth_potential_rise_v"]


def test_mesh_rolling_sphere_negative_radius_returns_422():
    # Shape from tests/test_peec_and_mesh_rolling_sphere.py::test_arbitrary_mesh_rolling_sphere_protection
    payload = {
        "sphere_radius_m": -5.0,
        "triangles": [
            {"id": "tri-near", "v0": [0, 0, 15], "v1": [2, 0, 15], "v2": [1, 2, 15]},
            {"id": "tri-far", "v0": [40, 40, 15], "v1": [42, 40, 15], "v2": [41, 42, 15]},
        ],
        "air_termination_tips": [[0.0, 0.0, 20.0]],
    }
    response = client.post("/api/v1/calculations/mesh-rolling-sphere", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body, dict) and "detail" in body
    assert isinstance(body["detail"], list) and len(body["detail"]) == 1
    assert body["detail"][0]["loc"] == ["body", "sphere_radius_m"]
    assert "sphere_radius_m" in body["detail"][0]["msg"]

    # Engine-level empty triangles ValueError maps via B1 handler
    empty_tri_payload = {
        "sphere_radius_m": 20.0,
        "triangles": [],
        "air_termination_tips": [[0.0, 0.0, 10.0]],
    }
    detail = _assert_value_error_422(
        client.post("/api/v1/calculations/mesh-rolling-sphere", json=empty_tri_payload)
    )
    assert detail == "triangles must not be empty"


def test_optimize_rods_negative_sphere_radius_returns_422():
    # Shape from tests/test_optimization_and_pv.py::test_design_optimization_coverage_improvement
    payload = {
        "lps_class": "I",
        "building_bounds": [-15.0, -10.0, 15.0, 10.0],
        "roof_height_m": 15.0,
        "target_sphere_radius_m": -10.0,
        "iterations": 50,
        "random_seed": 123,
    }
    response = client.post("/api/v1/optimization/optimize-rods", json=payload)
    detail = _assert_value_error_422(response)
    assert "sphere_radius_m" in detail


def test_pdf_report_invalid_lps_class_returns_422():
    # Shape from tests/test_api_endpoints.py::test_pdf_report_endpoint
    payload = _valid_project_payload(name="PDF Test Project", lps_class="INVALID")
    response = client.post("/api/v1/reports/pdf", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body, dict) and "detail" in body
    assert isinstance(body["detail"], list) and len(body["detail"]) == 1
    assert body["detail"][0]["loc"] == ["body", "lps_class"]
    assert "INVALID" in body["detail"][0]["msg"]


def test_docx_report_valid_project_returns_200():
    payload = _valid_project_payload(name="DOCX Test Project", lps_class="I")
    response = client.post("/api/v1/reports/docx", json=payload)
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert len(response.content) > 5000

    doc = docx.Document(io.BytesIO(response.content))
    summary_table = doc.tables[1]
    assert summary_table.cell(4, 0).text == "Earthing Resistance (R_dc)"
    assert summary_table.cell(4, 2).text == "N/A"
    assert summary_table.cell(4, 3).text == "N/A"


def test_docx_renderer_non_none_earthing_result_unchanged():
    project = Project(
        project_id="12345678-1234-5678-1234-567812345678",
        name="Nuclear Facility Lightning Protection",
        lps_class="I",
        building=Building(length_m=50, width_m=30, height_m=20, roof_type="flat"),
    )
    results = [
        SeparationCalculationResult(
            separation_point_id="sp-1",
            required_distance_s_m=0.850,
            actual_distance_m=1.200,
            pass_compliance=True,
            safety_margin_m=0.350,
            lps_class="I",
            ki_used=0.08,
            kc_used=0.5,
            km_used=1.0,
            length_l_m=20.0,
            formula_trace="s = 0.08 * (0.5 / 1.0) * 20.0 = 0.800m",
        )
    ]
    earthing_info = {
        "actual_effective_length_m": 120.0,
        "stationary_resistance_r_ohm": 1.45,
        "impulse_impedance_z_ohm": 0.98,
    }
    docx_bytes = DOCXReportRenderer.render_docx_report(
        project=project,
        separation_results=results,
        earthing_result=earthing_info,
    )
    doc = docx.Document(io.BytesIO(docx_bytes))
    summary_table = doc.tables[1]
    assert summary_table.cell(4, 2).text == "Stationary R = 1.45 ohm"
    assert summary_table.cell(4, 3).text == "COMPLIANT (< 10 ohm)"
