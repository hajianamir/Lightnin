import pytest
from aegislps_engine.peec_thermal import (
    PEECThermalEngine,
    ConductorThermalProperties,
    SkewSegment3D
)
from aegislps_geometry.mesh_rolling_sphere import (
    ArbitraryMeshRollingSphereEngine,
    MeshRollingSphereInput,
    TriangleFace
)
from aegislps_engine.comprehensive_risk import (
    ComprehensiveRisk2024Engine,
    ComprehensiveRiskInput,
    IncomingServiceLine
)

def test_neumann_mutual_inductance_parallel_segments():
    # Two parallel conductors of length 5m spaced 0.5m apart
    seg_1 = SkewSegment3D(start=(0, 0, 0), end=(5, 0, 0))
    seg_2 = SkewSegment3D(start=(0, 0.5, 0), end=(5, 0.5, 0))

    m_val = PEECThermalEngine.calculate_mutual_inductance_neumann(seg_1, seg_2)
    assert m_val > 0.0
    # Expected mutual inductance for 5m parallel wires spaced 0.5m ~ 1-5 uH
    assert 1e-7 <= m_val <= 1e-5

def test_conductor_adiabatic_heating_and_lorentz_force():
    props = ConductorThermalProperties(material="copper", cross_section_mm2=50.0, initial_temperature_c=20.0)
    res = PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(props, lps_class="I")

    assert res.thermal_stress_safe is True
    assert res.final_temperature_c > res.final_temperature_c - res.adiabatic_temp_rise_delta_theta_k
    assert res.peak_repulsive_force_n_per_m > 0.0
    assert 0.1 <= res.recommended_fastener_spacing_m <= 1.0

def test_arbitrary_mesh_rolling_sphere_protection():
    engine = ArbitraryMeshRollingSphereEngine()

    # 2 roof triangles, one protected under rod at (0, 0, 20), one far away
    triangles = [
        TriangleFace(id="tri-near", v0=(0, 0, 15), v1=(2, 0, 15), v2=(1, 2, 15)),
        TriangleFace(id="tri-far", v0=(40, 40, 15), v1=(42, 40, 15), v2=(41, 42, 15))
    ]
    tips = [(0.0, 0.0, 20.0)] # 5m rod above roof at z=15m

    res = engine.evaluate_mesh_protection(MeshRollingSphereInput(
        sphere_radius_m=20.0,
        triangles=triangles,
        air_termination_tips=tips
    ))

    assert res.evaluated_faces_count == 2
    assert res.unprotected_faces_count == 1
    assert res.coverage_percentage == 50.0
    assert res.face_clearances[0].is_protected is True
    assert res.face_clearances[1].is_protected is False

def test_comprehensive_risk_2024_8_components():
    engine = ComprehensiveRisk2024Engine()
    inp = ComprehensiveRiskInput(
        structure_length_m=40.0,
        structure_width_m=25.0,
        structure_height_m=15.0,
        ng_flashes_per_km2_year=2.5,
        lps_class="I",
        has_coordinated_spd=True,
        has_tws_early_warning=True,
        incoming_lines=[IncomingServiceLine(service_type="aerial_power", line_length_m=500.0)]
    )
    res = engine.evaluate_risk(inp)

    comp = res.risk_components
    assert comp.r_a_touch_step > 0
    assert comp.r_b_physical_damage > 0
    assert comp.r_u_touch_voltage_service > 0
    assert comp.total_risk_r1 > 0
    assert res.collection_area_al_services_m2 > 0
    assert comp.is_r1_acceptable is True
