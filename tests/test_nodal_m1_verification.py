"""Step 5.1 Part B — Independent-oracle verification of M1 (`nodal.py`).

Verifies:
1. Small 3-node, 2-branch network with known R and L at a known frequency:
   hand-written complex branch admittances y_k = 1 / (R_k + j * omega * L_k)
   and stamped 3x3 complex nodal matrix Y match the solver to rel=1e-9.
2. Solver output changes when branch phase changes at fixed |Z| (6-8-10 right
   triangle vs purely resistive 10 ohm), proving phasor behavior rather than
   magnitude-only 1 / |Z|.
3. Explicit z_surge uses 1 / (z_surge + 0j) exactly (zero imaginary part).
4. Kirchhoff current conservation holds in complex phasor form at every node
   (complex residual < 1e-9 relative to injected current) and globally at earth.
5. The experimental single-frequency (250 kHz) disclosure (not in
   IEC 62305-3:2024) remains intact in `nodal.py` and `docs/KNOWN_ISSUES.md`.
"""

import math
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

import aegislps_engine.nodal as nodal_mod
from aegislps_engine.nodal import NodalCurrentSolver

REPO_ROOT = Path(__file__).resolve().parent.parent


def _hand_branch_impedance(
    length_m: float, cross_section_mm2: float, rho_ohm_m: float, freq_khz: float
) -> complex:
    """Hand-written closed-form branch impedance Z = R_dc + j * 2*pi*f * L_ind."""
    area_m2 = cross_section_mm2 * 1e-6
    r_dc = (rho_ohm_m * length_m) / area_m2
    radius_m = max(1e-4, math.sqrt(area_m2 / math.pi))
    l_ind = max(
        1e-9,
        2e-7 * length_m * max(1.0, math.log(max(1.0, (2.0 * length_m) / radius_m)) - 0.75),
    )
    return complex(r_dc, 2.0 * math.pi * (freq_khz * 1e3) * l_ind)


