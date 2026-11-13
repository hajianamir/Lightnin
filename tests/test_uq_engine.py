import re
import numpy as np
import pytest
from aegislps_engine.earthing import (
    EarthingAssessmentInput,
    EarthingEngine,
    SoilLayerModel,
)
from aegislps_engine.uq_engine import UncertaintyQuantificationEngine, UQSimulationConfig

def test_uq_monte_carlo_convergence():
    engine = UncertaintyQuantificationEngine()
    cfg = UQSimulationConfig(
        num_samples=1000,
        random_seed=42,
        lps_class="I",
        target_clearance_d_m=1.0,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0,
        ring_radius_m=15.0,
    )
    res = engine.run_monte_carlo(cfg)

    assert res.num_samples == 1000
    # Closed-form expectation under independent inputs (ki=0.08, E[kc]=0.5, E[l]=15.0,
    # E[1/km] = ln(1.0/0.85)/0.15 = 1.083459): E[s] = 0.08 * 0.5 * 15.0 * 1.083459 = 0.6501 m
    # (within Monte Carlo 3*SE ~ 0.011 m for N=1000):
    assert res.mean_s_req_m == pytest.approx(0.6501, abs=0.02)
    assert res.p95_s_m >= res.p50_median_s_m
    assert res.p99_s_m >= res.p95_s_m
    assert len(res.histogram_bins) == 12
    assert len(res.histogram_counts) == 12
    assert sum(res.histogram_counts) == 1000

def test_uq_sobol_sensitivity_ranking():
    engine = UncertaintyQuantificationEngine()
    cfg = UQSimulationConfig(
        num_samples=500,
        random_seed=99,
        lps_class="I",
        target_clearance_d_m=1.0,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0,
        ring_radius_m=15.0,
    )
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
    cfg_safe = UQSimulationConfig(
        num_samples=300,
        lps_class="I",
        target_clearance_d_m=5.0,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0,
        ring_radius_m=15.0,
    )
    res_safe = engine.run_monte_carlo(cfg_safe)
    assert res_safe.probability_of_violation_pct == 0.0
    assert res_safe.status == "RELIABLE"

    # Very low clearance 0.1m -> violation probability ~ 100%
    cfg_risk = UQSimulationConfig(
        num_samples=300,
        lps_class="I",
        target_clearance_d_m=0.1,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0,
        ring_radius_m=15.0,
    )
    res_risk = engine.run_monte_carlo(cfg_risk)
    assert res_risk.probability_of_violation_pct >= 99.0
    assert res_risk.status == "UNRELIABLE_HIGH_RISK"


def test_uq_seed_reproducibility_and_distinct_seeds():
    """A1: Same random_seed gives identical numeric outputs; different seeds differ."""
    engine = UncertaintyQuantificationEngine()
    base_kwargs = dict(
        num_samples=1000,
        lps_class="I",
        target_clearance_d_m=0.65,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0,
        ring_radius_m=15.0,
    )
    res_a = engine.run_monte_carlo(UQSimulationConfig(random_seed=42, **base_kwargs))
    res_b = engine.run_monte_carlo(UQSimulationConfig(random_seed=42, **base_kwargs))
    res_c = engine.run_monte_carlo(UQSimulationConfig(random_seed=43, **base_kwargs))

    assert res_a.model_dump() == res_b.model_dump()
    assert (
        res_a.mean_s_req_m,
        res_a.p95_s_m,
        res_a.earthing_p95_resistance_ohm,
        res_a.histogram_counts,
    ) != (
        res_c.mean_s_req_m,
        res_c.p95_s_m,
        res_c.earthing_p95_resistance_ohm,
        res_c.histogram_counts,
    )


