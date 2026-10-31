import pytest
from aegislps_engine.nodal import NodalCurrentSolver

def test_nodal_symmetric_paths():
    solver = NodalCurrentSolver()
    nodes = [
        {"id": "n1", "x": 0, "y": 0, "z": 20},
        {"id": "n2", "x": 10, "y": 0, "z": 0},
        {"id": "n3", "x": -10, "y": 0, "z": 0}
    ]
    segments = [
        {"id": "s1", "start_node_id": "n1", "end_node_id": "n2", "cross_section_mm2": 50},
        {"id": "s2", "start_node_id": "n1", "end_node_id": "n3", "cross_section_mm2": 50}
    ]
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(injection_node="n1", earth_nodes=["n2", "n3"])

    assert res["converged"]
    assert pytest.approx(res["kc_factors"]["s1"], 0.05) == 0.5
    assert pytest.approx(res["kc_factors"]["s2"], 0.05) == 0.5
    assert res["relative_residual"] < 0.01

def test_nodal_asymmetric_parallel_paths():
    solver = NodalCurrentSolver()
    # Path 1 is 10m long, Path 2 is 20m long
    nodes = [
        {"id": "n_top", "x": 0, "y": 0, "z": 20},
        {"id": "n_earth1", "x": 0, "y": 10, "z": 0},
        {"id": "n_earth2", "x": 0, "y": 20, "z": 0}
    ]
    # Path 2 has double the resistance because of smaller cross-section
    segments = [
        {"id": "s_low_res", "start_node_id": "n_top", "end_node_id": "n_earth1", "cross_section_mm2": 100},
        {"id": "s_high_res", "start_node_id": "n_top", "end_node_id": "n_earth2", "cross_section_mm2": 25}
    ]
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(injection_node="n_top", earth_nodes=["n_earth1", "n_earth2"])

    assert res["converged"]
    # Lower resistance branch carries more current
    assert res["kc_factors"]["s_low_res"] > res["kc_factors"]["s_high_res"]

def test_nodal_disconnected_component():
    solver = NodalCurrentSolver()
    nodes = [
        {"id": "n_isolated", "x": 100, "y": 100, "z": 20},
        {"id": "n_other", "x": 200, "y": 200, "z": 0}
    ]
    segments = [] # No connection
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(injection_node="n_isolated", earth_nodes=["n_other"])

    assert res["converged"] is False
    assert len(res["warnings"]) > 0

def test_nodal_ring_and_mesh_conservation():
    solver = NodalCurrentSolver()
    # 4-corner mesh with ring conductor
    nodes = [
        {"id": "c1", "x": 0, "y": 0, "z": 15},
        {"id": "c2", "x": 20, "y": 0, "z": 15},
        {"id": "c3", "x": 20, "y": 10, "z": 15},
        {"id": "c4", "x": 0, "y": 10, "z": 15},
        {"id": "e1", "x": 0, "y": 0, "z": 0},
        {"id": "e2", "x": 20, "y": 10, "z": 0}
    ]
    segments = [
        {"id": "r1", "start_node_id": "c1", "end_node_id": "c2"},
        {"id": "r2", "start_node_id": "c2", "end_node_id": "c3"},
        {"id": "r3", "start_node_id": "c3", "end_node_id": "c4"},
        {"id": "r4", "start_node_id": "c4", "end_node_id": "c1"},
        {"id": "down1", "start_node_id": "c1", "end_node_id": "e1"},
        {"id": "down2", "start_node_id": "c3", "end_node_id": "e2"}
    ]
    solver.build_network(nodes, segments)
    res = solver.calculate_current_sharing(injection_node="c1", earth_nodes=["e1", "e2"])

    assert res["converged"]
    assert "down1" in res["kc_factors"]
    assert "down2" in res["kc_factors"]
    assert res["balance_residual"] >= 0.0
