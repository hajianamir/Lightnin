import math
import numpy as np
from typing import Callable, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# IEC 62305-1 Annex A, Table A.1 Heidler current parameters (n = 10),
# per secondary literature summaries (ETEP 2002; ELEK; Heidler & Zischank, ICLP 2008).
HEIDLER_IEC_62305_1: Dict[str, Dict[str, float]] = {
    "first_positive_10_350": {
        "tau1": 19.0,
        "tau2": 485.0,
        "eta": 0.93,
        "n": 10.0,
    },
    "subsequent_negative_025_100": {
        "tau1": 0.454,
        "tau2": 143.0,
        "eta": 0.993,
        "n": 10.0,
    },
}

_VALID_STROKE_TYPES = ("first_positive_10_350", "subsequent_negative_025_100")
_VALID_SHIELD_MATERIALS = ("copper_aluminium", "steel")


def _check_positive_finite(name: str, val: object) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float, np.number)):
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    val_f = float(val)
    if not math.isfinite(val_f) or val_f <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    return val_f


def _heidler_scalar_di_dt(
    t_us: float, i_peak_ka: float, tau1: float, tau2: float, eta: float, n: float
) -> float:
    """Analytic scalar di/dt [kA/us] at time t_us [us] for bounded peak refinement."""
    if t_us <= 0.0:
        return 0.0
    t_val = max(float(t_us), 1e-12)
    x = t_val / tau1
    x_n_minus_1 = x ** (n - 1.0)
    x_n = x_n_minus_1 * x
    denom = 1.0 + x_n
    return (
        (i_peak_ka / eta)
        * math.exp(-t_val / tau2)
        * (
            (n * x_n_minus_1) / (tau1 * denom * denom)
            - (1.0 / tau2) * (x_n / denom)
        )
    )


def _golden_section_max_abs(
    func: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-13,
    max_iter: int = 80,
) -> float:
    """Maximize |func(t)| on [a, b] via deterministic golden-section search."""
    if b <= a:
        return abs(func(a))
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c = b - gr * (b - a)
    d = a + gr * (b - a)
    fc = abs(func(c))
    fd = abs(func(d))
    for _ in range(max_iter):
        if (b - a) <= tol * max(1.0, abs(a) + abs(b)):
            break
        if fc > fd:
            b = d
            d = c
            fd = fc
            c = b - gr * (b - a)
            fc = abs(func(c))
        else:
            a = c
            c = d
            fc = fd
            d = a + gr * (b - a)
            fd = abs(func(d))
    mid = 0.5 * (a + b)
    return float(max(abs(func(mid)), fc, fd, abs(func(a)), abs(func(b))))