def test_uq_does_not_mutate_global_numpy_rng_state():
    """A2: np.random.get_state() before and after run_monte_carlo must be identical."""
    np.random.seed(123456)
    expected_next_draw = np.random.RandomState(123456).random()
    state_before = np.random.get_state()

    engine = UncertaintyQuantificationEngine()
    engine.run_monte_carlo(
        UQSimulationConfig(
            num_samples=500,
            random_seed=98765,
            lps_class="II",
            target_clearance_d_m=0.8,
            nominal_path_length_m=20.0,
            nominal_soil_rho_ohm_m=150.0,
            ring_radius_m=12.0,
        )
    )

    state_after = np.random.get_state()
    assert state_before[0] == state_after[0]
    assert np.array_equal(state_before[1], state_after[1])
    assert state_before[2:] == state_after[2:]
    assert np.random.random() == expected_next_draw


@pytest.mark.parametrize(
    "rho_ohm_m,ring_radius_m,conductor_diameter_m,burial_depth_m",
    [
        (100.0, 15.0, 0.01, 0.5),
        (250.0, 8.0, 0.012, 0.6),
        (1200.0, 25.0, 0.008, 0.8),
    ],
)
def test_uq_ring_resistance_matches_earthing_type_b_ring(
    rho_ohm_m: float,
    ring_radius_m: float,
    conductor_diameter_m: float,
    burial_depth_m: float,
):
    """B1: UQ Type B ring resistance matches earthing.py within 1e-9 relative."""
    engine = UncertaintyQuantificationEngine()
    earthing_res = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(is_two_layer=False, rho_upper_ohm_m=rho_ohm_m),
            electrode_type="type_b_ring",
            ring_radius_m=ring_radius_m,
            conductor_diameter_m=conductor_diameter_m,
            burial_depth_m=burial_depth_m,
        )
    )
    uq_r = engine.evaluate_type_b_ring_resistance(
        rho_ohm_m=rho_ohm_m,
        ring_radius_m=ring_radius_m,
        conductor_diameter_m=conductor_diameter_m,
        burial_depth_m=burial_depth_m,
        lps_class="I",
    )
    assert uq_r == pytest.approx(earthing_res.stationary_resistance_r_ohm, rel=1e-9)

    # Also verify end-to-end run_monte_carlo earthing_p95_resistance_ohm uses earthing.py
    cfg = UQSimulationConfig(
        num_samples=500,
        random_seed=42,
        lps_class="I",
        target_clearance_d_m=1.0,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0,
        ring_radius_m=ring_radius_m,
        conductor_diameter_m=conductor_diameter_m,
        burial_depth_m=burial_depth_m,
    )
    mc_res = engine.run_monte_carlo(cfg)

    rng = np.random.default_rng(cfg.random_seed)
    _ = rng.normal(15.0, 1.5, cfg.num_samples)
    _ = rng.normal(engine.KC_MEAN, engine.KC_STD, cfg.num_samples)
    _ = rng.uniform(0.85, 1.0, cfg.num_samples)
    samples_rho = rng.lognormal(np.log(100.0), 0.35, cfg.num_samples)
    p95_rho = float(np.percentile(samples_rho, 95))

    expected_p95_earthing = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(is_two_layer=False, rho_upper_ohm_m=p95_rho),
            electrode_type="type_b_ring",
            ring_radius_m=ring_radius_m,
            conductor_diameter_m=conductor_diameter_m,
            burial_depth_m=burial_depth_m,
        )
    ).stationary_resistance_r_ohm
    assert mc_res.earthing_p95_resistance_ohm == round(expected_p95_earthing, 2)


