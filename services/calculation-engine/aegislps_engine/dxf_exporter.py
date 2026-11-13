import io
import math
from typing import Any, Dict, List, Optional, Tuple

import ezdxf

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


def _validate_and_normalize_nodes(nodes: list) -> List[Dict[str, Any]]:
    if not isinstance(nodes, list):
        raise ValueError(f"nodes must be a list of dicts, got {type(nodes).__name__}.")

    normalized: List[Dict[str, Any]] = []
    for idx, n in enumerate(nodes):
        if not isinstance(n, dict) or "x" not in n or "y" not in n:
            raise ValueError(
                f"nodes[{idx}] must be a dict containing required keys 'x' and 'y'."
            )
        x = _require_finite_coord(f"nodes[{idx}]['x']", n["x"])
        y = _require_finite_coord(f"nodes[{idx}]['y']", n["y"])
        if "z" in n and n["z"] is not None:
            _require_finite_coord(f"nodes[{idx}]['z']", n["z"])

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

        node_id = n.get("id")
        if node_id is not None and (not isinstance(node_id, str) or not node_id.strip()):
            raise ValueError(f"nodes[{idx}]['id'] must be a non-empty string when provided.")

        normalized.append({"id": node_id, "x": x, "y": y, "node_type": node_type})
    return normalized


def _validate_segments(
    segments: Optional[List[Dict[str, Any]]],
    node_by_id: Dict[str, Tuple[float, float]],
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    if segments is None:
        return []
    if not isinstance(segments, list):
        raise ValueError(
            f"segments must be a list of dicts when provided, got {type(segments).__name__}."
        )
    edges: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
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
        if not isinstance(sid, str) or sid not in node_by_id:
            raise ValueError(f"segments[{idx}]['start_node_id'] {sid!r} not found in nodes.")
        if not isinstance(eid, str) or eid not in node_by_id:
            raise ValueError(f"segments[{idx}]['end_node_id'] {eid!r} not found in nodes.")
        edges.append((node_by_id[sid], node_by_id[eid]))
    return edges


class DXFExporter:
    @staticmethod
    def export_2d_plan(
        building_length: float,
        building_width: float,
        nodes: list,
        segments: Optional[List[Dict[str, Any]]] = None,
    ) -> bytes:
        bl = _require_positive_finite("building_length", building_length)
        bw = _require_positive_finite("building_width", building_width)
        norm_nodes = _validate_and_normalize_nodes(nodes)
        node_by_id: Dict[str, Tuple[float, float]] = {
            n["id"]: (n["x"], n["y"]) for n in norm_nodes if n["id"] is not None
        }
        segment_edges = _validate_segments(segments, node_by_id)

        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        # Existing layer names preserved; conductor and down-conductor layers added
        layer_bldg = doc.layers.add("BUILDING_OUTLINE")
        layer_bldg.color = 7

        layer_cond = doc.layers.add("CONDUCTORS")
        layer_cond.color = 3  # Green

        layer_down = doc.layers.add("DOWN_CONDUCTORS")
        layer_down.color = 5  # Blue

        layer_air = doc.layers.add("AIR_TERMINATIONS")
        layer_air.color = 1  # Red

        # 1. Roof perimeter (closed LWPOLYLINE on BUILDING_OUTLINE)
        msp.add_lwpolyline(
            [
                (0.0, 0.0),
                (bl, 0.0),
                (bl, bw),
                (0.0, bw),
            ],
            close=True,
            dxfattribs={"layer": "BUILDING_OUTLINE"},
        )

        air_nodes = [n for n in norm_nodes if n["node_type"] == "air_termination"]
        ring_nodes = [
            n
            for n in norm_nodes
            if n["node_type"] in ("down_conductor", "bonding", "conductor")
        ]
        down_nodes = [
            n for n in norm_nodes if n["node_type"] in ("down_conductor", "earth_point")
        ]

        # 2. Conductor rings and interconnecting lines on CONDUCTORS
        for p_start, p_end in segment_edges:
            msp.add_line(p_start, p_end, dxfattribs={"layer": "CONDUCTORS"})

        if not segment_edges:
            if len(ring_nodes) >= 3:
                cx = sum(n["x"] for n in ring_nodes) / len(ring_nodes)
                cy = sum(n["y"] for n in ring_nodes) / len(ring_nodes)
                ordered = sorted(
                    ring_nodes,
                    key=lambda n: math.atan2(n["y"] - cy, n["x"] - cx),
                )
                msp.add_lwpolyline(
                    [(n["x"], n["y"]) for n in ordered],
                    close=True,
                    dxfattribs={"layer": "CONDUCTORS"},
                )
            elif len(ring_nodes) == 2:
                msp.add_line(
                    (ring_nodes[0]["x"], ring_nodes[0]["y"]),
                    (ring_nodes[1]["x"], ring_nodes[1]["y"]),
                    dxfattribs={"layer": "CONDUCTORS"},
                )
            elif len(ring_nodes) == 1:
                rn = ring_nodes[0]
                if air_nodes:
                    target = min(
                        air_nodes,
                        key=lambda a: math.hypot(a["x"] - rn["x"], a["y"] - rn["y"]),
                    )
                    tx, ty = target["x"], target["y"]
                    if math.hypot(tx - rn["x"], ty - rn["y"]) == 0.0:
                        tx, ty = bl, 0.0
                else:
                    tx, ty = (bl, 0.0) if (rn["x"], rn["y"]) != (bl, 0.0) else (0.0, 0.0)
                msp.add_line(
                    (rn["x"], rn["y"]),
                    (tx, ty),
                    dxfattribs={"layer": "CONDUCTORS"},
                )

        # 3. Down-conductor plan symbols (LINE cross-ticks on DOWN_CONDUCTORS)
        tick = 0.25
        for dn in down_nodes:
            dx, dy = dn["x"], dn["y"]
            msp.add_line(
                (dx - tick, dy - tick),
                (dx + tick, dy + tick),
                dxfattribs={"layer": "DOWN_CONDUCTORS"},
            )
            msp.add_line(
                (dx - tick, dy + tick),
                (dx + tick, dy - tick),
                dxfattribs={"layer": "DOWN_CONDUCTORS"},
            )

        # 4. Air-termination markers (CIRCLE entities on AIR_TERMINATIONS)
        for an in air_nodes:
            msp.add_circle(
                (an["x"], an["y"]),
                radius=0.3,
                dxfattribs={"layer": "AIR_TERMINATIONS"},
            )

        stream = io.StringIO()
        doc.write(stream)
        return stream.getvalue().encode("utf-8")
