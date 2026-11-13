import pytest
from aegislps_engine.nodal import NodalCurrentSolver


def test_nodal_symmetric_paths():
    solver = NodalCurrentSolver()
    nodes = [
        {"id": "n1", "x": 0, "y": 0, "z": 20, "node_type": "conductor"},
        {"id": "n2", "x": 10, "y": 0, "z": 0, "node_type": "conductor"},
        {"id": "n3", "x": -10, "y": 0, "z": 0, "node_type": "conductor"},
    ]
    segments = [
        {
            "id": "s1",
            "start_node_id": "n1",
            "end_node_id": "n2",
            "cross_section_mm2": 50,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "s2",
            "start_node_id": "n1",
            "end_node_id": "n3",
            "cross_section_mm2": 50,
            "resistivity_ohm_m": 1.72e-8,
        },
    ]
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(
        injection_node="n1",
        earth_nodes=["n2", "n3"],
        total_injection_current_a=100000.0,
    )

    assert res["converged"]
    assert res["kc_factors"]["s1"] == pytest.approx(0.5, rel=1e-12)
    assert res["kc_factors"]["s2"] == pytest.approx(0.5, rel=1e-12)
    assert res["relative_residual"] <= 1e-12


def test_nodal_asymmetric_parallel_paths():
    import math

    solver = NodalCurrentSolver()
    # Path 1 is sqrt(10^2 + 20^2) m long (100 mm2); Path 2 is sqrt(20^2 + 20^2) m long (25 mm2)
    nodes = [
        {"id": "n_top", "x": 0, "y": 0, "z": 20, "node_type": "conductor"},
        {"id": "n_earth1", "x": 0, "y": 10, "z": 0, "node_type": "conductor"},
        {"id": "n_earth2", "x": 0, "y": 20, "z": 0, "node_type": "conductor"},
    ]
    segments = [
        {
            "id": "s_low_res",
            "start_node_id": "n_top",
            "end_node_id": "n_earth1",
            "cross_section_mm2": 100,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "s_high_res",
            "start_node_id": "n_top",
            "end_node_id": "n_earth2",
            "cross_section_mm2": 25,
            "resistivity_ohm_m": 1.72e-8,
        },
    ]
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(
        injection_node="n_top",
        earth_nodes=["n_earth1", "n_earth2"],
        total_injection_current_a=100000.0,
    )

    # Hand-calculated closed-form parallel AC current divider at f = 250 kHz:
    # Z_k = R_dc,k + j * 2*pi*f * 2e-7 * l_k * (ln(2*l_k / r_k) - 0.75), kc_k = |Y_k| / |Y_1 + Y_2|
    omega = 2.0 * math.pi * 250e3
    l1, a1 = math.hypot(10.0, 20.0), 100.0e-6
    l2, a2 = math.hypot(20.0, 20.0), 25.0e-6
    r1 = math.sqrt(a1 / math.pi)
    r2 = math.sqrt(a2 / math.pi)
    y1 = 1.0 / complex(1.72e-8 * l1 / a1, omega * 2e-7 * l1 * (math.log(2.0 * l1 / r1) - 0.75))
    y2 = 1.0 / complex(1.72e-8 * l2 / a2, omega * 2e-7 * l2 * (math.log(2.0 * l2 / r2) - 0.75))
    kc_low_ref = abs(y1) / abs(y1 + y2)
    kc_high_ref = abs(y2) / abs(y1 + y2)

    assert res["converged"]
    assert res["kc_factors"]["s_low_res"] == pytest.approx(kc_low_ref, rel=1e-9)
    assert res["kc_factors"]["s_high_res"] == pytest.approx(kc_high_ref, rel=1e-9)


def test_nodal_disconnected_component():
    solver = NodalCurrentSolver()
    nodes = [
        {"id": "n_isolated", "x": 100, "y": 100, "z": 20, "node_type": "conductor"},
        {"id": "n_other", "x": 200, "y": 200, "z": 0, "node_type": "conductor"},
    ]
    segments = []  # No connection
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(
        injection_node="n_isolated",
        earth_nodes=["n_other"],
        total_injection_current_a=100000.0,
    )

    assert res["converged"] is False
    assert any("galvanically isolated" in w for w in res["warnings"])