def test_uq_kc_docstring_and_code_parameters_match():
    """C1: Docstring kc parameters match class constants and actual Monte Carlo draws."""
    doc = UncertaintyQuantificationEngine.__doc__ or ""
    match = re.search(
        r"Current sharing kc\s*~\s*Normal\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)"
        r"\s*,\s*clipped to\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]",
        doc,
    )
    assert match is not None, (
        "Docstring must specify 'Current sharing kc ~ Normal(mean, std), clipped to [min, max]'."
    )
    doc_mean, doc_std, doc_clip_min, doc_clip_max = (
        float(match.group(1)),
        float(match.group(2)),
        float(match.group(3)),
        float(match.group(4)),
    )

    assert (doc_mean, doc_std, doc_clip_min, doc_clip_max) == (
        UncertaintyQuantificationEngine.KC_MEAN,
        UncertaintyQuantificationEngine.KC_STD,
        UncertaintyQuantificationEngine.KC_CLIP_MIN,
        UncertaintyQuantificationEngine.KC_CLIP_MAX,
    )
    assert (doc_mean, doc_std, doc_clip_min, doc_clip_max) == (0.5, 0.06, 0.15, 0.95)
    assert "modelling assumption" in doc.lower()
    assert "iec 62305-3:2024" in doc.lower()

    # Verify run_monte_carlo actually draws kc with the docstring-declared parameters
    engine = UncertaintyQuantificationEngine()
    cfg = UQSimulationConfig(
        num_samples=1500,
        random_seed=77,
        lps_class="I",
        target_clearance_d_m=0.8,
        nominal_path_length_m=15.0,
        nominal_soil_rho_ohm_m=100.0,
        ring_radius_m=15.0,
    )
    res = engine.run_monte_carlo(cfg)

    rng = np.random.default_rng(cfg.random_seed)
    samples_l = np.clip(rng.normal(15.0, 1.5, cfg.num_samples), 7.5, 30.0)
    samples_kc = np.clip(
        rng.normal(doc_mean, doc_std, cfg.num_samples), doc_clip_min, doc_clip_max
    )
    samples_km = rng.uniform(0.85, 1.0, cfg.num_samples)
    expected_s = 0.08 * (samples_kc / samples_km) * samples_l

    assert res.mean_s_req_m == round(float(np.mean(expected_s)), 3)
    assert res.std_s_req_m == round(float(np.std(expected_s)), 3)
    assert res.p95_s_m == round(float(np.percentile(expected_s, 95)), 3)
    assert any(
        "modelling assumption" in msg.lower() and "iec 62305-3:2024" in msg.lower()
        for msg in res.engineering_insights
    )


@pytest.mark.parametrize(
    "varying_key",
    ["conductor_length_l", "current_sharing_kc", "insulation_medium_km"],
)
def test_uq_sobol_analytic_single_varying_input(varying_key: str, monkeypatch):
    """D: When only one input varies (others fixed), its index is 1.0 within 1e-6 and others 0.0."""
    rng = np.random.default_rng(2026)
    n_samples = 1000
    fixed_l = np.full(n_samples, 15.1)
    fixed_kc = np.full(n_samples, 0.3)
    fixed_km = np.full(n_samples, 0.925)

    var_l = np.clip(rng.normal(15.0, 1.5, n_samples), 7.5, 30.0)
    var_kc = np.clip(rng.normal(0.5, 0.06, n_samples), 0.15, 0.95)
    var_km = rng.uniform(0.85, 1.0, n_samples)

    samples_l = var_l if varying_key == "conductor_length_l" else fixed_l
    samples_kc = var_kc if varying_key == "current_sharing_kc" else fixed_kc
    samples_km = var_km if varying_key == "insulation_medium_km" else fixed_km

    # 1. Direct screening estimator check (unrounded float64)
    raw = UncertaintyQuantificationEngine.compute_sobol_screening_indices(
        ki=0.08,
        samples_l=samples_l,
        samples_kc=samples_kc,
        samples_km=samples_km,
    )
    for key, val in raw.items():
        if key == varying_key:
            assert val == pytest.approx(1.0, abs=1e-6)
        else:
            assert val == 0.0

    # 2. End-to-end run_monte_carlo check
    engine = UncertaintyQuantificationEngine()
    monkeypatch.setattr(
        engine,
        "_sample_separation_inputs",
        lambda _rng, _n, _mu_l: (samples_l, samples_kc, samples_km),
    )
    res = engine.run_monte_carlo(
        UQSimulationConfig(
            num_samples=n_samples,
            random_seed=42,
            lps_class="I",
            target_clearance_d_m=0.8,
            nominal_path_length_m=15.1,
            nominal_soil_rho_ohm_m=100.0,
            ring_radius_m=15.0,
        )
    )
    for key, val in res.sobol_first_order_indices.items():
        if key == varying_key:
            assert val == pytest.approx(1.0, abs=1e-6)
        else:
            assert val == 0.0
    assert any("Option D2" in msg for msg in res.engineering_insights)
