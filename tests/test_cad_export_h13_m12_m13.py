"""Step 4.4 — H13, M12, M13: Real IFC bounding-box import, CAD export buttons, and DXF/glTF geometry."""

from __future__ import annotations

import base64
import io
import json
import struct
from collections import Counter
from pathlib import Path

import ezdxf
import pytest
from fastapi.testclient import TestClient

from aegislps_api.main import app
from aegislps_engine.cad_export import GLTF3DExporter
from aegislps_engine.dxf_exporter import DXFExporter
from aegislps_engine.ifc_importer import IFCImporter

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_step_ifc(data_lines: list[str]) -> bytes:
    body = "\n".join(data_lines)
    return (
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');\n"
        "FILE_NAME('sample.ifc','2026-11-09T00:00:00',('Author'),('Org'),'Pre','App','');\n"
        "FILE_SCHEMA(('IFC4'));\n"
        "ENDSEC;\n"
        "DATA;\n"
        f"{body}\n"
        "ENDSEC;\n"
        "END-ISO-10303-21;\n"
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# H13 — IFCImporter.parse_ifc_building_elements
# ---------------------------------------------------------------------------


def test_h13_ifc_bounding_box_dimensions_points_used_and_warnings() -> None:
    # dx = 17 - (-5) = 22.0, dy = 9 - (-3) = 12.0, dz = 14.25 - 0.0 = 14.25
    payload = _make_step_ifc(
        [
            "#10 = IFCCARTESIANPOINT((-5.0, -3.0, 0.0));",
            "#11 = IFCCARTESIANPOINT((17.0, 9.0, 6.5));",
            "#12 = IFCCARTESIANPOINT((17.0, -3.0, 14.25));",
            "#13 = IFCCARTESIANPOINT((-5.0, 9.0, 14.25));",
            "#14 = IFCCARTESIANPOINT((2.0, 4.0));",  # 2D sketch point ignored for 3D bbox
        ]
    )
    res = IFCImporter.parse_ifc_building_elements(payload)
    assert res["parsed"] is True
    assert res["points_used"] == 4
    assert res["detected_building"] == {
        "length_m": pytest.approx(22.0),
        "width_m": pytest.approx(12.0),
        "height_m": pytest.approx(14.25),
        "roof_type": None,
    }
    joined_warnings = " ".join(res["warnings"]).lower()
    assert "reviewed by qualified designer" in joined_warnings
    assert "bounding-box estimate" in joined_warnings
    assert "roof_type" in joined_warnings

    # Larger Y extent becomes length_m, and explicit IFCROOF enum derives roof_type
    payload_swapped = _make_step_ifc(
        [
            "#1 = IFCSIUNIT(*, .LENGTHUNIT., .MILLI., .METRE.);",
            "#2 = IFCCARTESIANPOINT((0., 0., 0.));",
            "#3 = IFCCARTESIANPOINT((14000., 36000., 9500.));",
            "#4 = IFCROOF('guid', #5, 'Main Roof', $, $, #6, #7, $, .GABLE_ROOF.);",
        ]
    )
    res_swapped = IFCImporter.parse_ifc_building_elements(payload_swapped)
    assert res_swapped["parsed"] is True
    assert res_swapped["points_used"] == 2
    assert res_swapped["detected_building"] == {
        "length_m": pytest.approx(36.0),
        "width_m": pytest.approx(14.0),
        "height_m": pytest.approx(9.5),
        "roof_type": "gable",
    }


def test_h13_ifc_no_points_or_non_finite_or_flat_plane_returns_parsed_false() -> None:
    empty_data = _make_step_ifc(["#1 = IFCPROJECT('id', $, 'Empty', $, $, $, $, $, $);"])
    res_empty = IFCImporter.parse_ifc_building_elements(empty_data)
    assert res_empty["parsed"] is False
    assert isinstance(res_empty.get("error"), str) and len(res_empty["error"]) > 0
    assert res_empty["detected_building"] is None

    nan_data = _make_step_ifc(
        [
            "#1 = IFCCARTESIANPOINT((0.0, 0.0, 0.0));",
            "#2 = IFCCARTESIANPOINT((10.0, NAN, 8.0));",
        ]
    )
    res_nan = IFCImporter.parse_ifc_building_elements(nan_data)
    assert res_nan["parsed"] is False
    assert "error" in res_nan and res_nan["detected_building"] is None

    inf_data = _make_step_ifc(
        [
            "#1 = IFCCARTESIANPOINT((0.0, 0.0, 0.0));",
            "#2 = IFCCARTESIANPOINT((10.0, 12.0, INF));",
        ]
    )
    res_inf = IFCImporter.parse_ifc_building_elements(inf_data)
    assert res_inf["parsed"] is False
    assert res_inf["detected_building"] is None

    coplanar_data = _make_step_ifc(
        [
            "#1 = IFCCARTESIANPOINT((0.0, 0.0, 0.0));",
            "#2 = IFCCARTESIANPOINT((20.0, 10.0, 0.0));",
        ]
    )
    res_coplanar = IFCImporter.parse_ifc_building_elements(coplanar_data)
    assert res_coplanar["parsed"] is False
    assert res_coplanar["detected_building"] is None


def test_h13_ifc_two_distinct_payloads_produce_different_outputs() -> None:
    ifc_a = _make_step_ifc(
        [
            "#1 = IFCCARTESIANPOINT((0.0, 0.0, 0.0));",
            "#2 = IFCCARTESIANPOINT((34.0, 19.0, 11.5));",
        ]
    )
    ifc_b = _make_step_ifc(
        [
            "#1 = IFCCARTESIANPOINT((-10.0, -5.0, 0.0));",
            "#2 = IFCCARTESIANPOINT((38.0, 16.0, 23.0));",
        ]
    )
    out_a = IFCImporter.parse_ifc_building_elements(ifc_a)
    out_b = IFCImporter.parse_ifc_building_elements(ifc_b)
    assert out_a["parsed"] is True and out_b["parsed"] is True
    assert out_a["detected_building"] != out_b["detected_building"]
    assert out_a["detected_building"]["length_m"] == pytest.approx(34.0)
    assert out_b["detected_building"]["length_m"] == pytest.approx(48.0)


def test_h13_ifc_header_and_empty_payload_validation_still_raises_value_error() -> None:
    for invalid in (None, "ISO-10303-21;", 42):
        with pytest.raises(ValueError):
            IFCImporter.parse_ifc_building_elements(invalid)  # type: ignore[arg-type]

    for bad_bytes in (b"", b"   \r\n\t ", b"NOT-ISO-STEP", b"%PDF-1.7\n"):
        with pytest.raises(ValueError):
            IFCImporter.parse_ifc_building_elements(bad_bytes)


# ---------------------------------------------------------------------------
# M13 — DXFExporter and GLTF3DExporter
# ---------------------------------------------------------------------------


def test_m13_dxf_contains_roof_conductor_down_conductor_and_air_termination_layers() -> None:
    # 1) Minimal synthetic case (A5): 1 roof + 1 conductor + 1 air-termination node
    dxf_min = DXFExporter.export_2d_plan(
        24.0,
        12.0,
        [
            {"id": "at-1", "x": 12.0, "y": 6.0, "node_type": "air_termination"},
            {"id": "dc-1", "x": 0.0, "y": 0.0, "node_type": "down_conductor"},
        ],
    )
    doc_min = ezdxf.read(io.StringIO(dxf_min.decode("utf-8")))
    counts_min = Counter(e.dxf.layer for e in doc_min.modelspace())
    assert len(counts_min) >= 3
    assert counts_min["BUILDING_OUTLINE"] == 1
    assert counts_min["CONDUCTORS"] == 1
    assert counts_min["DOWN_CONDUCTORS"] == 2
    assert counts_min["AIR_TERMINATIONS"] == 1

    # 2) Full 4-corner ring + 2 air-termination rods
    nodes_full = [
        {"id": "dc-1", "x": 0.0, "y": 0.0, "node_type": "down_conductor"},
        {"id": "dc-2", "x": 30.0, "y": 0.0, "node_type": "down_conductor"},
        {"id": "dc-3", "x": 30.0, "y": 20.0, "node_type": "down_conductor"},
        {"id": "dc-4", "x": 0.0, "y": 20.0, "node_type": "down_conductor"},
        {"id": "at-1", "x": 10.0, "y": 10.0, "node_type": "air_termination"},
        {"id": "at-2", "x": 20.0, "y": 10.0, "node_type": "air_termination"},
    ]
    dxf_full = DXFExporter.export_2d_plan(30.0, 20.0, nodes_full)
    doc_full = ezdxf.read(io.StringIO(dxf_full.decode("utf-8")))
    msp = doc_full.modelspace()

    roof_entities = [e for e in msp if e.dxf.layer == "BUILDING_OUTLINE"]
    cond_entities = [e for e in msp if e.dxf.layer == "CONDUCTORS"]
    down_entities = [e for e in msp if e.dxf.layer == "DOWN_CONDUCTORS"]
    air_entities = [e for e in msp if e.dxf.layer == "AIR_TERMINATIONS"]

    assert len(roof_entities) == 1 and roof_entities[0].dxftype() == "LWPOLYLINE"
    assert roof_entities[0].closed is True
    assert len(cond_entities) == 1 and cond_entities[0].dxftype() == "LWPOLYLINE"
    assert cond_entities[0].closed is True
    assert len(down_entities) == 8 and all(e.dxftype() == "LINE" for e in down_entities)
    assert len(air_entities) == 2 and all(e.dxftype() == "CIRCLE" for e in air_entities)

    # Invalid node_type or unknown segment endpoint rejected
    with pytest.raises(ValueError):
        DXFExporter.export_2d_plan(20.0, 10.0, [{"x": 1.0, "y": 2.0, "node_type": "bogus"}])
    with pytest.raises(ValueError):
        DXFExporter.export_2d_plan(
            20.0,
            10.0,
            [{"id": "n1", "x": 1.0, "y": 2.0}],
            segments=[{"start_node_id": "n1", "end_node_id": "missing"}],
        )


def test_m13_gltf_scene_is_valid_2_0_and_contains_conductor_paths_geometry() -> None:
    nodes = [
        {"id": "dc-1", "x": -15.0, "y": -10.0, "z": 15.0, "node_type": "down_conductor"},
        {"id": "dc-2", "x": 15.0, "y": -10.0, "z": 15.0, "node_type": "down_conductor"},
        {"id": "at-1", "x": 0.0, "y": 0.0, "z": 15.0, "node_type": "air_termination"},
    ]
    raw = GLTF3DExporter.export_gltf_scene(30.0, 20.0, 15.0, nodes)
    gltf = json.loads(raw)

    assert gltf["asset"]["version"] == "2.0"
    node_names = [n["name"] for n in gltf["nodes"]]
    assert "Building_Envelope" in node_names
    assert "Conductor_Paths" in node_names

    cond_node = next(n for n in gltf["nodes"] if n["name"] == "Conductor_Paths")
    assert cond_node["mesh"] == 0
    assert gltf["meshes"][0]["primitives"][0]["mode"] == 1  # LINES

    uri = gltf["buffers"][0]["uri"]
    assert uri.startswith("data:application/octet-stream;base64,")
    buf_bytes = base64.b64decode(uri.split(",", 1)[1])
    assert len(buf_bytes) == gltf["buffers"][0]["byteLength"]

    acc = gltf["accessors"][0]
    assert acc["type"] == "VEC3"
    assert acc["componentType"] == 5126
    assert acc["count"] >= 6 and acc["count"] % 2 == 0
    assert len(buf_bytes) == acc["count"] * 12

    verts = [struct.unpack_from("<3f", buf_bytes, i * 12) for i in range(acc["count"])]
    assert min(v[1] for v in verts) == pytest.approx(0.0)  # Down-conductor reaches ground y=0
    assert max(v[1] for v in verts) == pytest.approx(15.5)  # Air-termination tip at 15.0 + 0.5


# ---------------------------------------------------------------------------
# API & M12 UI source checks
# ---------------------------------------------------------------------------


def test_api_ifc_import_and_cad_exports_end_to_end() -> None:
    r_bad = client.post(
        "/api/v1/imports/ifc",
        files={"file": ("bad.ifc", b"NOT-IFC-HEADER", "application/octet-stream")},
    )
    assert r_bad.status_code == 422

    header_only = _make_step_ifc([])
    r_empty_geom = client.post(
        "/api/v1/imports/ifc",
        files={"file": ("empty_geom.ifc", header_only, "application/octet-stream")},
    )
    assert r_empty_geom.status_code == 200
    assert r_empty_geom.json()["parsed"] is False
    assert "error" in r_empty_geom.json()

    valid_ifc = _make_step_ifc(
        [
            "#1 = IFCCARTESIANPOINT((0.0, 0.0, 0.0));",
            "#2 = IFCCARTESIANPOINT((42.0, 18.5, 16.0));",
        ]
    )
    r_valid = client.post(
        "/api/v1/imports/ifc",
        files={"file": ("substation.ifc", valid_ifc, "application/octet-stream")},
    )
    assert r_valid.status_code == 200
    body = r_valid.json()
    assert body["parsed"] is True
    assert body["detected_building"]["length_m"] == pytest.approx(42.0)
    assert body["detected_building"]["width_m"] == pytest.approx(18.5)
    assert body["detected_building"]["height_m"] == pytest.approx(16.0)

    proj_payload = {
        "name": "Step 4.4 Export Check",
        "lps_class": "I",
        "building": {"length_m": 30.0, "width_m": 20.0, "height_m": 15.0, "roof_type": "flat"},
        "nodes": [
            {"id": "dc-1", "x": 0.0, "y": 0.0, "z": 15.0, "node_type": "down_conductor"},
            {"id": "dc-2", "x": 30.0, "y": 0.0, "z": 15.0, "node_type": "down_conductor"},
            {"id": "at-1", "x": 15.0, "y": 10.0, "z": 15.0, "node_type": "air_termination"},
        ],
        "segments": [
            {
                "id": "seg-1",
                "start_node_id": "dc-1",
                "end_node_id": "dc-2",
                "material": "copper",
                "cross_section_mm2": 50.0,
            }
        ],
        "separation_points": [],
    }
    r_dxf = client.post("/api/v1/exports/dxf", json=proj_payload)
    assert r_dxf.status_code == 200
    doc = ezdxf.read(io.StringIO(r_dxf.content.decode("utf-8")))
    layer_counts = Counter(e.dxf.layer for e in doc.modelspace())
    assert layer_counts["BUILDING_OUTLINE"] == 1
    assert layer_counts["CONDUCTORS"] == 1
    assert layer_counts["DOWN_CONDUCTORS"] == 4
    assert layer_counts["AIR_TERMINATIONS"] == 1

    r_gltf = client.post("/api/v1/exports/gltf", json=proj_payload)
    assert r_gltf.status_code == 200
    gltf_doc = r_gltf.json()
    assert gltf_doc["asset"]["version"] == "2.0"
    assert any(n["name"] == "Conductor_Paths" and "mesh" in n for n in gltf_doc["nodes"])


def test_m12_web_app_cad_export_buttons_use_relative_fetch_and_no_alert() -> None:
    app_tsx = (REPO_ROOT / "apps" / "web" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert "'/api/v1/exports/dxf'" in app_tsx
    assert "'/api/v1/exports/gltf'" in app_tsx
    assert "DXF download ready at" not in app_tsx
    assert "glTF download ready at" not in app_tsx
    assert "setExportError" in app_tsx