def test_nodal_ring_and_mesh_conservation():
    solver = NodalCurrentSolver()
    # 4-corner mesh with ring conductor
    nodes = [
        {"id": "c1", "x": 0, "y": 0, "z": 15, "node_type": "conductor"},
        {"id": "c2", "x": 20, "y": 0, "z": 15, "node_type": "conductor"},
        {"id": "c3", "x": 20, "y": 10, "z": 15, "node_type": "conductor"},
        {"id": "c4", "x": 0, "y": 10, "z": 15, "node_type": "conductor"},
        {"id": "e1", "x": 0, "y": 0, "z": 0, "node_type": "conductor"},
        {"id": "e2", "x": 20, "y": 10, "z": 0, "node_type": "conductor"},
    ]
    segments = [
        {
            "id": "r1",
            "start_node_id": "c1",
            "end_node_id": "c2",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "r2",
            "start_node_id": "c2",
            "end_node_id": "c3",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "r3",
            "start_node_id": "c3",
            "end_node_id": "c4",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "r4",
            "start_node_id": "c4",
            "end_node_id": "c1",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "down1",
            "start_node_id": "c1",
            "end_node_id": "e1",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "down2",
            "start_node_id": "c3",
            "end_node_id": "e2",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
    ]
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(
        injection_node="c1",
        earth_nodes=["e1", "e2"],
        total_injection_current_a=100000.0,
    )

    # Closed-form series-parallel reduction of symmetric 20 m x 10 m roof ring between c1 and c3:
    # Two identical half-rings (Z_20 + Z_10) in parallel give Z_ring_eq = 0.5 * (Z_20 + Z_10)
    # in series with Z_down(15 m) vs direct Z_down(15 m) at c1 -> e1.
    import math

    omega = 2.0 * math.pi * 250e3
    area_m2 = 50.0e-6
    rad_m = math.sqrt(area_m2 / math.pi)

    def _z_seg(length_m: float) -> complex:
        r_dc = 1.72e-8 * length_m / area_m2
        l_ind = 2e-7 * length_m * (math.log(2.0 * length_m / rad_m) - 0.75)
        return complex(r_dc, omega * l_ind)

    z_down = _z_seg(15.0)
    z_ring_eq = 0.5 * (_z_seg(20.0) + _z_seg(10.0))
    y_branch1 = 1.0 / z_down
    y_branch2 = 1.0 / (z_ring_eq + z_down)
    kc_down1_ref = abs(y_branch1) / abs(y_branch1 + y_branch2)
    kc_down2_ref = abs(y_branch2) / abs(y_branch1 + y_branch2)

    assert res["converged"]
    assert res["kc_factors"]["down1"] == pytest.approx(kc_down1_ref, rel=1e-9)
    assert res["kc_factors"]["down2"] == pytest.approx(kc_down2_ref, rel=1e-9)
    assert res["conservation_residual_a"] <= 1e-9 * 100000.0
    assert len(res["node_potentials"]) == 6
    # Sanity check only (solver-internal diagonal-ratio diagnostic; no independent physical reference):
    assert res["condition_number_estimate"] >= 1.0


def _solve_pre_change_real_conductance(nodes, segments, injection_node, earth_nodes, i_total):
    """Reference pre-Step-3.1 real-conductance sparse solver (float64 lil_matrix + spsolve)."""
    import numpy as np
    from scipy.sparse import lil_matrix
    from scipy.sparse.linalg import spsolve

    node_ids = [n["id"] for n in nodes]
    idx = {nid: i for i, nid in enumerate(node_ids)}
    coords = {n["id"]: (float(n["x"]), float(n["y"]), float(n["z"])) for n in nodes}
    n_cnt = len(node_ids)
    G = lil_matrix((n_cnt, n_cnt), dtype=np.float64)
    rhs = np.zeros(n_cnt, dtype=np.float64)
    rhs[idx[injection_node]] = float(i_total)

    seg_g = {}
    for s in segments:
        u, v = s["start_node_id"], s["end_node_id"]
        if s.get("length") is not None:
            length = float(s["length"])
        else:
            ux, uy, uz = coords[u]
            vx, vy, vz = coords[v]
            length = float(np.sqrt((ux - vx) ** 2 + (uy - vy) ** 2 + (uz - vz) ** 2))
        if s.get("z_surge") is not None:
            r_seg = float(s["z_surge"])
        else:
            cs_m2 = float(s["cross_section_mm2"]) * 1e-6
            r_seg = (float(s["resistivity_ohm_m"]) * length) / cs_m2
        g = 1.0 / r_seg
        seg_g[s["id"]] = (u, v, g)
        iu, iv = idx[u], idx[v]
        G[iu, iu] += g
        G[iv, iv] += g
        G[iu, iv] -= g
        G[iv, iu] -= g

    for en in earth_nodes:
        ei = idx[en]
        G[ei, :] = 0.0
        G[ei, ei] = 1.0
        rhs[ei] = 0.0

    V = spsolve(G.tocsc(), rhs)
    potentials = {nid: float(V[idx[nid]]) for nid in node_ids}
    currents = {}
    kc = {}
    for sid, (u, v, g) in seg_g.items():
        i_br = float(abs(V[idx[u]] - V[idx[v]]) * g)
        currents[sid] = i_br
        kc[sid] = float(min(1.0, max(0.0, i_br / i_total)))
    return kc, currents, potentials


def test_nodal_resistive_only_matches_pre_change_within_1e12():
    """Criterion A: Resistive-only network (omega = 0 and explicit real z_surge / L = 0) matches pre-change code within 1e-12."""
    nodes = [
        {"id": "n_inj", "x": 0.0, "y": 0.0, "z": 20.0, "node_type": "air_termination"},
        {"id": "n_mid", "x": 8.0, "y": 0.0, "z": 10.0, "node_type": "down_conductor"},
        {"id": "e1", "x": 0.0, "y": 0.0, "z": 0.0, "node_type": "earth_point"},
        {"id": "e2", "x": 12.0, "y": 0.0, "z": 0.0, "node_type": "earth_point"},
    ]
    base_segments = [
        {
            "id": "s_direct",
            "start_node_id": "n_inj",
            "end_node_id": "e1",
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "s_upper",
            "start_node_id": "n_inj",
            "end_node_id": "n_mid",
            "cross_section_mm2": 35.0,
            "resistivity_ohm_m": 2.82e-8,
        },
        {
            "id": "s_lower1",
            "start_node_id": "n_mid",
            "end_node_id": "e1",
            "cross_section_mm2": 70.0,
            "resistivity_ohm_m": 1.72e-8,
        },
        {
            "id": "s_lower2",
            "start_node_id": "n_mid",
            "end_node_id": "e2",
            "cross_section_mm2": 25.0,
            "resistivity_ohm_m": 1.72e-8,
        },
    ]
    i_total = 1000.0
    ref_kc, ref_cur, ref_pot = _solve_pre_change_real_conductance(
        nodes, base_segments, "n_inj", ["e1", "e2"], i_total
    )

    # Case 1: omega = 0.0 (zero inductive reactance j*omega*L = 0)
    solver_dc = NodalCurrentSolver()
    solver_dc.omega = 0.0
    solver_dc.build_network(nodes, base_segments)
    res_dc = solver_dc.calculate_current_sharing("n_inj", ["e1", "e2"], i_total)

    for k in ref_kc:
        assert abs(res_dc["kc_factors"][k] - ref_kc[k]) <= 1e-12
        assert abs(res_dc["segment_currents"][k] - ref_cur[k]) <= 1e-12
    for nid in ref_pot:
        assert abs(res_dc["node_potentials"][nid] - ref_pot[nid]) <= 1e-12

    # Case 2: explicit real z_surge supplied (Z = z_surge + 0j, effective L = 0)
    z_surge_segments = [
        {**s, "z_surge": (idx_s + 1) * 2.5} for idx_s, s in enumerate(base_segments)
    ]
    ref_kc_z, ref_cur_z, ref_pot_z = _solve_pre_change_real_conductance(
        nodes, z_surge_segments, "n_inj", ["e1", "e2"], i_total
    )
    solver_z = NodalCurrentSolver()
    solver_z.build_network(nodes, z_surge_segments)
    res_z = solver_z.calculate_current_sharing("n_inj", ["e1", "e2"], i_total)

    for k in ref_kc_z:
        assert abs(res_z["kc_factors"][k] - ref_kc_z[k]) <= 1e-12
        assert abs(res_z["segment_currents"][k] - ref_cur_z[k]) <= 1e-12
    for nid in ref_pot_z:
        assert abs(res_z["node_potentials"][nid] - ref_pot_z[nid]) <= 1e-12


def _two_segment_inductive_parallel_fixture():
    """2-segment parallel network with distinct X/R ratios and closed-form phasor solution."""
    import numpy as np

    nodes = [
        {"id": "n_inj", "x": 0.0, "y": 0.0, "z": 10.0, "node_type": "air_termination"},
        {"id": "e1", "x": 0.0, "y": 0.0, "z": 0.0, "node_type": "earth_point"},
        {"id": "e2", "x": 10.0, "y": 0.0, "z": 0.0, "node_type": "earth_point"},
    ]
    segments = [
        {
            "id": "s1",
            "start_node_id": "n_inj",
            "end_node_id": "e1",
            "length": 10.0,
            "cross_section_mm2": 10.0,
            "resistivity_ohm_m": 2.5e-4,
        },
        {
            "id": "s2",
            "start_node_id": "n_inj",
            "end_node_id": "e2",
            "length": 100.0,
            "cross_section_mm2": 50.0,
            "resistivity_ohm_m": 1.72e-8,
        },
    ]
    omega = 2.0 * np.pi * 250e3

    def _segment_z(seg):
        length = seg["length"]
        cs_m2 = seg["cross_section_mm2"] * 1e-6
        r_dc = (seg["resistivity_ohm_m"] * length) / cs_m2
        radius_m = max(1e-4, float(np.sqrt(cs_m2 / np.pi)))
        l_ind = max(
            1e-9,
            2e-7 * length * max(1.0, float(np.log(max(1.0, 2.0 * length / radius_m)) - 0.75)),
        )
        return complex(r_dc, omega * l_ind)

    z1 = _segment_z(segments[0])
    z2 = _segment_z(segments[1])
    return nodes, segments, z1, z2


def test_nodal_inductive_parallel_closed_form():
    """Criterion B: 2-segment parallel inductive network matches closed-form phasor solution to 1e-9 relative."""
    nodes, segments, z1, z2 = _two_segment_inductive_parallel_fixture()
    i_total = 1000.0

    # Exact phasor current divider: I1 = I_tot * Z2 / (Z1 + Z2), I2 = I_tot * Z1 / (Z1 + Z2),
    # V_inj = I_tot * (Z1 * Z2) / (Z1 + Z2)
    v_inj_exact = i_total * (z1 * z2) / (z1 + z2)
    i1_exact = i_total * z2 / (z1 + z2)
    i2_exact = i_total * z1 / (z1 + z2)
    kc1_exact = min(1.0, abs(i1_exact) / i_total)
    kc2_exact = min(1.0, abs(i2_exact) / i_total)

    solver = NodalCurrentSolver(equivalent_frequency_khz=250.0)
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing("n_inj", ["e1", "e2"], i_total)

    assert res["node_potentials"]["n_inj"] == pytest.approx(abs(v_inj_exact), rel=1e-9)
    assert res["node_potentials"]["e1"] == 0.0
    assert res["node_potentials"]["e2"] == 0.0
    assert res["segment_currents"]["s1"] == pytest.approx(abs(i1_exact), rel=1e-9)
    assert res["segment_currents"]["s2"] == pytest.approx(abs(i2_exact), rel=1e-9)
    assert res["kc_factors"]["s1"] == pytest.approx(kc1_exact, rel=1e-9)
    assert res["kc_factors"]["s2"] == pytest.approx(kc2_exact, rel=1e-9)


def test_nodal_inductive_earth_phasor_conservation():
    """Criterion C: Complex phasor earth current sum conserves i_total within 1e-9 * i_total and converges."""
    nodes, segments, _, _ = _two_segment_inductive_parallel_fixture()
    i_total = 1000.0

    solver = NodalCurrentSolver(equivalent_frequency_khz=250.0)
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing("n_inj", ["e1", "e2"], i_total)

    assert res["converged"] is True
    assert res["conservation_residual_a"] <= 1e-9 * i_total
    assert res["total_earth_current_a"] == pytest.approx(i_total, rel=1e-9)

