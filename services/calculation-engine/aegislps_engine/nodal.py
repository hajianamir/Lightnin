import math
import networkx as nx
import numpy as np
from pydantic import BaseModel, ConfigDict, field_validator
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from typing import Any, Dict, List, Optional, Sequence, Union

# Validated node_type set: domain-model roles plus nodal network "conductor".
_VALID_NODAL_NODE_TYPES = (
    "air_termination",
    "down_conductor",
    "earth_point",
    "bonding",
    "conductor",
)


def _check_finite_float(name: str, v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float, np.number)):
        raise ValueError(f"{name} must be a finite number, not bool; got {v!r}.")
    val = float(v)
    if not math.isfinite(val):
        raise ValueError(f"{name} must be finite, got {v!r}.")
    return val


def _check_positive_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val <= 0.0:
        raise ValueError(f"{name} must be > 0, got {v!r}.")
    return val


def _check_nonnegative_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val < 0.0:
        raise ValueError(f"{name} must be >= 0, got {v!r}.")
    return val


def _check_nonempty_str(name: str, v: Any) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{name} must be a non-empty string, got {v!r}.")
    return v


class NodeIn(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str
    x: float
    y: float
    z: float
    node_type: str

    @field_validator("id", mode="before")
    @classmethod
    def _validate_id(cls, v: Any) -> str:
        return _check_nonempty_str("id", v)

    @field_validator("x", "y", "z", mode="before")
    @classmethod
    def _validate_coords(cls, v: Any, info) -> float:
        return _check_finite_float(info.field_name, v)

    @field_validator("node_type", mode="before")
    @classmethod
    def _validate_node_type(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_NODAL_NODE_TYPES:
            raise ValueError(
                f"Unknown node_type {v!r}; expected one of {_VALID_NODAL_NODE_TYPES}."
            )
        return v


class SegmentIn(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str
    start_node_id: str
    end_node_id: str
    cross_section_mm2: float
    resistivity_ohm_m: float
    z_surge: Optional[float] = None
    length: Optional[float] = None

    @field_validator("id", "start_node_id", "end_node_id", mode="before")
    @classmethod
    def _validate_ids(cls, v: Any, info) -> str:
        return _check_nonempty_str(info.field_name, v)

    @field_validator("cross_section_mm2", "resistivity_ohm_m", mode="before")
    @classmethod
    def _validate_positive(cls, v: Any, info) -> float:
        return _check_positive_finite_float(info.field_name, v)

    @field_validator("z_surge", mode="before")
    @classmethod
    def _validate_z_surge(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        return _check_nonnegative_finite_float("z_surge", v)

    @field_validator("length", mode="before")
    @classmethod
    def _validate_length(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        return _check_positive_finite_float("length", v)


class NodalCurrentSolver:
    """
    Experimental Frequency-Domain Current-Sharing Solver.

    ENGINEERING STATUS:
    - Status: Experimental, unverified.
    - Simplified frequency-domain approximation Z = R_dc + omega * L_eff.
    - Note: This is a simplified single-frequency approximation representing the high-frequency
      inductive behavior of lightning transients. It omits frequency-dependent skin effect,
      capacitive coupling to ground, and non-uniform ground-return impedances.
    - Not certified as a full transient time-domain electromagnetic solver.
    """

    def __init__(
        self,
        # experimental single-frequency heuristic; not in IEC 62305-3:2024 Annex C
        equivalent_frequency_khz: float = 250.0,
    ):
        freq_khz = _check_positive_finite_float(
            "equivalent_frequency_khz", equivalent_frequency_khz
        )
        self.freq_hz = freq_khz * 1e3
        self.omega = 2.0 * np.pi * self.freq_hz
        self.graph = nx.Graph()

    def build_network(
        self,
        nodes: Sequence[Union[NodeIn, Dict[str, Any]]],
        segments: Sequence[Union[SegmentIn, Dict[str, Any]]],
    ) -> None:
        if not isinstance(nodes, (list, tuple)):
            raise ValueError("nodes must be a list of NodeIn items.")
        if not isinstance(segments, (list, tuple)):
            raise ValueError("segments must be a list of SegmentIn items.")

        parsed_nodes: List[NodeIn] = [
            n if isinstance(n, NodeIn) else NodeIn.model_validate(n) for n in nodes
        ]
        parsed_segments: List[SegmentIn] = [
            s if isinstance(s, SegmentIn) else SegmentIn.model_validate(s)
            for s in segments
        ]

        self.graph.clear()
        seen_node_ids = set()
        for n in parsed_nodes:
            if n.id in seen_node_ids:
                raise ValueError(f"Duplicate node id {n.id!r} in network.")
            seen_node_ids.add(n.id)
            self.graph.add_node(
                n.id,
                x=float(n.x),
                y=float(n.y),
                z=float(n.z),
                node_type=n.node_type,
            )

        seen_seg_ids = set()
        for s in parsed_segments:
            if s.id in seen_seg_ids:
                raise ValueError(f"Duplicate segment id {s.id!r} in network.")
            seen_seg_ids.add(s.id)

            u, v = s.start_node_id, s.end_node_id
            if u not in self.graph:
                raise ValueError(
                    f"Segment {s.id!r} references unknown start_node_id {u!r}."
                )
            if v not in self.graph:
                raise ValueError(
                    f"Segment {s.id!r} references unknown end_node_id {v!r}."
                )
            if u == v:
                raise ValueError(
                    f"Segment {s.id!r} has zero length (start_node_id == end_node_id == {u!r})."
                )

            if s.length is not None:
                length = float(s.length)
            else:
                dx = self.graph.nodes[u]["x"] - self.graph.nodes[v]["x"]
                dy = self.graph.nodes[u]["y"] - self.graph.nodes[v]["y"]
                dz = self.graph.nodes[u]["z"] - self.graph.nodes[v]["z"]
                length = float(np.sqrt(dx**2 + dy**2 + dz**2))

            if not math.isfinite(length) or length <= 0.0:
                raise ValueError(
                    f"Segment {s.id!r} has zero or non-positive length ({length})."
                )

            cross_section_m2 = float(s.cross_section_mm2) * 1e-6
            rho = float(s.resistivity_ohm_m)

            r_dc = (rho * length) / cross_section_m2
            radius_m = max(1e-4, np.sqrt(cross_section_m2 / np.pi))
            l_inductance = max(
                1e-9,
                (2e-7)
                * length
                * max(1.0, (np.log(max(1.0, 2.0 * length / radius_m)) - 0.75)),
            )

            if s.z_surge is not None:
                z_surge = float(s.z_surge)
            else:
                z_surge = float(np.sqrt(r_dc**2 + (self.omega * l_inductance) ** 2))

            if not math.isfinite(z_surge) or z_surge <= 0.0:
                raise ValueError(
                    f"Segment {s.id!r} surge impedance z_surge must be > 0, got {z_surge!r}."
                )
            admittance = 1.0 / z_surge

            self.graph.add_edge(
                u,
                v,
                id=s.id,
                length_m=length,
                resistance_ohm=r_dc,
                inductance_h=l_inductance,
                impedance_ohm=z_surge,
                admittance_siemens=admittance,
            )

    def calculate_current_sharing(
        self,
        injection_node: str,
        earth_nodes: List[str],
        total_injection_current_a: float,
    ) -> Dict[str, Any]:
        i_total = _check_positive_finite_float(
            "total_injection_current_a", total_injection_current_a
        )
        _check_nonempty_str("injection_node", injection_node)
        if not isinstance(earth_nodes, list) or len(earth_nodes) == 0:
            raise ValueError("earth_nodes must be a non-empty list of node IDs.")
        for en in earth_nodes:
            _check_nonempty_str("earth_nodes item", en)

        node_list = list(self.graph.nodes())
        if not node_list:
            raise ValueError("Network graph is empty; add nodes before solving.")

        if injection_node not in self.graph:
            raise ValueError(
                f"Injection node {injection_node!r} does not exist in network."
            )

        for en in earth_nodes:
            if en not in self.graph:
                raise ValueError(
                    f"Earth node {en!r} does not exist in network."
                )

        connected_earth = [
            en for en in earth_nodes if nx.has_path(self.graph, injection_node, en)
        ]
        if not connected_earth:
            return {
                "kc_factors": {
                    d["id"]: 0.0 for _, _, d in self.graph.edges(data=True)
                },
                "segment_currents": {},
                "node_potentials": {},
                "kcl_residuals": {},
                "max_kcl_residual_a": 0.0,
                "relative_residual": 1.0,
                "converged": False,
                "condition_number_estimate": 0.0,
                "warnings": [
                    f"Injection node '{injection_node}' is galvanically isolated from earth terminations"
                ],
            }

        N = len(node_list)
        idx = {node: i for i, node in enumerate(node_list)}
        Y = lil_matrix((N, N), dtype=np.float64)
        I = np.zeros(N, dtype=np.float64)

        I[idx[injection_node]] = i_total

        for u, v, data in self.graph.edges(data=True):
            i_u, i_v = idx[u], idx[v]
            y_elem = data["admittance_siemens"]
            Y[i_u, i_u] += y_elem
            Y[i_v, i_v] += y_elem
            Y[i_u, i_v] -= y_elem
            Y[i_v, i_u] -= y_elem

        for en in connected_earth:
            e_i = idx[en]
            Y[e_i, :] = 0.0
            Y[e_i, e_i] = 1.0
            I[e_i] = 0.0

        Y_csc = Y.tocsc()
        diag_elements = np.abs(Y_csc.diagonal())
        diag_max = float(np.max(diag_elements)) if len(diag_elements) > 0 else 1.0
        diag_min = (
            float(np.min(diag_elements[diag_elements > 0]))
            if np.any(diag_elements > 0)
            else 1e-6
        )
        cond_estimate = diag_max / max(1e-12, diag_min)

        try:
            V = spsolve(Y_csc, I)
        except Exception as err:
            return {
                "kc_factors": {},
                "segment_currents": {},
                "node_potentials": {},
                "kcl_residuals": {},
                "max_kcl_residual_a": 0.0,
                "relative_residual": 1.0,
                "converged": False,
                "condition_number_estimate": float(cond_estimate),
                "warnings": [f"Sparse linear solver failed: {str(err)}"],
            }

        node_potentials = {node: float(V[idx[node]]) for node in node_list}

        kc_factors = {}
        segment_currents = {}
        for u, v, data in self.graph.edges(data=True):
            i_u, i_v = idx[u], idx[v]
            v_drop = abs(V[i_u] - V[i_v])
            i_branch = float(v_drop * data["admittance_siemens"])
            segment_currents[data["id"]] = i_branch
            kc_factors[data["id"]] = float(min(1.0, max(0.0, i_branch / i_total)))

        kcl_residuals = {}
        max_kcl_res = 0.0
        for node in node_list:
            if node in connected_earth:
                continue
            n_i = idx[node]
            sum_current = 0.0
            for neighbor in self.graph.neighbors(node):
                nb_i = idx[neighbor]
                g = self.graph[node][neighbor]["admittance_siemens"]
                sum_current += (V[n_i] - V[nb_i]) * g
            injected = i_total if node == injection_node else 0.0
            res = abs(sum_current - injected)
            kcl_residuals[node] = float(res)
            if res > max_kcl_res:
                max_kcl_res = float(res)

        total_earth_current = 0.0
        for en in connected_earth:
            e_i = idx[en]
            for neighbor in self.graph.neighbors(en):
                nb_i = idx[neighbor]
                g = self.graph[en][neighbor]["admittance_siemens"]
                total_earth_current += abs(V[nb_i] - V[e_i]) * g

        conservation_residual = abs(i_total - total_earth_current)
        rel_residual = float(conservation_residual / i_total)
        converged = bool(rel_residual < 0.02)

        warnings = [
            "Approximation: Single-frequency equivalent impedance model; unverified transient response."
        ]
        if not converged:
            warnings.append(
                f"Global current conservation residual ({rel_residual*100:.2f}%) exceeded 2% tolerance"
            )
        if max_kcl_res > (0.05 * i_total):
            warnings.append(
                f"Local KCL residual at node ({max_kcl_res:.1f} A) indicates ill-conditioned branch"
            )

        return {
            "kc_factors": kc_factors,
            "segment_currents": segment_currents,
            "node_potentials": node_potentials,
            "kcl_residuals": kcl_residuals,
            "total_earth_current_a": float(total_earth_current),
            "max_kcl_residual_a": float(max_kcl_res),
            "conservation_residual_a": float(conservation_residual),
            "relative_residual": float(rel_residual),
            "condition_number_estimate": float(cond_estimate),
            "converged": converged,
            "warnings": warnings,
        }
