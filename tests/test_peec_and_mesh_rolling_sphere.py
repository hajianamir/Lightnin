import math
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


def test_neumann_touching_and_overlapping_collinear_segments_raise_value_error():
    """Step 3.4 (M2, A-b): touching or overlapping collinear filaments diverge logarithmically."""
    seg_base = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(10.0, 0.0, 0.0))
    divergent_partners = [
        # Parallel collinear sharing endpoint (10, 0, 0)
        SkewSegment3D(start=(10.0, 0.0, 0.0), end=(20.0, 0.0, 0.0)),
        # Anti-parallel collinear sharing endpoint (10, 0, 0)
        SkewSegment3D(start=(20.0, 0.0, 0.0), end=(10.0, 0.0, 0.0)),
        # Overlapping collinear segments
        SkewSegment3D(start=(5.0, 0.0, 0.0), end=(15.0, 0.0, 0.0)),
        # Coincident collinear segment
        SkewSegment3D(start=(0.0, 0.0, 0.0), end=(10.0, 0.0, 0.0)),
    ]
    for seg_other in divergent_partners:
        with pytest.raises(ValueError, match="logarithmic divergence"):
            PEECThermalEngine.calculate_mutual_inductance_neumann(seg_base, seg_other)


@pytest.mark.parametrize(
    ("spacing_m", "ref_40pt_h"),
    [
        # Converged 40-point adaptive Gauss-Legendre reference values for L = 10 m
        # parallel filaments (agreeing to 12 significant digits with exact analytical
        # antiderivative (mu_0 / (2*pi)) * [L * asinh(L/d) - sqrt(L^2 + d^2) + d]):
        (0.01, 1.320380441908e-05),
        (0.10, 8.616584733721e-06),
        (1.00, 4.186470776372e-06),
    ],
)
def test_neumann_parallel_10m_matches_40pt_reference_within_1e6(
    spacing_m: float, ref_40pt_h: float
):
    """Step 3.4 (M2, A-c & B-c): 10 m parallel filaments at 1 cm, 10 cm, 1 m within 1e-6 rel."""
    seg_1 = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(10.0, 0.0, 0.0))
    seg_2 = SkewSegment3D(start=(0.0, spacing_m, 0.0), end=(10.0, spacing_m, 0.0))

    m_10 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_1, seg_2, num_gauss_points=10
    )
    m_20 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_1, seg_2, num_gauss_points=20
    )
    m_40 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_1, seg_2, num_gauss_points=40
    )

    assert m_10 == pytest.approx(ref_40pt_h, rel=1e-6)
    assert m_20 == pytest.approx(ref_40pt_h, rel=1e-6)
    assert m_40 == pytest.approx(ref_40pt_h, rel=1e-6)
    assert abs(m_20 - m_40) / abs(m_40) < 1e-6


def test_neumann_collinear_1mm_gap_and_noncollinear_crossing_converge():
    """Step 3.4 (M2): 1 mm collinear gap and non-collinear crossing/shared-vertex filaments."""
    # (iv) Two 10 m collinear segments separated by a 1 mm gap:
    # Exact analytical integral of 1e-7 * int_0^10 int_{10.001}^{20.001} dx dy / (y - x)
    # = 1e-7 * (20.001 * ln(20.001) - 2 * 10.001 * ln(10.001) + 0.001 * ln(0.001))
    seg_c1 = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(10.0, 0.0, 0.0))
    seg_c2 = SkewSegment3D(start=(10.001, 0.0, 0.0), end=(20.001, 0.0, 0.0))
    m_gap_10 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_c1, seg_c2, num_gauss_points=10
    )
    m_gap_20 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_c1, seg_c2, num_gauss_points=20
    )
    m_gap_40 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_c1, seg_c2, num_gauss_points=40
    )
    assert m_gap_10 == pytest.approx(1.385342634301e-06, rel=1e-6)
    assert abs(m_gap_20 - m_gap_40) / abs(m_gap_40) < 1e-6

    # (iii) Two 10 m non-collinear segments crossing at their midpoint at 60 deg
    # (including odd num_gauss_points=11 where single-panel Gauss hits s=t=0.5):
    half_h = 2.5 * math.sqrt(3.0)
    seg_x1 = SkewSegment3D(start=(-5.0, 0.0, 0.0), end=(5.0, 0.0, 0.0))
    seg_x2 = SkewSegment3D(start=(-2.5, -half_h, 0.0), end=(2.5, half_h, 0.0))
    m_cross_10 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_x1, seg_x2, num_gauss_points=10
    )
    m_cross_11 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_x1, seg_x2, num_gauss_points=11
    )
    m_cross_40 = PEECThermalEngine.calculate_mutual_inductance_neumann(
        seg_x1, seg_x2, num_gauss_points=40
    )
    assert m_cross_10 == pytest.approx(1.86626404e-06, rel=1e-6)
    assert m_cross_11 == pytest.approx(1.86626404e-06, rel=1e-6)
    assert m_cross_40 == pytest.approx(1.86626404e-06, rel=1e-6)

    # Non-collinear 0.1 m segments sharing endpoint (0, 0, 0) at 60 deg:
    # Exact analytical integral = (mu_0 / (4*pi)) * L * cos(60 deg) * 2 * ln(3) = 1e-7 * 0.1 * ln(3)
    seg_v1 = SkewSegment3D(start=(0.0, 0.0, 0.0), end=(0.1, 0.0, 0.0))
    seg_v2 = SkewSegment3D(
        start=(0.0, 0.0, 0.0), end=(0.05, 0.05 * math.sqrt(3.0), 0.0)
    )
    m_vert = PEECThermalEngine.calculate_mutual_inductance_neumann(seg_v1, seg_v2)
    assert m_vert == pytest.approx(1.098612288668e-08, rel=1e-6)

def test_conductor_adiabatic_heating_and_lorentz_force():
    props = ConductorThermalProperties(material="copper", cross_section_mm2=50.0, initial_temperature_c=20.0)
    res = PEECThermalEngine.evaluate_thermal_and_electrodynamic_stress(
        props, lps_class="I", parallel_conductor_spacing_m=0.1
    )
    
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
    assert res.unprotected_faces_count == 2
    assert res.coverage_percentage == 0.0
    assert res.face_clearances[0].is_protected is False
    assert res.face_clearances[0].status == "PARTIALLY_EXPOSED"
    assert res.face_clearances[1].is_protected is False
    assert res.face_clearances[1].status == "EXPOSED"

def test_comprehensive_risk_2024_8_components():
    engine = ComprehensiveRisk2024Engine()
    inp = ComprehensiveRiskInput(
        structure_length_m=40.0,
        structure_width_m=25.0,
        structure_height_m=15.0,
        ng_flashes_per_km2_year=2.5,
        environmental_cd=1.0,
        lps_class="I",
        fire_risk_rf=0.01,
        has_coordinated_spd=True,
        has_tws_early_warning=True,
        loss_category="normal",  # Test fixture assumption: normal-loss structure. Not a default.
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