class LEMPWaveformSpecification(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    stroke_type: str  # first_positive_10_350, subsequent_negative_025_100
    peak_current_ka: float  # I_peak in kA (> 0)
    t_end_us: float = 100.0  # numerical simulation window, not a standard value
    num_time_steps: int = 500  # numerical simulation window, not a standard value

    @field_validator("stroke_type", mode="before")
    @classmethod
    def _validate_stroke_type(cls, v):
        if not isinstance(v, str) or v not in _VALID_STROKE_TYPES:
            raise ValueError(
                f"Unknown stroke_type {v!r}; expected one of {_VALID_STROKE_TYPES}."
            )
        return v

    @field_validator("peak_current_ka", "t_end_us", mode="before")
    @classmethod
    def _validate_positive_floats(cls, v, info):
        return _check_positive_finite(info.field_name, v)

    @field_validator("num_time_steps", mode="before")
    @classmethod
    def _validate_num_time_steps(cls, v):
        if isinstance(v, bool) or not isinstance(v, int) or v < 2:
            raise ValueError(
                f"num_time_steps must be an integer >= 2, got {v!r}."
            )
        return v


_INTERNAL_PEAK_GRID_POINTS: int = 20_000
_MAX_RECOMMENDED_MESH_WIDTH_M: float = 5.0
_K_SOURCE_IEC_2024: Literal["IEC 62305-4:2024 Table A.4"] = (
    "IEC 62305-4:2024 Table A.4"
)
_K_SOURCE_OVERRIDE: Literal["override"] = "override"


def _shielding_factor_db(
    w_m: float,
    r_c: float,
    stroke_type: str,
    bonded: bool,
    material: str,
) -> float:
    """
    IEC 62305-4:2024 Annex A, Table A.4 magnetic shielding factor SF [dB].

    Evaluation order:
    1. Formula by material and frequency row:
       - "first_positive_10_350" (25 kHz row):
         * copper_aluminium: SF_formula = 20 * log10(8.5 / w_m)
         * steel (Note c: mu_r ~ 200):
           SF_formula = 20 * log10((8.5 / w_m) / sqrt(1 + 18e-6 / r_c^2))
       - "subsequent_negative_025_100" (1 MHz / 250 kHz row):
         * copper_aluminium or steel: SF_formula = 20 * log10(8.5 / w_m)
    2. Note a: if SF_formula < 0, set SF = 0.
    3. Note b: if bonded (meshed bonding network per Clause 5.3), add +6 dB.
    """
    w_f = _check_positive_finite("mesh_width_w_m", w_m)
    r_f = _check_positive_finite("rod_radius_m", r_c)
    if not isinstance(stroke_type, str) or stroke_type not in _VALID_STROKE_TYPES:
        raise ValueError(
            f"Unknown stroke_type {stroke_type!r}; expected one of {_VALID_STROKE_TYPES}."
        )
    if not isinstance(material, str) or material not in _VALID_SHIELD_MATERIALS:
        raise ValueError(
            f"Unknown shield material {material!r}; expected one of {_VALID_SHIELD_MATERIALS}."
        )
    if not isinstance(bonded, bool):
        raise ValueError(f"meshed_bonding_network must be a strict boolean, got {bonded!r}.")

    if stroke_type == "subsequent_negative_025_100":
        sf_formula = 20.0 * math.log10(8.5 / w_f)
    elif material == "steel":
        steel_factor = math.sqrt(1.0 + 18.0e-6 / (r_f * r_f))
        sf_formula = 20.0 * math.log10((8.5 / w_f) / steel_factor)
    elif material == "copper_aluminium":
        sf_formula = 20.0 * math.log10(8.5 / w_f)
    else:
        raise ValueError(
            f"Unknown shield material {material!r}; expected one of {_VALID_SHIELD_MATERIALS}."
        )

    sf_db = max(0.0, sf_formula)
    if bonded:
        sf_db += 6.0
    return float(sf_db)


def _safety_distance_dsf_m(w_m: float, sf_db: float) -> float:
    """
    IEC 62305-4:2024 Annex A, Eq. (A.14)-(A.15) internal safety distance d_SF/n [m]:
    d_SF/n = w_m * SF / 10 for SF >= 10 dB, and d_SF/n = w_m for SF < 10 dB.
    """
    if sf_db >= 10.0:
        return float(w_m * sf_db / 10.0)
    return float(w_m)


class ShieldingGrid(BaseModel):
    """
    Spatial grid shield parameters per IEC 62305-4:2024 Annex A (Table A.4).

    `relative_permeability_mur` is retained for input schema compatibility and has
    no effect on K_MS; for steel (`material="steel"`), magnetic permeability
    (Table A.4 Note c: mu_r ~ 200) enters SF via `rod_radius_m` (`r_c`).
    """

    model_config = ConfigDict(allow_inf_nan=False)

    is_shielded: bool
    mesh_width_w_m: Optional[float] = None
    relative_permeability_mur: float = 1.0  # relative permeability of air-like non-magnetic material
    rod_radius_m: Optional[float] = None
    material: Optional[str] = None
    meshed_bonding_network: bool = False
    shielding_factor_override_db: Optional[float] = None

    @field_validator("is_shielded", "meshed_bonding_network", mode="before")
    @classmethod
    def _require_strict_bool(cls, v, info):
        if not isinstance(v, bool):
            raise ValueError(f"{info.field_name} must be a strict boolean, got {v!r}.")
        return v

    @field_validator(
        "mesh_width_w_m",
        "relative_permeability_mur",
        "rod_radius_m",
        "shielding_factor_override_db",
        mode="before",
    )
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("Boolean is not valid for numeric shielding parameter.")
        return v

    @model_validator(mode="after")
    def _validate_shielding_grid(self) -> "ShieldingGrid":
        _check_positive_finite(
            "relative_permeability_mur", self.relative_permeability_mur
        )
        if self.mesh_width_w_m is not None:
            _check_positive_finite("mesh_width_w_m", self.mesh_width_w_m)
        if self.rod_radius_m is not None:
            _check_positive_finite("rod_radius_m", self.rod_radius_m)
        if self.material is not None:
            if not isinstance(self.material, str) or self.material not in _VALID_SHIELD_MATERIALS:
                raise ValueError(
                    f"Unknown shield material {self.material!r}; expected one of {_VALID_SHIELD_MATERIALS}."
                )
        if self.shielding_factor_override_db is not None:
            if (
                not math.isfinite(self.shielding_factor_override_db)
                or self.shielding_factor_override_db < 0.0
            ):
                raise ValueError(
                    f"shielding_factor_override_db must be finite and >= 0, got {self.shielding_factor_override_db!r}."
                )
        if self.is_shielded:
            if self.mesh_width_w_m is None:
                raise ValueError("mesh_width_w_m is required when is_shielded=True.")
            if self.rod_radius_m is None:
                raise ValueError("rod_radius_m is required when is_shielded=True.")
            if self.material is None:
                raise ValueError("material is required when is_shielded=True.")
        return self


class InternalCableLoop(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str = "signal-loop-1"
    loop_area_m2: float  # Area enclosed by signal cable and ground plane (> 0)
    center_distance_from_down_conductor_m: float  # Radial offset s_a (> 0)
    equipment_withstand_uw_kv: float  # Equipment impulse withstand U_w [kV] (> 0)

    @field_validator(
        "loop_area_m2",
        "center_distance_from_down_conductor_m",
        "equipment_withstand_uw_kv",
        mode="before",
    )
    @classmethod
    def _validate_positive_loop_fields(cls, v, info):
        return _check_positive_finite(info.field_name, v)


class LEMPTransientResult(BaseModel):
    stroke_type: str
    peak_current_ka: float
    max_di_dt_ka_per_us: float
    unattenuated_peak_h_field_a_per_m: float
    shielded_peak_h_field_a_per_m: float
    grid_shielding_factor_kms: float
    shielding_factor_db: float
    safety_distance_m: float
    k_source: Literal["IEC 62305-4:2024 Table A.4", "override"] = _K_SOURCE_IEC_2024
    peak_induced_voltage_kv: float
    equipment_withstand_uw_kv: float
    equipment_protected: bool
    status: str
    time_series_us: List[float]
    current_waveform_ka: List[float]
    induced_voltage_waveform_kv: List[float]
    warnings: List[str] = Field(default_factory=list)
    engineering_insights: List[str] = Field(default_factory=list)


class LEMPEngine:
    """
    IEC 62305-4:2024 Annex A Lightning Electromagnetic Pulse (LEMP) Engine.

    Implements:
    - Analytical Heidler function modeling of lightning surge currents:
      i(t) = (I / eta) * ( (t / tau1)^10 / (1 + (t / tau1)^10) ) * exp(-t / tau2)
    - Biot-Savart magnetic field Eq. (A.6)-(A.10) at user-supplied strike-to-volume
      distance s_a (`InternalCableLoop.center_distance_from_down_conductor_m`):
      H_0(t) = i(t) / (2 * pi * s_a),  H_1(t) = H_0(t) / 10^(SF / 20)
    - IEC 62305-4:2024 Table A.4 spatial grid shield attenuation:
      K_MS = 10^(-SF / 20), with copper/aluminium & steel rows, Note a (SF >= 0 dB),
      Note b (+6 dB meshed bonding network), and internal safety distance d_SF/n
      per Eq. (A.14)-(A.15).
    - Uniform-field Faraday induction over internal cabling loops (valid for b << s_a):
      u_i(t) = - mu_0 * K_MS * (dH_0 / dt) * A_loop
             = - (mu_0 / (2 * pi * s_a)) * K_MS * A_loop * (di / dt)
    - Continuous/fine-grid peak surge stress evaluation vs. equipment withstand (U_w).
    """

    MU_0 = 4.0 * np.pi * 1e-7  # H/m permeability of free space

    @classmethod
    def evaluate_heidler_current(
        cls,
        t_us: np.ndarray,
        stroke_type: str,
        i_peak_ka: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Evaluates current i(t) in kA and analytic derivative di/dt in kA/us
        using IEC 62305-1 Table A.1 Heidler parameters (HEIDLER_IEC_62305_1).

        Notes & limitations:
        - Returns positive current magnitude for all strokes (including
          "subsequent_negative_025_100"); `i_peak_ka` must be finite and > 0.
        - Unrecognized `stroke_type` values raise `ValueError`.
        - Under the IEC 62305-1 10%-90% current front-time definition
          T1 = 1.25 * (t90 - t10), the Table A.1 parameters give
          T1 = 9.980 us (-0.20% vs nominal 10 us) for 10/350 and
          T1 = 0.2493 us (-0.27% vs nominal 0.25 us) for 0.25/100;
          tail times to 0.5 * I_peak are T2 = 370.76 us (+5.93%) and
          T2 = 100.16 us (+0.16%).
        """
        if not isinstance(stroke_type, str) or stroke_type not in HEIDLER_IEC_62305_1:
            raise ValueError(
                f"Unknown stroke_type {stroke_type!r}; expected one of {_VALID_STROKE_TYPES}."
            )
        peak_f = _check_positive_finite("peak_current_ka", i_peak_ka)
        params = HEIDLER_IEC_62305_1[stroke_type]

        tau1 = params["tau1"]
        tau2 = params["tau2"]
        eta = params["eta"]
        n = params["n"]

        t_arr = np.asarray(t_us, dtype=float)
        t_pos = np.maximum(t_arr, 1e-12)
        x = t_pos / tau1
        x_n_minus_1 = x ** (n - 1.0)
        x_n = x_n_minus_1 * x
        denom = 1.0 + x_n
        exp_decay = np.exp(-t_pos / tau2)
        scale = peak_f / eta

        current_shape = scale * (x_n / denom) * exp_decay
        di_dt_shape = scale * exp_decay * (
            (n * x_n_minus_1) / (tau1 * denom * denom)
            - (1.0 / tau2) * (x_n / denom)
        )

        current_ka = np.where(t_arr <= 0.0, 0.0, current_shape)
        di_dt = np.where(t_arr <= 0.0, 0.0, di_dt_shape)

        if t_arr.size == 0:
            return current_ka, di_dt, 0.0

        max_di_dt = float(np.max(np.abs(di_dt)))
        if t_arr.size > 1:
            idx = int(np.argmax(np.abs(di_dt)))
            left_idx = max(0, idx - 1)
            right_idx = min(int(t_arr.size) - 1, idx + 1)
            a_br = float(min(t_arr[left_idx], t_arr[right_idx]))
            b_br = float(max(t_arr[left_idx], t_arr[right_idx]))

            scalar_fn = lambda t_val: _heidler_scalar_di_dt(
                t_val, peak_f, tau1, tau2, eta, n
            )
            if b_br > a_br:
                max_di_dt = max(
                    max_di_dt, _golden_section_max_abs(scalar_fn, a_br, b_br)
                )

            t_min = float(np.min(t_arr))
            t_max = float(np.max(t_arr))
            front_lo = max(0.0, t_min)
            front_hi = min(t_max, 2.0 * tau1)
            if front_hi > front_lo:
                max_di_dt = max(
                    max_di_dt, _golden_section_max_abs(scalar_fn, front_lo, front_hi)
                )

        return current_ka, di_dt, max_di_dt

    def calculate_lemp_induction(
        self,
        waveform: LEMPWaveformSpecification,
        shield: ShieldingGrid,
        loop: InternalCableLoop,
    ) -> LEMPTransientResult:
        """
        Evaluate LEMP magnetic field attenuation and induced loop voltage per
        IEC 62305-4:2024 Annex A (pp. 54-55, Table A.4, Eq. A.6-A.10, Eq. A.14-A.15).
        """
        if (
            isinstance(waveform.num_time_steps, bool)
            or not isinstance(waveform.num_time_steps, int)
            or waveform.num_time_steps < 2
        ):
            raise ValueError(
                f"num_time_steps must be an integer >= 2, got {waveform.num_time_steps!r}."
            )
        t_end_us = _check_positive_finite("t_end_us", waveform.t_end_us)
        peak_ka = _check_positive_finite("peak_current_ka", waveform.peak_current_ka)
        n_steps = int(waveform.num_time_steps)

        shield._validate_shielding_grid()
        s_a_m = _check_positive_finite(
            "center_distance_from_down_conductor_m",
            loop.center_distance_from_down_conductor_m,
        )
        a_loop = _check_positive_finite("loop_area_m2", loop.loop_area_m2)
        uw_kv = _check_positive_finite(
            "equipment_withstand_uw_kv", loop.equipment_withstand_uw_kv
        )

        t_us = np.linspace(0.0, t_end_us, n_steps)
        i_ka, di_dt_ka_us, _ = self.evaluate_heidler_current(
            t_us, waveform.stroke_type, peak_ka
        )

        # Fine internal grid independent of num_time_steps for continuous peak evaluation
        t_fine_us = np.linspace(0.0, t_end_us, _INTERNAL_PEAK_GRID_POINTS)
        i_fine_ka, di_dt_fine_ka_us, max_di_dt = self.evaluate_heidler_current(
            t_fine_us, waveform.stroke_type, peak_ka
        )

        # Eq. (A.6): Peak unattenuated magnetic field H_0 = I_0 / (2 * pi * s_a) [A/m]
        h_unshielded_fine_a_m = (i_fine_ka * 1e3) / (2.0 * np.pi * s_a_m)
        peak_h_unshielded = float(np.max(h_unshielded_fine_a_m))

        warnings: List[str] = []
        if shield.is_shielded:
            assert (
                shield.mesh_width_w_m is not None
                and shield.rod_radius_m is not None
                and shield.material is not None
            )
            if shield.mesh_width_w_m > _MAX_RECOMMENDED_MESH_WIDTH_M:
                warnings.append(
                    f"Spatial shield mesh width w_m = {shield.mesh_width_w_m:.2f} m exceeds "
                    f"{_MAX_RECOMMENDED_MESH_WIDTH_M:.1f} m; wide spatial grids provide reduced "
                    "or zero magnetic-field attenuation per IEC 62305-4:2024 Annex A."
                )

        if not shield.is_shielded:
            sf_db = 0.0
            kms = 1.0
            safety_distance_m = 0.0
            k_source: Literal["IEC 62305-4:2024 Table A.4", "override"] = (
                _K_SOURCE_IEC_2024
            )
        elif shield.shielding_factor_override_db is not None:
            assert shield.mesh_width_w_m is not None
            sf_db = float(shield.shielding_factor_override_db)
            kms = float(10.0 ** (-sf_db / 20.0))
            safety_distance_m = _safety_distance_dsf_m(shield.mesh_width_w_m, sf_db)
            k_source = _K_SOURCE_OVERRIDE
        else:
            assert (
                shield.mesh_width_w_m is not None
                and shield.rod_radius_m is not None
                and shield.material is not None
            )
            sf_db = _shielding_factor_db(
                w_m=shield.mesh_width_w_m,
                r_c=shield.rod_radius_m,
                stroke_type=waveform.stroke_type,
                bonded=shield.meshed_bonding_network,
                material=shield.material,
            )
            kms = float(10.0 ** (-sf_db / 20.0))
            safety_distance_m = _safety_distance_dsf_m(shield.mesh_width_w_m, sf_db)
            k_source = _K_SOURCE_IEC_2024

        # Eq. (A.10): H_1 = H_0 / 10^(SF / 20) = H_0 * K_MS
        peak_h_shielded = float(peak_h_unshielded * kms)

        # Faraday induced electromotive force u_i(t) (uniform-field approximation, b << s_a)
        # di/dt is in kA/us = 10^3 A / 10^-6 s = 10^9 A/s
        loop_coupling_v_per_ka_us = (
            self.MU_0 * kms * (a_loop / (2.0 * np.pi * s_a_m)) * 1e9
        )
        u_induced_kv = np.abs(loop_coupling_v_per_ka_us * di_dt_ka_us) * 1e-3

        u_fine_peak_kv = float(
            np.max(np.abs(loop_coupling_v_per_ka_us * di_dt_fine_ka_us)) * 1e-3
        )
        u_refined_peak_kv = float(abs(loop_coupling_v_per_ka_us * max_di_dt) * 1e-3)
        peak_induced_kv = max(u_fine_peak_kv, u_refined_peak_kv)

        protected = peak_induced_kv <= uw_kv
        status = (
            "COMPLIANT_WITHIN_WITHSTAND" if protected else "EXCEEDS_WITHSTAND_HAZARD"
        )

        insights = [
            f"Heidler surge waveform '{waveform.stroke_type}': Peak current {peak_ka:.1f} kA, max steepness di/dt = {max_di_dt:.2f} kA/us.",
            (
                f"Magnetic field at s_a = {s_a_m:.1f} m: H0 = {peak_h_unshielded:.1f} A/m -> "
                f"H1 = {peak_h_shielded:.1f} A/m (SF = {sf_db:.2f} dB, K_MS = {kms:.4f}, "
                f"d_SF/n = {safety_distance_m:.2f} m, source = {k_source})."
            ),
            f"Induced loop voltage: Peak {peak_induced_kv:.2f} kV vs Equipment withstand Uw = {uw_kv:.2f} kV.",
            "Mitigation recommendation: Reduce loop area or add Type 3 fine surge protection."
            if not protected
            else "Equipment protected by existing shielding and spatial separation.",
        ]

        # Downsample time series for lightweight API/UI serialization
        sample_step = max(1, len(t_us) // 50)
        return LEMPTransientResult(
            stroke_type=waveform.stroke_type,
            peak_current_ka=peak_ka,
            max_di_dt_ka_per_us=round(max_di_dt, 3),
            unattenuated_peak_h_field_a_per_m=round(peak_h_unshielded, 1),
            shielded_peak_h_field_a_per_m=round(peak_h_shielded, 1),
            grid_shielding_factor_kms=kms,
            shielding_factor_db=round(sf_db, 4),
            safety_distance_m=round(safety_distance_m, 4),
            k_source=k_source,
            peak_induced_voltage_kv=round(peak_induced_kv, 3),
            equipment_withstand_uw_kv=uw_kv,
            equipment_protected=protected,
            status=status,
            time_series_us=[round(float(t), 2) for t in t_us[::sample_step]],
            current_waveform_ka=[round(float(i), 2) for i in i_ka[::sample_step]],
            induced_voltage_waveform_kv=[
                round(float(u), 3) for u in u_induced_kv[::sample_step]
            ],
            warnings=warnings,
            engineering_insights=insights,
        )
