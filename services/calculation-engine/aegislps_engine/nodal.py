import networkx as nx
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from typing import Dict, List, Tuple, Any

class NodalCurrentSolver:
    """
    Solves conductor network currents and calculates current-sharing factors (kc).
    Uses NetworkX for topology management and SciPy sparse linear algebra for conductance system Y * V = I.
    Handles disconnected graphs, multiple injection points, and current conservation residual checks.
    """
    def __init__(self):
        self.graph = nx.Graph()

    def build_network(self, nodes: List[Dict], segments: List[Dict]):
        self.graph.clear()
        for n in nodes:
            self.graph.add_node(n["id"], x=n["x"], y=n["y"], z=n["z"], type=n.get("node_type", "conductor"))
        for s in segments:
            u, v = s["start_node_id"], s["end_node_id"]
            if u not in self.graph or v not in self.graph:
                continue
            dx = self.graph.nodes[u]['x'] - self.graph.nodes[v]['x']
            dy = self.graph.nodes[u]['y'] - self.graph.nodes[v]['y']
            dz = self.graph.nodes[u]['z'] - self.graph.nodes[v]['z']
            raw_len = np.sqrt(dx**2 + dy**2 + dz**2)
            length = max(0.01, float(raw_len))
            cross_section = s.get("cross_section_mm2", 50.0) * 1e-6 # m2
            rho = s.get("resistivity_ohm_m", 1.72e-8) # copper default
            resistance = (rho * length) / max(1e-12, cross_section)
            conductance = 1.0 / max(1e-6, resistance)
            self.graph.add_edge(u, v, id=s["id"], weight=conductance, length=length, resistance=resistance)

    def calculate_current_sharing(
        self,
        injection_node: str,
        earth_nodes: List[str],
        total_injection_current_a: float = 100000.0
    ) -> Dict[str, Any]:
        node_list = list(self.graph.nodes())
        if not node_list:
            return {"kc_factors": {}, "residuals": {}, "converged": False, "warnings": ["Empty network"]}

        if injection_node not in node_list or not earth_nodes:
            fallback_kc = {data["id"]: 1.0 / max(1, len(self.graph.edges())) for _, _, data in self.graph.edges(data=True)}
            return {
                "kc_factors": fallback_kc,
                "residuals": {},
                "converged": False,
                "warnings": ["Injection node or earth nodes not found in graph topology"]
            }

        # Check connectivity: find connected component containing injection_node
        if not nx.has_path(self.graph, injection_node, earth_nodes[0]):
            connected_earth = [en for en in earth_nodes if en in self.graph and nx.has_path(self.graph, injection_node, en)]
            if not connected_earth:
                return {
                    "kc_factors": {data["id"]: 0.0 for _, _, data in self.graph.edges(data=True)},
                    "residuals": {},
                    "converged": False,
                    "warnings": ["Injection node is disconnected from all earth points"]
                }
            earth_nodes = connected_earth

        idx = {node: i for i, node in enumerate(node_list)}
        N = len(node_list)
        Y = lil_matrix((N, N))
        I = np.zeros(N)

        I[idx[injection_node]] = total_injection_current_a

        for u, v, data in self.graph.edges(data=True):
            i_u, i_v = idx[u], idx[v]
            g = data["weight"]
            Y[i_u, i_u] += g
            Y[i_v, i_v] += g
            Y[i_u, i_v] -= g
            Y[i_v, i_u] -= g

        # Ground boundary conditions V = 0 at earth_nodes
        for en in earth_nodes:
            if en in idx:
                e_i = idx[en]
                Y[e_i, :] = 0
                Y[e_i, e_i] = 1.0
                I[e_i] = 0.0

        try:
            V = spsolve(Y.tocsr(), I)
        except Exception as e:
            return {
                "kc_factors": {},
                "residuals": {},
                "converged": False,
                "warnings": [f"Matrix solver failed: {str(e)}"]
            }

        kc_factors = {}
        segment_currents = {}
        for u, v, data in self.graph.edges(data=True):
            i_u, i_v = idx[u], idx[v]
            v_diff = abs(V[i_u] - V[i_v])
            i_seg = v_diff * data["weight"]
            segment_currents[data["id"]] = float(i_seg)
            # kc factor ratio of total injected current
            kc_factors[data["id"]] = float(min(1.0, max(0.0, i_seg / total_injection_current_a)))

        # Residual & Conservation check
        total_earth_current = 0.0
        for en in earth_nodes:
            e_i = idx[en]
            # sum currents entering earth node
            for neighbor in self.graph.neighbors(en):
                n_i = idx[neighbor]
                g = self.graph[en][neighbor]["weight"]
                total_earth_current += abs(V[n_i] - V[e_i]) * g

        balance_residual = abs(total_injection_current_a - total_earth_current)
        relative_residual = balance_residual / max(1.0, total_injection_current_a)
        converged = bool(relative_residual < 0.05) # 5% balance tolerance

        return {
            "kc_factors": kc_factors,
            "segment_currents": segment_currents,
            "total_earth_current": float(total_earth_current),
            "balance_residual": float(balance_residual),
            "relative_residual": float(relative_residual),
            "converged": converged,
            "warnings": [] if converged else ["Current conservation residual exceeded 5% tolerance"]
        }
