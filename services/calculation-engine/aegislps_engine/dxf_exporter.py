import ezdxf
import io
import math
from typing import Any


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


class DXFExporter:
    @staticmethod
    def export_2d_plan(building_length: float, building_width: float, nodes: list) -> bytes:
        _require_positive_finite("building_length", building_length)
        _require_positive_finite("building_width", building_width)
        if not isinstance(nodes, list):
            raise ValueError(f"nodes must be a list of dicts, got {type(nodes).__name__}.")

        for idx, n in enumerate(nodes):
            if not isinstance(n, dict) or "x" not in n or "y" not in n:
                raise ValueError(
                    f"nodes[{idx}] must be a dict containing required keys 'x' and 'y'."
                )
            _require_finite_coord(f"nodes[{idx}]['x']", n["x"])
            _require_finite_coord(f"nodes[{idx}]['y']", n["y"])

        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        # Add layers using valid ezdxf API
        layer_bldg = doc.layers.add("BUILDING_OUTLINE")
        layer_bldg.color = 7

        layer_air = doc.layers.add("AIR_TERMINATIONS")
        layer_air.color = 1 # Red

        # Draw Building Box
        msp.add_lwpolyline([
            (0, 0),
            (building_length, 0),
            (building_length, building_width),
            (0, building_width),
            (0, 0)
        ], dxfattribs={"layer": "BUILDING_OUTLINE"})

        # Draw Air Termination Nodes
        for n in nodes:
            msp.add_circle((n["x"], n["y"]), radius=0.3, dxfattribs={"layer": "AIR_TERMINATIONS"})

        stream = io.StringIO()
        doc.write(stream)
        return stream.getvalue().encode('utf-8')