def test_m1_3node_2branch_complex_admittance_and_stamped_y_matrix():
    """Part B.1: 3-node, 2-branch network complex admittance & Y matrix match hand formula to rel=1e-9."""
    freq_khz = 250.0
    i_inj = 100_000.0

    # 3 nodes: n1 (0, 0, 12) -> n2 (0, 0, 4) -> e1 (6, 0, 0)
    # Branch b12: length = 8.0 m, A = 50 mm2, rho = 1.72e-8 ohm.m (copper)
    # Branch b23: length = hypot(6, 4) = sqrt(52) m, A = 35 mm2, rho = 7.0e-7 ohm.m (stainless steel)
    nodes = [
        {"id": "n1", "x": 0.0, "y": 0.0, "z": 12.0, "node_type": "conductor"},
        {"id": "n2", "x": 0.0, "y": 0.0, "z": 4.0, "node_type": "conductor"},
        {"id": "e1", "x": 6.0, "y": 0.0, "z": 0.0, "node_type": "earth_point"},
    ]
    segments = [
        {
            "id": "b12",
            "start_node_id": "n1",
            "end_node_id": "n2",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "b23",
            "start_node_id": "n2",
            "end_node_id": "e1",
            "cross_section_mm2": 35.0,
            "resistivity_ohm_m": 7.0e-7,
        },
    ]

    z12_ref = _hand_branch_impedance(8.0, 50.0, 1.72e-8, freq_khz)
    z23_ref = _hand_branch_impedance(math.hypot(6.0, 4.0), 35.0, 7.0e-7, freq_khz)
    y12_ref = 1.0 / z12_ref
    y23_ref = 1.0 / z23_ref

    # Expected 3x3 Dirichlet-stamped complex admittance matrix for node order [n1, n2, e1]:
    y_mat_expected = np.array(
        [
            [y12_ref, -y12_ref, 0.0 + 0.0j],
            [-y12_ref, y12_ref + y23_ref, -y23_ref],
            [0.0 + 0.0j, 0.0 + 0.0j, 1.0 + 0.0j],
        ],
        dtype=np.complex128,
    )

    solver = NodalCurrentSolver(equivalent_frequency_khz=freq_khz)
    solver.build_network(nodes, segments)

    edge_12 = solver.graph.get_edge_data("n1", "n2")
    edge_23 = solver.graph.get_edge_data("n2", "e1")
    assert edge_12 is not None and edge_23 is not None

    # Verify complex branch admittances match hand formula to rel=1e-9 (real & imag parts nonzero):
    assert edge_12["admittance_siemens"].imag < 0.0
    assert edge_23["admittance_siemens"].imag < 0.0
    assert abs(edge_12["admittance_siemens"] - y12_ref) <= 1e-9 * abs(y12_ref)
    assert abs(edge_23["admittance_siemens"] - y23_ref) <= 1e-9 * abs(y23_ref)

    # Intercept spsolve inside calculate_current_sharing to inspect the exact Y matrix built by solver:
    captured = {}
    orig_spsolve = nodal_mod.spsolve

    def _recording_spsolve(a_mat, b_vec):
        captured["Y_dense"] = a_mat.toarray()
        captured["I_rhs"] = np.array(b_vec, copy=True)
        return orig_spsolve(a_mat, b_vec)

    nodal_mod.spsolve = _recording_spsolve
    try:
        res = solver.calculate_current_sharing(
            injection_node="n1",
            earth_nodes=["e1"],
            total_injection_current_a=i_inj,
        )
    finally:
        nodal_mod.spsolve = orig_spsolve

    assert res["converged"] is True
    y_actual = captured["Y_dense"]
    assert y_actual.dtype == np.complex128
    assert y_actual.shape == (3, 3)

    for r_idx in range(3):
        for c_idx in range(3):
            exp_val = y_mat_expected[r_idx, c_idx]
            act_val = y_actual[r_idx, c_idx]
            if exp_val == 0.0:
                assert abs(act_val) <= 1e-15
            else:
                assert abs(act_val - exp_val) <= 1e-9 * abs(exp_val)

    # Also verify node potential phasor magnitudes against hand series impedance Z_total = Z_12 + Z_23:
    v_n2_ref = complex(i_inj, 0.0) * z23_ref
    v_n1_ref = complex(i_inj, 0.0) * (z12_ref + z23_ref)
    assert res["node_potentials"]["n1"] == pytest.approx(abs(v_n1_ref), rel=1e-9)
    assert res["node_potentials"]["n2"] == pytest.approx(abs(v_n2_ref), rel=1e-9)
    assert res["node_potentials"]["e1"] == 0.0


