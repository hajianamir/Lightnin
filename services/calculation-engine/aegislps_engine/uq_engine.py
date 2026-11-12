import math
import numpy as np
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aegislps_engine.earthing import (
    EarthingAssessmentInput,
    EarthingEngine,
    SoilLayerModel,
)

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")
_LPS_KI_MAP: Dict[str, float] = {
    "I": 0.08,
    "II": 0.06,
    "III": 0.04,
    "IV": 0.04,
}


def _check_positive_finite(name: str, val: object) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float, np.number)):
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    val_f = float(val)
    if not math.isfinite(val_f) or val_f <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    return val_f


def _check_nonnegative_finite(name: str, val: object) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float, np.number)):
        raise ValueError(f"{name} must be finite and >= 0, got {val!r}.")
    val_f = float(val)
    if not math.isfinite(val_f) or val_f < 0.0:
        raise ValueError(f"{name} must be finite and >= 0, got {val!r}.")
    return val_f


class UQInputDistribution(BaseModel):
    # unused model, not wired to any route
    model_config = ConfigDict(allow_inf_nan=False)

    parameter_name: str
    distribution_type: str = "normal"  # normal, lognormal, uniform, weibull — unused model, not wired to any route
    mean: float
    std_dev: float = 0.1  # unused model, not wired to any route
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    shape_k: Optional[float] = 2.0  # Weibull shape parameter — unused model, not wired to any route
    scale_lambda: Optional[float] = 100.0  # Weibull scale parameter — unused model, not wired to any route

    @field_validator("mean", "min_val", "max_val", mode="before")
    @classmethod
    def _validate_finite_numeric(cls, v, info):
        if v is None:
            return v
        if isinstance(v, bool) or not isinstance(v, (int, float, np.number)):
            raise ValueError(f"{info.field_name} must be finite numeric, got {v!r}.")
        val_f = float(v)
        if not math.isfinite(val_f):
            raise ValueError(f"{info.field_name} must be finite numeric, got {v!r}.")
        return val_f

    @field_validator("std_dev", mode="before")
    @classmethod
    def _validate_std_dev(cls, v):
        return _check_positive_finite("std_dev", v)

    @field_validator("shape_k", "scale_lambda", mode="before")
    @classmethod
    def _validate_optional_positive_params(cls, v, info):
        if v is None:
            return v
        return _check_positive_finite(info.field_name, v)

    @model_validator(mode="after")
    def _validate_bounds(self) -> "UQInputDistribution":
        if (
            self.min_val is not None
            and self.max_val is not None
            and self.min_val > self.max_val
        ):
            raise ValueError(
                f"min_val ({self.min_val}) must not exceed max_val ({self.max_val})."
            )
        return self


class UQSimulationConfig(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    num_samples: int = 2000
    random_seed: int = 42
    lps_class: str
    target_clearance_d_m: float
    nominal_path_length_m: float
    nominal_soil_rho_ohm_m: float
    ring_radius_m: float
    conductor_diameter_m: float = 0.01
    burial_depth_m: float = 0.5

    @field_validator("num_samples", mode="before")
    @classmethod
    def _validate_num_samples(cls, v):
        if isinstance(v, bool) or not isinstance(v, int) or v < 100:
            raise ValueError(
                f"num_samples must be an integer >= 100, got {v!r}."
            )
        return v

    @field_validator("random_seed", mode="before")
    @classmethod
    def _validate_random_seed(cls, v):
        if isinstance(v, bool) or not isinstance(v, int) or v < 0 or v >= 2**32:
            raise ValueError(
                f"random_seed must be an integer in [0, 2**32 - 1], got {v!r}."
            )
        return v

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v):
        if not isinstance(v, str) or v not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        return v

    @field_validator("target_clearance_d_m", mode="before")
    @classmethod
    def _validate_target_clearance(cls, v):
        return _check_nonnegative_finite("target_clearance_d_m", v)

    @field_validator(
        "nominal_path_length_m",
        "nominal_soil_rho_ohm_m",
        "ring_radius_m",
        "conductor_diameter_m",
        "burial_depth_m",
        mode="before",
    )
    @classmethod
    def _validate_positive_geometry_fields(cls, v, info):
        return _check_positive_finite(info.field_name, v)


