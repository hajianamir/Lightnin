import networkx as nx
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from typing import Dict, List, Tuple

class NodalCurrentSolver:
    """
    Solves conductor network currents and calculates current-sharing factors (kc).
    Uses NetworkX for topology management and SciPy sparse linear algebra for conductance system Y * V = I.
    """
    def __init__(self):
        self.graph = nx.Graph()

    def build_network(self, nodes: List[Dict], segments: List[Dict]):
        self.graph.clear()
        for n in nodes:
            self.graph.add_node(n["id"], x=n["x"], y=n["y"], z=n["z"], type=n.get("node_type", "conductor"))
        for s in segments:
            u, v = s["start_node_id"], s["end_node_id"]
            # Conductance G = A / (rho * L)
            length = max(0.1, np.sqrt((self.graph.nodes[u]['x'] - self.graph.nodes[v]['x'])**2 +
                                      (self.graph.nodes[u]['y'] - self.graph.nodes[v]['y'])**2 +
                                      (self.graph.nodes[u]['z'] - self.graph.nodes[v]['z'])**2))
            cross_section = s.get("cross_section_mm2", 50.0) * 1e-6 # m2
            rho = 1.72e-8 # copper resistivity
            resistance = (rho * length) / cross_section
            conductance = 1.0 / max(1e-6, resistance)
            self.graph.add_edge(u, v, id=s["id"], weight=conductance, length=length)

    def calculate_current_sharing(self, injection_node: str, earth_nodes: List[str]) -> Dict[str, float]:
        node_list = list(self.graph.nodes())
        if injection_node not in node_list or not earth_nodes:
            # Fallback to simplified kc if network boundary conditions incomplete
            return {edge_data["id"]: 1.0 / max(1, len(self.graph.edges())) for _, _, edge_data in self.graph.edges(data=True)}

        idx = {node: i for i, node in enumerate(node_list)}
        N = len(node_list)
        Y = lil_matrix((N, N))
        I = np.zeros(N)

        # Inject total lightning current = 100 kA (reference)
        I[idx[injection_node]] = 100000.0

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

        V = spsolve(Y.tocsr(), I)

        kc_factors = {}
        total_injected = 100000.0
        for u, v, data in self.graph.edges(data=True):
            i_u, i_v = idx[u], idx[v]
            v_diff = abs(V[i_u] - V[i_v])
            i_seg = v_diff * data["weight"]
            kc_factors[data["id"]] = min(1.0, max(0.05, i_seg / total_injected))

        return kc_factors
