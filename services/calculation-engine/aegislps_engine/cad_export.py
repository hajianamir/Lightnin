import base64
import json
import math
import struct
from typing import Any, Dict, List, Optional, Tuple

_ALLOWED_NODE_TYPES = frozenset(
    {"air_termination", "down_conductor", "earth_point", "bonding", "conductor"}
)


def _require_positive_finite(name: str, val: Any) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(f"{name} must be a finite number > 0, not bool; got {val!r}.")
    fval = float(val)
    if not math.isfinite(fval) or fval <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    return fval


def _require_finite_coord(name: str, val: Any) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(f"{name} must be a finite number, not bool; got {val!r}.")
    fval = float(val)
    if not math.isfinite(fval):
        raise ValueError(f"{name} must be finite, got {val!r}.")
    return fval


class GLTF3DExporter:
    """
    glTF 2.0 3D Geometry Exporter for interoperability with CAD and BIM tools (FreeCAD, Blender, AutoCAD).
    Serializes building geometry, conductor lines, and air-termination rods.
    """

    @staticmethod
    def export_gltf_scene(
        building_length: float,
        building_width: float,
        building_height: float,
        nodes: List[Dict[str, Any]],
        segments: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        bl = _require_positive_finite("building_length", building_length)
        bw = _require_positive_finite("building_width", building_width)
        bh = _require_positive_finite("building_height", building_height)
        if not isinstance(nodes, list):
            raise ValueError(f"nodes must be a list, got {type(nodes).__name__}.")
        if segments is not None and not isinstance(segments, list):
            raise ValueError(
                f"segments must be a list when provided, got {type(segments).__name__}."
            )

        norm_nodes: List[Dict[str, Any]] = []
        node_by_id: Dict[str, Tuple[float, float, float]] = {}

        for idx, n in enumerate(nodes):
            if not isinstance(n, dict) or "x" not in n or "y" not in n:
                raise ValueError(
                    f"nodes[{idx}] must be a dict containing required keys 'x' and 'y'."
                )
            x = _require_finite_coord(f"nodes[{idx}]['x']", n["x"])
            y = _require_finite_coord(f"nodes[{idx}]['y']", n["y"])
            z = (
                _require_finite_coord(f"nodes[{idx}]['z']", n["z"])
                if "z" in n and n["z"] is not None
                else bh
            )
            raw_type = n.get("node_type")
            if raw_type is None:
                node_type = "air_termination"
            elif isinstance(raw_type, str) and raw_type in _ALLOWED_NODE_TYPES:
                node_type = raw_type
            else:
                raise ValueError(
                    f"nodes[{idx}]['node_type'] must be one of {sorted(_ALLOWED_NODE_TYPES)}, "
                    f"got {raw_type!r}."
                )
            nid = n.get("id")
            if nid is not None:
                if not isinstance(nid, str) or not nid.strip():
                    raise ValueError(
                        f"nodes[{idx}]['id'] must be a non-empty string when provided."
                    )
                # glTF Y-up convention matching Building_Envelope: [x, z_height, y_plan]
                node_by_id[nid] = (x, z, y)

            norm_nodes.append({"id": nid, "x": x, "y": y, "z": z, "node_type": node_type})

        # Build 3D line-segment vertex pairs (glTF primitive mode 1 = LINES)
        line_vertices: List[Tuple[float, float, float]] = []

        if segments:
            for idx, seg in enumerate(segments):
                if (
                    not isinstance(seg, dict)
                    or "start_node_id" not in seg
                    or "end_node_id" not in seg
                ):
                    raise ValueError(
                        f"segments[{idx}] must be a dict with 'start_node_id' and 'end_node_id'."
                    )
                sid = seg["start_node_id"]
                eid = seg["end_node_id"]
                if sid not in node_by_id or eid not in node_by_id:
                    raise ValueError(
                        f"segments[{idx}] references unknown node id ({sid!r} -> {eid!r})."
                    )
                line_vertices.append(node_by_id[sid])
                line_vertices.append(node_by_id[eid])

        # Vertical down-conductor drops & air-termination finials from node data
        ring_pts: List[Tuple[float, float, float]] = []
        for n in norm_nodes:
            vx, vy, vz = n["x"], n["z"], n["y"]
            nt = n["node_type"]
            if nt == "down_conductor":
                top_y = vy if vy > 0.0 else bh
                line_vertices.append((vx, top_y, vz))
                line_vertices.append((vx, 0.0, vz))
                ring_pts.append((vx, top_y, vz))
            elif nt in ("bonding", "conductor"):
                ring_pts.append((vx, vy, vz))
            elif nt == "air_termination":
                line_vertices.append((vx, vy, vz))
                line_vertices.append((vx, vy + 0.5, vz))
                ring_pts.append((vx, vy, vz))
            elif nt == "earth_point":
                line_vertices.append((vx, bh, vz))
                line_vertices.append((vx, vy, vz))

        # Interconnecting roof conductor ring/path when >= 2 roof-level nodes exist and no segments given
        if not segments and len(ring_pts) >= 2:
            if len(ring_pts) >= 3:
                cx = sum(p[0] for p in ring_pts) / len(ring_pts)
                cz = sum(p[2] for p in ring_pts) / len(ring_pts)
                ordered = sorted(
                    ring_pts, key=lambda p: math.atan2(p[2] - cz, p[0] - cx)
                )
                for idx in range(len(ordered)):
                    line_vertices.append(ordered[idx])
                    line_vertices.append(ordered[(idx + 1) % len(ordered)])
            else:
                line_vertices.append(ring_pts[0])
                line_vertices.append(ring_pts[1])

        conductor_node: Dict[str, Any] = {"name": "Conductor_Paths"}
        gltf: Dict[str, Any] = {
            "asset": {
                "version": "2.0",
                "generator": "AegisLPS 3D CAD Exporter v1.0.0-alpha.1",
            },
            "scene": 0,
            "scenes": [
                {
                    "name": "AegisLPS Engineering Scene",
                    "nodes": [0, 1],
                }
            ],
            "nodes": [
                {
                    "name": "Building_Envelope",
                    "translation": [0.0, bh / 2.0, 0.0],
                    "scale": [bl / 2.0, bh / 2.0, bw / 2.0],
                },
                {
                    "name": "Lightning_Protection_System",
                    "children": [2],
                },
                conductor_node,
            ],
        }

        if line_vertices:
            packed = b"".join(
                struct.pack("<3f", float(p[0]), float(p[1]), float(p[2]))
                for p in line_vertices
            )
            # Re-unpack exact float32 values so accessor min/max match IEEE-754 float32 bytes
            unpacked = [
                struct.unpack_from("<3f", packed, i * 12)
                for i in range(len(line_vertices))
            ]
            min_bounds = [
                min(v[0] for v in unpacked),
                min(v[1] for v in unpacked),
                min(v[2] for v in unpacked),
            ]
            max_bounds = [
                max(v[0] for v in unpacked),
                max(v[1] for v in unpacked),
                max(v[2] for v in unpacked),
            ]
            b64_payload = base64.b64encode(packed).decode("ascii")
            conductor_node["mesh"] = 0
            gltf["buffers"] = [
                {
                    "byteLength": len(packed),
                    "uri": f"data:application/octet-stream;base64,{b64_payload}",
                }
            ]
            gltf["bufferViews"] = [
                {
                    "buffer": 0,
                    "byteOffset": 0,
                    "byteLength": len(packed),
                    "target": 34962,
                }
            ]
            gltf["accessors"] = [
                {
                    "bufferView": 0,
                    "byteOffset": 0,
                    "componentType": 5126,
                    "count": len(line_vertices),
                    "type": "VEC3",
                    "min": min_bounds,
                    "max": max_bounds,
                }
            ]
            gltf["meshes"] = [
                {
                    "name": "Conductor_Paths_Mesh",
                    "primitives": [
                        {
                            "attributes": {"POSITION": 0},
                            "mode": 1,
                        }
                    ],
                }
            ]

        return json.dumps(gltf, indent=2)