class UQSimulationResult(BaseModel):
    """Monte Carlo uncertainty quantification and sensitivity screening result.

    ``sobol_first_order_indices`` retains its field name for API/schema
    compatibility, and reports Option D2 screening indicators: raw clipped
    plug-in conditional-mean variance ratios ``clip(Var(s | X_i, E[X_~i]) / Var(s), 0, 1)``
    without forced sum-to-1 normalization.
    """

    num_samples: int
    mean_s_req_m: float
    std_s_req_m: float
    p50_median_s_m: float
    p95_s_m: float
    p99_s_m: float
    probability_of_violation_pct: float
    histogram_bins: List[float]
    histogram_counts: List[int]
    sobol_first_order_indices: Dict[str, float]
    earthing_p95_resistance_ohm: float
    status: str
    engineering_insights: List[str] = Field(default_factory=list)


class UncertaintyQuantificationEngine:
    """
    Uncertainty Quantification (UQ) & Sensitivity Screening Engine.

    Implements:
    - Monte Carlo stochastic simulations using an isolated local RNG
      (``numpy.random.default_rng``) without mutating global NumPy RNG state.
    - Statistical input distributions:
      * Path length l ~ Normal(mu_l, 0.1 * mu_l), clipped to [0.5 * mu_l, 2.0 * mu_l]
      * Current sharing kc ~ Normal(0.5, 0.06), clipped to [0.15, 0.95]
        (modelling assumption; not from IEC 62305-3:2024)
      * Material insulation km ~ Uniform(0.85, 1.0)
      * Soil resistivity rho ~ Lognormal(ln(mu_rho), 0.35)
    - Stationary Type B ring earth-electrode resistance delegated directly to
      ``EarthingEngine.evaluate_earthing_system`` (``earthing.py``, Sunde
      equivalent-radius form).
    - Empirical percentiles (P50 / P95 / P99) and violation probability.
    - Sensitivity screening indicators (Option D2, returned in
      ``sobol_first_order_indices``): plug-in conditional-mean variance ratios
      ``clip(Var(s | X_i, E[X_~i]) / Var(s), 0, 1)`` reported as raw clipped
      values without forced normalization to sum 1.0 (not a Saltelli/Jansen
      first-order Sobol estimator).
    """

    # Modelling assumption for stochastic sensitivity screening; NOT specified by
    # IEC 62305-3:2024 (which defines deterministic topological/tabular kc values,
    # not a probability distribution).
    KC_MEAN: float = 0.5
    KC_STD: float = 0.06
    KC_CLIP_MIN: float = 0.15
    KC_CLIP_MAX: float = 0.95

    @staticmethod
    def _unit_type_b_ring_resistance(
        ring_radius_m: float,
        conductor_diameter_m: float = 0.01,
        burial_depth_m: float = 0.5,
        lps_class: str = "I",
    ) -> float:
        """Evaluate Type B ring stationary resistance at unit soil resistivity
        (``rho = 1.0 ohm.m``) via ``EarthingEngine.evaluate_earthing_system``."""
        unit_res = EarthingEngine().evaluate_earthing_system(
            EarthingAssessmentInput(
                lps_class=lps_class,
                soil=SoilLayerModel(is_two_layer=False, rho_upper_ohm_m=1.0),
                electrode_type="type_b_ring",
                ring_radius_m=ring_radius_m,
                conductor_diameter_m=conductor_diameter_m,
                burial_depth_m=burial_depth_m,
            )
        )
        return float(unit_res.stationary_resistance_r_ohm)

    @classmethod
    def evaluate_type_b_ring_resistance(
        cls,
        rho_ohm_m: float,
        ring_radius_m: float,
        *,
        conductor_diameter_m: float = 0.01,
        burial_depth_m: float = 0.5,
        lps_class: str = "I",
    ) -> float:
        """Evaluate stationary Type B ring resistance by reusing ``earthing.py``'s
        ``EarthingEngine.evaluate_earthing_system`` (`electrode_type='type_b_ring'`)
        and scaling linearly by ``rho_ohm_m``."""
        rho = _check_positive_finite("rho_ohm_m", rho_ohm_m)
        r_ring = _check_positive_finite("ring_radius_m", ring_radius_m)
        d_cond = _check_positive_finite("conductor_diameter_m", conductor_diameter_m)
        h_depth = _check_positive_finite("burial_depth_m", burial_depth_m)
        unit_r = cls._unit_type_b_ring_resistance(
            ring_radius_m=r_ring,
            conductor_diameter_m=d_cond,
            burial_depth_m=h_depth,
            lps_class=lps_class,
        )
        return float(rho * unit_r)

    def _sample_separation_inputs(
        self,
        rng: np.random.Generator,
        num_samples: int,
        mu_l: float,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Path length l ~ Normal(mu_l, 0.1 * mu_l), clipped to [0.5 * mu_l, 2.0 * mu_l]
        sigma_l = 0.1 * mu_l
        samples_l = rng.normal(mu_l, sigma_l, num_samples)
        samples_l = np.clip(samples_l, 0.5 * mu_l, 2.0 * mu_l)

        # Current-sharing factor kc ~ Normal(0.5, 0.06), clipped to [0.15, 0.95].
        # Modelling assumption for probabilistic screening; NOT from IEC 62305-3:2024.
        samples_kc = rng.normal(self.KC_MEAN, self.KC_STD, num_samples)
        samples_kc = np.clip(samples_kc, self.KC_CLIP_MIN, self.KC_CLIP_MAX)

        # Insulation factor km ~ Uniform(0.85, 1.0)
        samples_km = rng.uniform(0.85, 1.0, num_samples)
        return samples_l, samples_kc, samples_km

    @staticmethod
    def compute_sobol_screening_indices(
        ki: float,
        samples_l: np.ndarray,
        samples_kc: np.ndarray,
        samples_km: np.ndarray,
        samples_s: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Compute Option D2 sensitivity screening indicators (raw clipped plug-in
        conditional-mean variance ratios without forced sum-to-1 normalization)."""
        if samples_s is None:
            samples_s = ki * (samples_kc / samples_km) * samples_l

        var_total = (
            0.0 if np.ptp(samples_s) == 0.0 else float(np.var(samples_s))
        )
        if not math.isfinite(var_total) or var_total <= 0.0:
            raise ValueError(
                f"Degenerate zero or non-finite separation-distance variance var_total={var_total!r}; "
                "cannot compute sensitivity screening indices."
            )

        mean_l = float(np.mean(samples_l))
        mean_kc = float(np.mean(samples_kc))
        mean_km = float(np.mean(samples_km))

        s_mean_l = ki * (mean_kc / mean_km) * samples_l
        var_l = 0.0 if np.ptp(s_mean_l) == 0.0 else float(np.var(s_mean_l))
        sobol_l = float(min(1.0, max(0.0, var_l / var_total)))

        s_mean_kc = ki * (samples_kc / mean_km) * mean_l
        var_kc = 0.0 if np.ptp(s_mean_kc) == 0.0 else float(np.var(s_mean_kc))
        sobol_kc = float(min(1.0, max(0.0, var_kc / var_total)))

        s_mean_km = ki * (mean_kc / samples_km) * mean_l
        var_km = 0.0 if np.ptp(s_mean_km) == 0.0 else float(np.var(s_mean_km))
        sobol_km = float(min(1.0, max(0.0, var_km / var_total)))

        return {
            "conductor_length_l": sobol_l,
            "current_sharing_kc": sobol_kc,
            "insulation_medium_km": sobol_km,
        }

    def run_monte_carlo(self, cfg: UQSimulationConfig) -> UQSimulationResult:
        if (
            isinstance(cfg.num_samples, bool)
            or not isinstance(cfg.num_samples, int)
            or cfg.num_samples < 100
        ):
            raise ValueError(
                f"num_samples must be an integer >= 100, got {cfg.num_samples!r}."
            )
        if (
            isinstance(cfg.random_seed, bool)
            or not isinstance(cfg.random_seed, int)
            or cfg.random_seed < 0
            or cfg.random_seed >= 2**32
        ):
            raise ValueError(
                f"random_seed must be an integer in [0, 2**32 - 1], got {cfg.random_seed!r}."
            )
        if not isinstance(cfg.lps_class, str) or cfg.lps_class not in _LPS_KI_MAP:
            raise ValueError(
                f"Unknown LPS class {cfg.lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )

        d_target = _check_nonnegative_finite(
            "target_clearance_d_m", cfg.target_clearance_d_m
        )
        mu_l = _check_positive_finite(
            "nominal_path_length_m", cfg.nominal_path_length_m
        )
        mu_rho = _check_positive_finite(
            "nominal_soil_rho_ohm_m", cfg.nominal_soil_rho_ohm_m
        )
        r_ring = _check_positive_finite("ring_radius_m", cfg.ring_radius_m)
        d_cond = _check_positive_finite(
            "conductor_diameter_m", cfg.conductor_diameter_m
        )
        h_depth = _check_positive_finite("burial_depth_m", cfg.burial_depth_m)

        rng = np.random.default_rng(cfg.random_seed)
        N = int(cfg.num_samples)
        ki = _LPS_KI_MAP[cfg.lps_class]

        # 1. Sample input parameter distributions using local RNG
        samples_l, samples_kc, samples_km = self._sample_separation_inputs(
            rng, N, mu_l
        )

        # Soil resistivity rho ~ Lognormal(ln(mu_rho), 0.35)
        sigma_log = 0.35  # Typical 35% geometric dispersion in geotechnical surveys
        samples_rho = rng.lognormal(np.log(mu_rho), sigma_log, N)

        # 2. Vectorized separation distance evaluation s = ki * (kc / km) * l
        samples_s = ki * (samples_kc / samples_km) * samples_l

        # 3. Vectorized Type B ring resistance via earthing.py (Sunde equivalent-radius form)
        unit_ring_r_ohm = self._unit_type_b_ring_resistance(
            ring_radius_m=r_ring,
            conductor_diameter_m=d_cond,
            burial_depth_m=h_depth,
            lps_class=cfg.lps_class,
        )
        samples_r_earth = samples_rho * unit_ring_r_ohm

        # Statistical analysis
        mean_s = float(np.mean(samples_s))
        std_s = float(np.std(samples_s))
        p50 = float(np.percentile(samples_s, 50))
        p95 = float(np.percentile(samples_s, 95))
        p99 = float(np.percentile(samples_s, 99))
        p95_r_earth = float(np.percentile(samples_r_earth, 95))

        # Probability of compliance violation (D_actual < s_required)
        violations = np.sum(samples_s > d_target)
        prob_violation = float((violations / N) * 100.0)

        # Generate histogram bins for UI distribution chart
        counts, bin_edges = np.histogram(samples_s, bins=12)
        bins_mid = [
            float((bin_edges[i] + bin_edges[i + 1]) / 2.0)
            for i in range(len(counts))
        ]
        counts_list = [int(c) for c in counts]

        # 4. Option D2 sensitivity screening indicators (raw clipped values; unnormalized)
        raw_screening = self.compute_sobol_screening_indices(
            ki=ki,
            samples_l=samples_l,
            samples_kc=samples_kc,
            samples_km=samples_km,
            samples_s=samples_s,
        )
        sobol_indices = {
            key: round(val, 3) for key, val in raw_screening.items()
        }
        raw_sum = sum(raw_screening.values())
        dominant_key = max(raw_screening, key=raw_screening.get)

        insights = [
            f"Evaluated {N:,} stochastic Monte Carlo realizations for LPS Class {cfg.lps_class}.",
            f"Nominal separation distance: {mean_s:.3f}m | 95th Percentile (P95): {p95:.3f}m | 99th Percentile (P99): {p99:.3f}m.",
            f"Probability of separation-distance violation at physical clearance {d_target:.2f}m is {prob_violation:.1f}%.",
            (
                f"Sensitivity screening indicator (Option D2, plug-in conditional-mean variance ratios, "
                f"unnormalized; not Saltelli/Jansen Sobol): primary driver '{dominant_key}' = "
                f"{raw_screening[dominant_key]:.3f} (raw clipped indicators: "
                f"conductor_length_l={raw_screening['conductor_length_l']:.3f}, "
                f"current_sharing_kc={raw_screening['current_sharing_kc']:.3f}, "
                f"insulation_medium_km={raw_screening['insulation_medium_km']:.3f}; "
                f"raw sum={raw_sum:.3f})."
            ),
            (
                "Current-sharing distribution kc ~ Normal(0.5, 0.06) clipped to [0.15, 0.95] "
                "is a modelling assumption, not from IEC 62305-3:2024."
            ),
            (
                f"95% confidence upper bound for Type B ring earthing resistance "
                f"(shared earthing.py Sunde equivalent-radius form) is {p95_r_earth:.2f} ohm."
            ),
        ]

        return UQSimulationResult(
            num_samples=N,
            mean_s_req_m=round(mean_s, 3),
            std_s_req_m=round(std_s, 3),
            p50_median_s_m=round(p50, 3),
            p95_s_m=round(p95, 3),
            p99_s_m=round(p99, 3),
            probability_of_violation_pct=round(prob_violation, 1),
            histogram_bins=bins_mid,
            histogram_counts=counts_list,
            sobol_first_order_indices=sobol_indices,
            earthing_p95_resistance_ohm=round(p95_r_earth, 2),
            status="RELIABLE" if prob_violation < 5.0 else "UNRELIABLE_HIGH_RISK",
            engineering_insights=insights,
        )