def test_m1_phase_change_alters_solution_at_identical_branch_impedance_magnitude():
    """Part B.2: Changing branch phase while holding |Z| = 10 ohm constant changes kc and |V|."""
    # Construct Branch B with exact 6-8-10 right-triangle impedance Z_B = 6 + j*8 ohm (|Z_B| = 10 ohm):
    # Length l = 10 m, cross-section A = 50 mm2 -> r = sqrt(50e-6 / pi),
    # L_ind = 2e-7 * 10 * (ln(20 / r) - 0.75).
    # Pick rho so R_dc = rho * l / A = 6.0 ohm, and f_khz so 2*pi*(f_khz*1e3)*L_ind = 8.0 ohm.
    length_m = 10.0
    area_mm2 = 50.0
    area_m2 = area_mm2 * 1e-6
    radius_m = math.sqrt(area_m2 / math.pi)
    l_ind = 2e-7 * length_m * (math.log(2.0 * length_m / radius_m) - 0.75)
    freq_khz = (8.0 / (2.0 * math.pi * l_ind)) * 1e-3
    rho_for_6_ohm = 6.0 * area_m2 / length_m

    nodes = [
        {"id": "n_inj", "x": 0.0, "y": 0.0, "z": 10.0, "node_type": "conductor"},
        {"id": "e1", "x": 0.0, "y": 0.0, "z": 0.0, "node_type": "earth_point"},
        {"id": "e2", "x": 0.0, "y": 0.0, "z": 0.0, "node_type": "earth_point"},
    ]

    # Network 1 (zero phase difference): Z_1 = 10 + j0, Z_2 = 10 + j0 (|Z_1| = |Z_2| = 10 ohm)
    solver_in_phase = NodalCurrentSolver(equivalent_frequency_khz=freq_khz)
    solver_in_phase.build_network(
        nodes,
        [
            {
                "id": "b1",
                "start_node_id": "n_inj",
                "end_node_id": "e1",
                "cross_section_mm2": area_mm2,
                "resistivity_ohm_m": 1.72e-8,
                "z_surge": 10.0,
            },
            {
                "id": "b2",
                "start_node_id": "n_inj",
                "end_node_id": "e2",
                "cross_section_mm2": area_mm2,
                "resistivity_ohm_m": 1.72e-8,
                "z_surge": 10.0,
            },
        ],
    )
    res_in_phase = solver_in_phase.calculate_current_sharing("n_inj", ["e1", "e2"], 100_000.0)

    # Network 2 (53.13 deg phase difference at SAME |Z_1| = |Z_2| = 10 ohm):
    # Z_1 = 10 + j0, Z_2 = 6 + j8 -> Y_1 = 0.1, Y_2 = 0.06 - j0.08,
    # Y_1 + Y_2 = 0.16 - j0.08 -> |Y_1 + Y_2| = sqrt(0.032) = 0.1788854382 S.
    # Phasor solution: |V_inj| = 100000 / sqrt(0.032) = 559016.994375 V,
    # kc_1 = |Y_1| / |Y_1 + Y_2| = 1 / sqrt(3.2) = 0.559016994375,
    # kc_2 = |Y_2| / |Y_1 + Y_2| = 1 / sqrt(3.2) = 0.559016994375.
    solver_out_of_phase = NodalCurrentSolver(equivalent_frequency_khz=freq_khz)
    solver_out_of_phase.build_network(
        nodes,
        [
            {
                "id": "b1",
                "start_node_id": "n_inj",
                "end_node_id": "e1",
                "cross_section_mm2": area_mm2,
                "resistivity_ohm_m": 1.72e-8,
                "z_surge": 10.0,
            },
            {
                "id": "b2",
                "start_node_id": "n_inj",
                "end_node_id": "e2",
                "cross_section_mm2": area_mm2,
                "resistivity_ohm_m": rho_for_6_ohm,
            },
        ],
    )
    res_out_of_phase = solver_out_of_phase.calculate_current_sharing(
        "n_inj", ["e1", "e2"], 100_000.0
    )

    # Confirm both branches in Network 2 truly have |Z| == 10.0 ohm:
    e_b1 = solver_out_of_phase.graph.get_edge_data("n_inj", "e1")
    e_b2 = solver_out_of_phase.graph.get_edge_data("n_inj", "e2")
    assert e_b1["impedance_magnitude_ohm"] == pytest.approx(10.0, rel=1e-12)
    assert e_b2["impedance_magnitude_ohm"] == pytest.approx(10.0, rel=1e-12)

    expected_kc_phasor = 1.0 / math.sqrt(3.2)
    expected_v_phasor = 100_000.0 / math.sqrt(0.032)

    assert res_in_phase["kc_factors"]["b1"] == pytest.approx(0.5, rel=1e-9)
    assert res_in_phase["node_potentials"]["n_inj"] == pytest.approx(500_000.0, rel=1e-9)

    assert res_out_of_phase["kc_factors"]["b1"] == pytest.approx(expected_kc_phasor, rel=1e-9)
    assert res_out_of_phase["kc_factors"]["b2"] == pytest.approx(expected_kc_phasor, rel=1e-9)
    assert res_out_of_phase["node_potentials"]["n_inj"] == pytest.approx(
        expected_v_phasor, rel=1e-9
    )
    assert res_out_of_phase["kc_factors"]["b1"] != pytest.approx(
        res_in_phase["kc_factors"]["b1"], rel=1e-2
    )


