import pytest
from aegislps_engine.uq_engine import UncertaintyQuantificationEngine, UQSimulationConfig

def test_uq_monte_carlo_convergence():
    engine = UncertaintyQuantificationEngine()
    cfg = UQSimulationConfig(
        num_samples=1000,
        random_seed=42,
        lps_class="I",
        target_clearance_d_m=1.0,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0
    )
    res = engine.run_monte_carlo(cfg)

    assert res.num_samples == 1000
    assert res.mean_s_req_m > 0.4
    assert res.p95_s_m >= res.p50_median_s_m
    assert res.p99_s_m >= res.p95_s_m
    assert len(res.histogram_bins) == 12
    assert len(res.histogram_counts) == 12
    assert sum(res.histogram_counts) == 1000

def test_uq_sobol_sensitivity_ranking():
    engine = UncertaintyQuantificationEngine()
    cfg = UQSimulationConfig(num_samples=500, random_seed=99, lps_class="I")
    res = engine.run_monte_carlo(cfg)

    sobol = res.sobol_first_order_indices
    assert "conductor_length_l" in sobol
    assert "current_sharing_kc" in sobol
    assert "insulation_medium_km" in sobol
    # Sobol index sum ~ 1.0
    assert pytest.approx(sum(sobol.values()), 0.05) == 1.0

def test_uq_violation_probability_boundary():
    engine = UncertaintyQuantificationEngine()
    # High clearance 5.0m -> violation probability ~ 0%
    cfg_safe = UQSimulationConfig(num_samples=300, target_clearance_d_m=5.0)
    res_safe = engine.run_monte_carlo(cfg_safe)
    assert res_safe.probability_of_violation_pct == 0.0
    assert res_safe.status == "RELIABLE"

    # Very low clearance 0.1m -> violation probability ~ 100%
    cfg_risk = UQSimulationConfig(num_samples=300, target_clearance_d_m=0.1)
    res_risk = engine.run_monte_carlo(cfg_risk)
    assert res_risk.probability_of_violation_pct >= 99.0
    assert res_risk.status == "UNRELIABLE_HIGH_RISK"
