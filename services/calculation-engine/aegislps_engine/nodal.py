import networkx as nx
import numpy as np
from scipy.sparse import lil_matrix, csc_matrix
from scipy.sparse.linalg import spsolve
from typing import Dict, List, Tuple, Any, Optional

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
    def __init__(self, equivalent_frequency_khz: float = 250.0):
        self.freq_hz = equivalent_frequency_khz * 1e3
        self.omega = 2.0 * np.pi * self.freq_hz
        self.graph = nx.Graph()

    def build_network(self, nodes: List[Dict], segments: List[Dict]):
        self.graph.clear()
        for n in nodes:
            self.graph.add_node(
                n["id"],
                x=float(n["x"]),
                y=float(n["y"]),
                z=float(n["z"]),
                node_type=n.get("node_type", "conductor")
            )

        for s in segments:
            u, v = s["start_node_id"], s["end_node_id"]
            if u not in self.graph or v not in self.graph:
                continue

            dx = self.graph.nodes[u]['x'] - self.graph.nodes[v]['x']
            dy = self.graph.nodes[u]['y'] - self.graph.nodes[v]['y']
            dz = self.graph.nodes[u]['z'] - self.graph.nodes[v]['z']
            length = float(np.sqrt(dx**2 + dy**2 + dz**2))

            if length < 1e-4:
                continue

            cross_section_mm2 = float(s.get("cross_section_mm2", 50.0))
            cross_section_m2 = max(1e-12, cross_section_mm2 * 1e-6)
            rho = float(s.get("resistivity_ohm_m", 1.72e-8))

            r_dc = (rho * length) / cross_section_m2
            radius_m = max(1e-4, np.sqrt(cross_section_m2 / np.pi))
            l_inductance = max(1e-9, (2e-7) * length * max(1.0, (np.log(max(1.0, 2.0 * length / radius_m)) - 0.75)))

            z_surge = float(np.sqrt(r_dc**2 + (self.omega * l_inductance)**2))
            admittance = 1.0 / max(1e-4, z_surge)

            self.graph.add_edge(
                u, v,
                id=s["id"],
                length_m=length,
                resistance_ohm=r_dc,
                inductance_h=l_inductance,
                impedance_ohm=z_surge,
                admittance_siemens=admittance
            )

    def calculate_current_sharing(
        self,
        injection_node: str,
        earth_nodes: List[str],
        total_injection_current_a: float = 100000.0
    ) -> Dict[str, Any]:
        node_list = list(self.graph.nodes())
        if not node_list:
            return {
                "kc_factors": {},
                "segment_currents": {},
                "node_potentials": {},
                "kcl_residuals": {},
                "max_kcl_residual_a": 0.0,
                "relative_residual": 1.0,
                "converged": False,
                "condition_number_estimate": 0.0,
                "warnings": ["Empty network graph"]
            }

        if injection_node not in node_list:
            return {
                "kc_factors": {d["id"]: 0.0 for _, _, d in self.graph.edges(data=True)},
                "segment_currents": {},
                "node_potentials": {},
                "kcl_residuals": {},
                "max_kcl_residual_a": 0.0,
                "relative_residual": 1.0,
                "converged": False,
                "condition_number_estimate": 0.0,
                "warnings": [f"Injection node '{injection_node}' does not exist in network"]
            }

        valid_earth = [en for en in earth_nodes if en in self.graph]
        if not valid_earth:
            return {
                "kc_factors": {d["id"]: 0.0 for _, _, d in self.graph.edges(data=True)},
                "segment_currents": {},
                "node_potentials": {},
                "kcl_residuals": {},
                "max_kcl_residual_a": 0.0,
                "relative_residual": 1.0,
                "converged": False,
                "condition_number_estimate": 0.0,
                "warnings": ["No valid earth grounding nodes specified"]
            }

        connected_earth = [en for en in valid_earth if nx.has_path(self.graph, injection_node, en)]
        if not connected_earth:
            return {
                "kc_factors": {d["id"]: 0.0 for _, _, d in self.graph.edges(data=True)},
                "segment_currents": {},
                "node_potentials": {},
                "kcl_residuals": {},
                "max_kcl_residual_a": 0.0,
                "relative_residual": 1.0,
                "converged": False,
                "condition_number_estimate": 0.0,
                "warnings": [f"Injection node '{injection_node}' is galvanically isolated from earth terminations"]
            }

        N = len(node_list)
        idx = {node: i for i, node in enumerate(node_list)}
        Y = lil_matrix((N, N), dtype=np.float64)
        I = np.zeros(N, dtype=np.float64)

        I[idx[injection_node]] = total_injection_current_a

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
        diag_min = float(np.min(diag_elements[diag_elements > 0])) if np.any(diag_elements > 0) else 1e-6
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
                "warnings": [f"Sparse linear solver failed: {str(err)}"]
            }

        node_potentials = {node: float(V[idx[node]]) for node in node_list}

        kc_factors = {}
        segment_currents = {}
        for u, v, data in self.graph.edges(data=True):
            i_u, i_v = idx[u], idx[v]
            v_drop = abs(V[i_u] - V[i_v])
            i_branch = float(v_drop * data["admittance_siemens"])
            segment_currents[data["id"]] = i_branch
            kc_factors[data["id"]] = float(min(1.0, max(0.0, i_branch / max(1.0, total_injection_current_a))))

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
            injected = total_injection_current_a if node == injection_node else 0.0
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

        conservation_residual = abs(total_injection_current_a - total_earth_current)
        rel_residual = float(conservation_residual / max(1.0, total_injection_current_a))
        converged = bool(rel_residual < 0.02)

        warnings = ["Approximation: Single-frequency equivalent impedance model; unverified transient response."]
        if not converged:
            warnings.append(f"Global current conservation residual ({rel_residual*100:.2f}%) exceeded 2% tolerance")
        if max_kcl_res > (0.05 * total_injection_current_a):
            warnings.append(f"Local KCL residual at node ({max_kcl_res:.1f} A) indicates ill-conditioned branch")

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
            "warnings": warnings
        }