@pytest.mark.parametrize("z_val", [0.5, 25.0, 40.0, 125.0])
def test_m1_explicit_z_surge_uses_exact_one_over_z_surge_plus_0j(z_val: float):
    """Part B.3: Explicit z_surge uses 1 / (z_surge + 0j) with exact zero imaginary part."""
    solver = NodalCurrentSolver(equivalent_frequency_khz=250.0)
    solver.build_network(
        [
            {"id": "n_a", "x": 0.0, "y": 0.0, "z": 15.0, "node_type": "conductor"},
            {"id": "n_b", "x": 3.0, "y": 4.0, "z": 0.0, "node_type": "earth_point"},
        ],
        [
            {
                "id": "seg_z",
                "start_node_id": "n_a",
                "end_node_id": "n_b",
                "cross_section_mm2": 50.0,
                "resistivity_ohm_m": 1.72e-8,
                "z_surge": z_val,
            }
        ],
    )

    edge = solver.graph.get_edge_data("n_a", "n_b")
    expected_z = complex(z_val, 0.0)
    expected_y = complex(1.0) / expected_z

    assert edge["impedance_ohm"] == expected_z
    assert edge["impedance_ohm"].imag == 0.0
    assert edge["admittance_siemens"] == expected_y
    assert edge["admittance_siemens"].imag == 0.0


