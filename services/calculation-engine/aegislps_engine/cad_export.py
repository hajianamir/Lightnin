import json
import base64
import math
from typing import Dict, List, Any


def _require_positive_finite(name: str, val: Any) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(f"{name} must be a finite number > 0, not bool; got {val!r}.")
    fval = float(val)
    if not math.isfinite(fval) or fval <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
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
        nodes: List[Dict[str, Any]]
    ) -> str:
        _require_positive_finite("building_length", building_length)
        _require_positive_finite("building_width", building_width)
        _require_positive_finite("building_height", building_height)
        if not isinstance(nodes, list):
            raise ValueError(f"nodes must be a list, got {type(nodes).__name__}.")

        # Standard glTF 2.0 JSON structure
        gltf = {
            "asset": {
                "version": "2.0",
                "generator": "AegisLPS 3D CAD Exporter v1.0.0-alpha.1"
            },
            "scene": 0,
            "scenes": [
                {
                    "name": "AegisLPS Engineering Scene",
                    "nodes": [0, 1]
                }
            ],
            "nodes": [
                {
                    "name": "Building_Envelope",
                    "translation": [0, building_height / 2.0, 0],
                    "scale": [building_length / 2.0, building_height / 2.0, building_width / 2.0]
                },
                {
                    "name": "Lightning_Protection_System",
                    "children": []
                }
            ]
        }
        return json.dumps(gltf, indent=2)
