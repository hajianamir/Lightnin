import pytest
from aegislps_domain.models import Project, Building, ConductorNode, SeparationPoint, CalculationStatus
from aegislps_standards.repository import StandardsRepository
from aegislps_engine.separation import SeparationDistanceEngine

def test_simplified_separation_distance_class_I():
    repo = StandardsRepository()
    engine = SeparationDistanceEngine(repo)

    proj = Project(
        name="Ref Case 1",
        lps_class="I",
        building=Building(length_m=20, width_m=10, height_m=15),
        nodes=[ConductorNode(id="n1", x=0, y=0, z=15)],
        segments=[],
        separation_points=[
            SeparationPoint(
                id="sp1",
                name="Rooftop Antenna",
                x=1, y=1, z=15,
                associated_node_id="n1",
                insulation_medium="air",
                physical_distance_m=1.5
            )
        ]
    )

    results = engine.calculate_project(proj)
    assert len(results) == 1
    res = results[0]

    assert pytest.approx(res.required_distance_s_m, 0.001) == 1.200
    assert res.pass_compliance is True
    assert pytest.approx(res.safety_margin_m, 0.001) == 0.300
    assert res.status == CalculationStatus.CALCULATED

def test_simplified_separation_distance_class_III_solid_medium():
    repo = StandardsRepository()
    engine = SeparationDistanceEngine(repo)

    proj = Project(
        name="Ref Case 2",
        lps_class="III",
        building=Building(length_m=30, width_m=20, height_m=20),
        nodes=[ConductorNode(id="n1", x=0, y=0, z=20)],
        segments=[{"start_node_id": "n1", "end_node_id": "n2"}, {"start_node_id": "n1", "end_node_id": "n3"}],
        separation_points=[
            SeparationPoint(
                id="sp2",
                name="Internal Metallic Pipe",
                x=0.5, y=0.5, z=20,
                associated_node_id="n1",
                insulation_medium="solid",
                physical_distance_m=0.6
            )
        ]
    )

    results = engine.calculate_project(proj)
    assert len(results) == 1
    res = results[0]

    assert pytest.approx(res.required_distance_s_m, 0.001) == 0.800
    assert res.pass_compliance is False
    assert pytest.approx(res.safety_margin_m, 0.001) == -0.200

def test_general_method_two_segments():
    """
    CALC-002 Segment-by-segment calculation test
    s = (ki / km) * (kc1 * l1 + kc2 * l2)
    For Class I (ki=0.08), air medium (km=1.0), kc1=0.5 (l1=10m), kc2=1.0 (l2=5m)
    s = 0.08 * (0.5*10 + 1.0*5) = 0.08 * 10 = 0.800 m
    """
    repo = StandardsRepository()
    engine = SeparationDistanceEngine(repo)

    ki = 0.08
    km = 1.0
    kc1, l1 = 0.5, 10.0
    kc2, l2 = 1.0, 5.0

    s_expected = (ki / km) * (kc1 * l1 + kc2 * l2)

    proj = Project(
        name="CALC-002 Segment Test",
        lps_class="I",
        building=Building(height_m=15),
        nodes=[ConductorNode(id="n1", x=0, y=0, z=15)],
        separation_points=[
            SeparationPoint(id="sp_gen", name="P1", x=0, y=0, z=15, associated_node_id="n1", insulation_medium="air", physical_distance_m=1.0)
        ]
    )

    results = engine.calculate_project(proj)
    res = results[0]
    assert pytest.approx(s_expected, 0.001) == 0.800
    assert res.required_distance_s_m > 0