def test_m1_kirchhoff_current_conservation_at_each_node_phasor():
    """Part B.4: Complex phasor KCL holds at every node (< 1e-9 relative residual)."""
    freq_khz = 250.0
    i_total = 100_000.0

    # Non-symmetric 5-node bridged network with mixed copper, steel, and explicit z_surge branches:
    nodes = [
        {"id": "n_inj", "x": 0.0, "y": 0.0, "z": 16.0, "node_type": "conductor"},
        {"id": "n_mid1", "x": 8.0, "y": 0.0, "z": 10.0, "node_type": "conductor"},
        {"id": "n_mid2", "x": 0.0, "y": 6.0, "z": 9.0, "node_type": "conductor"},
        {"id": "e1", "x": 8.0, "y": 0.0, "z": 0.0, "node_type": "earth_point"},
        {"id": "e2", "x": 0.0, "y": 6.0, "z": 0.0, "node_type": "earth_point"},
    ]
    segments = [
        {
            "id": "s_inj_1",
            "start_node_id": "n_inj",
            "end_node_id": "n_mid1",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "s_inj_2",
            "start_node_id": "n_inj",
            "end_node_id": "n_mid2",
            "cross_section_mm2": 35.0,
            "resistivity_ohm_m": 7.0e-7,
        },
        {
            "id": "s_bridge",
            "start_node_id": "n_mid1",
            "end_node_id": "n_mid2",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
            "z_surge": 2.5,
        },
        {
            "id": "s_down_1",
            "start_node_id": "n_mid1",
            "end_node_id": "e1",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "s_down_2",
            "start_node_id": "n_mid2",
            "end_node_id": "e2",
            "cross_section_mm2": 70.0,
            "resistivity_ohm_m": 2.82e-8,
        },
    ]

    solver = NodalCurrentSolver(equivalent_frequency_khz=freq_khz)
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing("n_inj", ["e1", "e2"], i_total)
    assert res["converged"] is True

    # Independently solve the true complex nodal system Y_true * V_phasor = I_ext
    # using hand-computed complex admittances, and verify both node-by-node phasor KCL
    # and agreement with solver outputs to rel=1e-9:
    node_ids = [n["id"] for n in nodes]
    idx = {nid: k for k, nid in enumerate(node_ids)}
    coords = {n["id"]: (n["x"], n["y"], n["z"]) for n in nodes}
    y_true = lil_matrix((len(node_ids), len(node_ids)), dtype=np.complex128)
    rhs = np.zeros(len(node_ids), dtype=np.complex128)
    rhs[idx["n_inj"]] = complex(i_total, 0.0)

    hand_y_by_seg = {}
    for seg in segments:
        u, v = seg["start_node_id"], seg["end_node_id"]
        if "z_surge" in seg:
            y_seg = complex(1.0) / complex(seg["z_surge"], 0.0)
        else:
            p1, p2 = coords[u], coords[v]
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
            y_seg = 1.0 / _hand_branch_impedance(
                dist, seg["cross_section_mm2"], seg["resistivity_ohm_m"], freq_khz
            )
        hand_y_by_seg[seg["id"]] = (u, v, y_seg)
        iu, iv = idx[u], idx[v]
        y_true[iu, iu] += y_seg
        y_true[iv, iv] += y_seg
        y_true[iu, iv] -= y_seg
        y_true[iv, iu] -= y_seg

    for en in ("e1", "e2"):
        ie = idx[en]
        y_true[ie, :] = 0.0
        y_true[ie, ie] = 1.0 + 0.0j
        rhs[ie] = 0.0 + 0.0j

    v_phasor = np.atleast_1d(spsolve(y_true.tocsc(), rhs))

    # 1. Solver potentials & currents must match complex phasor solution to rel=1e-9:
    for nid in node_ids:
        exp_mag = abs(v_phasor[idx[nid]])
        if exp_mag == 0.0:
            assert res["node_potentials"][nid] == 0.0
        else:
            assert res["node_potentials"][nid] == pytest.approx(exp_mag, rel=1e-9)

    for seg_id, (u, v, y_seg) in hand_y_by_seg.items():
        i_phasor = (v_phasor[idx[u]] - v_phasor[idx[v]]) * y_seg
        assert res["segment_currents"][seg_id] == pytest.approx(abs(i_phasor), rel=1e-9)

    # 2. Complex phasor KCL at every non-earth node (and solver-reported kcl_residuals):
    for nid in ("n_inj", "n_mid1", "n_mid2"):
        net_out = 0.0 + 0.0j
        for _, (u, v, y_seg) in hand_y_by_seg.items():
            if u == nid:
                net_out += (v_phasor[idx[u]] - v_phasor[idx[v]]) * y_seg
            elif v == nid:
                net_out += (v_phasor[idx[v]] - v_phasor[idx[u]]) * y_seg
        i_injected = complex(i_total, 0.0) if nid == "n_inj" else 0.0 + 0.0j
        complex_kcl_residual = abs(net_out - i_injected)
        assert complex_kcl_residual / i_total < 1e-9
        assert res["kcl_residuals"][nid] / i_total < 1e-9

    # 3. Phasor current entering all earth nodes sums to I_total + 0j (< 1e-9 relative):
    earth_phasor_sum = 0.0 + 0.0j
    for en in ("e1", "e2"):
        for _, (u, v, y_seg) in hand_y_by_seg.items():
            if v == en:
                earth_phasor_sum += (v_phasor[idx[u]] - v_phasor[idx[en]]) * y_seg
            elif u == en:
                earth_phasor_sum += (v_phasor[idx[v]] - v_phasor[idx[en]]) * y_seg
    assert abs(earth_phasor_sum - complex(i_total, 0.0)) / i_total < 1e-9
    assert res["conservation_residual_a"] / i_total < 1e-9


def test_m1_single_frequency_experimental_note_unchanged():
    """Part B.5: Experimental single-frequency note (not in IEC 62305-3:2024) stays intact."""
    class_doc = NodalCurrentSolver.__doc__ or ""
    assert "Experimental, unverified; not in IEC 62305-3:2024" in class_doc
    assert "single-frequency approximation" in class_doc

    known_issues = (REPO_ROOT / "docs" / "KNOWN_ISSUES.md").read_text(encoding="utf-8")
    m1_lines = [line for line in known_issues.splitlines() if line.startswith("| M1 |")]
    assert len(m1_lines) == 1
    assert "250 kHz" in m1_lines[0]
    assert "experimental" in m1_lines[0].lower()
    assert "IEC 62305-3:2024" in m1_lines[0]
