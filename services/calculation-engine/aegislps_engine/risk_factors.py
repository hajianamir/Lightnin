"""Shared IEC 62305-2:2024 risk factor lookups and formulas.

Implements Annex B (Tables B.3, B.4, B.5, B.6, B.7 and Eq. B.4) and Annex C
(Table C.2 upper-bound default loss fractions) as the single source of truth
for ``risk.py`` and ``comprehensive_risk.py``.
"""

from dataclasses import dataclass
import math
from typing import Dict, Optional, Tuple, Union


@dataclass(frozen=True)
class LossValues:
    """Upper-bound typical mean loss values from IEC 62305-2:2024 Table C.2 (p. 73)."""

    l_t: float
    l_d: float
    l_f1: float
    l_f2: float
    l_o1: float
    l_o2: float

    @property
    def L_T(self) -> float:
        return self.l_t

    @property
    def L_D(self) -> float:
        return self.l_d

    @property
    def L_F1(self) -> float:
        return self.l_f1

    @property
    def L_F2(self) -> float:
        return self.l_f2

    @property
    def L_O1(self) -> float:
        return self.l_o1

    @property
    def L_O2(self) -> float:
        return self.l_o2

    def __getitem__(self, key: str) -> float:
        key_map = {
            "l_t": self.l_t,
            "L_T": self.l_t,
            "l_d": self.l_d,
            "L_D": self.l_d,
            "l_f1": self.l_f1,
            "L_F1": self.l_f1,
            "l_f2": self.l_f2,
            "L_F2": self.l_f2,
            "l_o1": self.l_o1,
            "L_O1": self.l_o1,
            "l_o2": self.l_o2,
            "L_O2": self.l_o2,
        }
        if key not in key_map:
            raise KeyError(key)
        return key_map[key]


# IEC 62305-2:2024 Table B.3 (p. 56) — Probability P_LPS
_UNPROTECTED_CLASSES = ("none", "unprotected")
_VALID_PROTECTION_VARIANTS = (
    "standard",
    "framework_natural_downconductor",
    "metal_roof_full_protection",
)
_TABLE_B3_STANDARD_P_LPS: Dict[str, float] = {
    "IV": 0.2,    # IEC 62305-2:2024 Table B.3, row 2: Protected by LPS Class IV
    "III": 0.1,   # IEC 62305-2:2024 Table B.3, row 3: Protected by LPS Class III
    "II": 0.05,   # IEC 62305-2:2024 Table B.3, row 4: Protected by LPS Class II
    "I": 0.02,    # IEC 62305-2:2024 Table B.3, row 5: Protected by LPS Class I
}
_TABLE_B3_CLASS_I_VARIANTS: Dict[str, float] = {
    # IEC 62305-2:2024 Table B.3, row 6: LPS I + continuous metal/RC framework as natural down-conductor
    "framework_natural_downconductor": 0.01,
    # IEC 62305-2:2024 Table B.3, row 7: LPS I + metal roof + complete roof air-termination + continuous framework
    "metal_roof_full_protection": 0.001,
}

# IEC 62305-2:2024 Table B.4 (p. 57) — Probability P_S
_TABLE_B4_P_S: Dict[str, float] = {
    "wood_masonry": 1.0,                       # IEC 62305-2:2024 Table B.4, row 1: Wood and masonry
    "continuous_rc_or_metal_framework": 0.5,   # IEC 62305-2:2024 Table B.4, row 2: Continuous RC or interconnected metal framework
}

# IEC 62305-2:2024 Table B.5 (p. 58) — Reduction factor r_p
_TABLE_B5_R_P: Dict[str, float] = {
    "none": 1.0,               # IEC 62305-2:2024 Table B.5, row 1: No provisions (or if in doubt per NOTE)
    "passive_or_manual": 0.5,  # IEC 62305-2:2024 Table B.5, row 2: Extinguishers / manual extinguishing / manual alarm / hydrants / compartments / escape routes
    "automatic": 0.2,          # IEC 62305-2:2024 Table B.5, row 3: Fixed automatic extinguishing or protected automatic alarm (< 10 min)
}

# IEC 62305-2:2024 Table B.6 (p. 58) — Reduction factor r_f
_TABLE_B6_R_F: Dict[str, float] = {
    "explosion_zone_0_20": 1.0,    # IEC 62305-2:2024 Table B.6, row 1: Explosion — Zones 0, 20 and solid explosive
    "explosion_zone_1_21": 1e-1,   # IEC 62305-2:2024 Table B.6, row 2: Explosion — Zones 1, 21
    "explosion_zone_2_22": 1e-3,   # IEC 62305-2:2024 Table B.6, row 3: Explosion — Zones 2, 22
    "fire_high": 1e-1,             # IEC 62305-2:2024 Table B.6, row 4: Fire — High
    "fire_ordinary": 1e-2,         # IEC 62305-2:2024 Table B.6, row 5: Fire — Ordinary
    "fire_low": 1e-3,              # IEC 62305-2:2024 Table B.6, row 6: Fire — Low
    "none": 0.0,                   # IEC 62305-2:2024 Table B.6, row 7: Explosion or fire — None
}

# Exact legacy float mapping for fire_risk_rf -> Table B.6 level (zones 1/21 and 2/22 require explicit level)
_FIRE_RISK_FLOAT_MAP: Tuple[Tuple[float, str], ...] = (
    (1.0, "explosion_zone_0_20"),  # IEC 62305-2:2024 Table B.6, row 1
    (1e-1, "fire_high"),           # IEC 62305-2:2024 Table B.6, row 4
    (1e-2, "fire_ordinary"),       # IEC 62305-2:2024 Table B.6, row 5
    (1e-3, "fire_low"),            # IEC 62305-2:2024 Table B.6, row 6
    (0.0, "none"),                 # IEC 62305-2:2024 Table B.6, row 7
)

# IEC 62305-2:2024 Table B.7 (p. 60) — Typical values of P_SPD (LV system)
# S1 covers both S1a (inductive, 8/20 µs) and S1b (resistive, 10/350 µs) per Clause B.5 NOTE 2.
_VALID_SPD_SOURCES = ("S1", "S2", "S3", "S4")
_TABLE_B7_NO_SPD: float = 1.0  # IEC 62305-2:2024 Table B.7, row 1: No SPDs (all sources S1, S2, S3, S4)
_TABLE_B7_BY_SOURCE_AND_LPL: Dict[str, Dict[str, float]] = {
    "S1": {
        "IV": 0.05,   # IEC 62305-2:2024 Table B.7, row 2: LPL III–IV, S1a (5 kA 8/20 µs) & S1b (12.5 kA 10/350 µs)
        "III": 0.05,  # IEC 62305-2:2024 Table B.7, row 2: LPL III–IV, S1a (5 kA 8/20 µs) & S1b (12.5 kA 10/350 µs)
        "II": 0.02,   # IEC 62305-2:2024 Table B.7, row 3: LPL II, S1a (7.5 kA 8/20 µs) & S1b (18.75 kA 10/350 µs)
        "I": 0.01,    # IEC 62305-2:2024 Table B.7, row 4: LPL I, S1a (10 kA 8/20 µs) & S1b (25 kA 10/350 µs)
    },
    "S2": {
        "IV": 0.05,   # IEC 62305-2:2024 Table B.7, row 2: LPL III–IV, S2 (0.1 kA 8/20 µs)
        "III": 0.05,  # IEC 62305-2:2024 Table B.7, row 2: LPL III–IV, S2 (0.1 kA 8/20 µs)
        "II": 0.02,   # IEC 62305-2:2024 Table B.7, row 3: LPL II, S2 (0.15 kA 8/20 µs)
        "I": 0.01,    # IEC 62305-2:2024 Table B.7, row 4: LPL I, S2 (0.2 kA 8/20 µs)
    },
    "S3": {
        "IV": 0.05,   # IEC 62305-2:2024 Table B.7, row 2: LPL III–IV, S3 (5 kA 10/350 µs)
        "III": 0.05,  # IEC 62305-2:2024 Table B.7, row 2: LPL III–IV, S3 (5 kA 10/350 µs)
        "II": 0.02,   # IEC 62305-2:2024 Table B.7, row 3: LPL II, S3 (7.5 kA 10/350 µs)
        "I": 0.01,    # IEC 62305-2:2024 Table B.7, row 4: LPL I, S3 (10 kA 10/350 µs)
    },
    "S4": {
        "IV": 0.05,   # IEC 62305-2:2024 Table B.7, row 2: LPL III–IV, S4 (0.3 kA 8/20 µs)
        "III": 0.05,  # IEC 62305-2:2024 Table B.7, row 2: LPL III–IV, S4 (0.3 kA 8/20 µs)
        "II": 0.02,   # IEC 62305-2:2024 Table B.7, row 3: LPL II, S4 (0.45 kA 8/20 µs)
        "I": 0.01,    # IEC 62305-2:2024 Table B.7, row 4: LPL I, S4 (0.6 kA 8/20 µs)
    },
}
_TABLE_B7_BETTER_THAN_LPL_I_S2_S4: Tuple[Tuple[float, float], ...] = (
    (2.5, 1e-4),    # IEC 62305-2:2024 Table B.7, row 5: Better than LPL I, 2.5 kA 8/20 µs (S4, S2 only)
    (3.75, 5e-5),   # IEC 62305-2:2024 Table B.7, row 6: Better than LPL I, 3.75 kA 8/20 µs (S4, S2 only)
    (5.0, 1e-5),    # IEC 62305-2:2024 Table B.7, row 7: Better than LPL I, 5 kA 8/20 µs (S4, S2 only)
)

# IEC 62305-2:2024 Table C.2 (p. 73) — Typical mean loss values (upper bound of each range per Clause C.2)
_TABLE_C2_UPPER_BOUND: Dict[str, LossValues] = {
    # IEC 62305-2:2024 Table C.2, row 1 (footnote a): Very high loss or highly critical structures/risk zones
    "very_high": LossValues(
        l_t=1e-2,   # Table C.2 row 1, col L_T: 10^-2
        l_d=1e-1,   # Table C.2 row 1, col L_D: upper bound of 10^-2 – 10^-1
        l_f1=2e-1,  # Table C.2 row 1, col L_F1: upper bound of 10^-2 – 2×10^-1
        l_f2=2e-1,  # Table C.2 row 1, col L_F2: upper bound of 10^-2 – 2×10^-1
        l_o1=1e-2,  # Table C.2 row 1, col L_O1: upper bound of 10^-3 – 10^-2
        l_o2=1e-2,  # Table C.2 row 1, col L_O2: upper bound of 10^-3 – 10^-2
    ),
    # IEC 62305-2:2024 Table C.2, row 2 (footnote b): High loss or critical structures/risk zones
    "high": LossValues(
        l_t=1e-2,   # Table C.2 row 2, col L_T: 10^-2
        l_d=1e-1,   # Table C.2 row 2, col L_D: upper bound of 10^-2 – 10^-1
        l_f1=1e-1,  # Table C.2 row 2, col L_F1: upper bound of 10^-2 – 10^-1
        l_f2=1e-1,  # Table C.2 row 2, col L_F2: upper bound of 10^-2 – 10^-1
        l_o1=1e-3,  # Table C.2 row 2, col L_O1: upper bound of 10^-4 – 10^-3
        l_o2=1e-3,  # Table C.2 row 2, col L_O2: upper bound of 10^-4 – 10^-3
    ),
    # IEC 62305-2:2024 Table C.2, row 3 (footnote c): Normal loss structures/risk zones
    "normal": LossValues(
        l_t=1e-2,   # Table C.2 row 3, col L_T: 10^-2
        l_d=1e-1,   # Table C.2 row 3, col L_D: upper bound of 10^-2 – 10^-1
        l_f1=5e-2,  # Table C.2 row 3, col L_F1: upper bound of 5×10^-3 – 5×10^-2
        l_f2=5e-2,  # Table C.2 row 3, col L_F2: upper bound of 5×10^-3 – 5×10^-2
        l_o1=5e-4,  # Table C.2 row 3, col L_O1: upper bound of 10^-5 – 5×10^-4 (footnote e)
        l_o2=5e-4,  # Table C.2 row 3, col L_O2: upper bound of 10^-5 – 5×10^-4 (footnote e)
    ),
    # IEC 62305-2:2024 Table C.2, row 4 (footnote d): Low-loss structures/risk zones
    "low": LossValues(
        l_t=1e-2,   # Table C.2 row 4, col L_T: 10^-2
        l_d=1e-1,   # Table C.2 row 4, col L_D: upper bound of 10^-2 – 10^-1
        l_f1=2e-2,  # Table C.2 row 4, col L_F1: upper bound of 2×10^-3 – 2×10^-2
        l_f2=2e-2,  # Table C.2 row 4, col L_F2: upper bound of 2×10^-3 – 2×10^-2
        l_o1=1e-4,  # Table C.2 row 4, col L_O1: upper bound of 10^-5 – 10^-4 (footnote e)
        l_o2=1e-4,  # Table C.2 row 4, col L_O2: upper bound of 10^-5 – 10^-4 (footnote e)
    ),
}


def _validate_lps_class(lps_class: Optional[str]) -> Optional[str]:
    """Validate ``lps_class`` against Table B.3 / B.7 classes."""
    if lps_class is None:
        return None
    if not isinstance(lps_class, str):
        raise ValueError(f"Invalid lps_class type: {type(lps_class).__name__}")
    if lps_class in _UNPROTECTED_CLASSES or lps_class in _TABLE_B3_STANDARD_P_LPS:
        return lps_class
    raise ValueError(
        f"Unknown lps_class {lps_class!r}; expected one of 'I', 'II', 'III', 'IV', 'none', 'unprotected', or None."
    )


def p_lps(lps_class: Optional[str], protection_variant: str = "standard") -> float:
    """Return probability ``P_LPS`` per IEC 62305-2:2024 Table B.3 (p. 56)."""
    if not isinstance(protection_variant, str) or protection_variant not in _VALID_PROTECTION_VARIANTS:
        raise ValueError(
            f"Unknown protection_variant {protection_variant!r}; expected one of {_VALID_PROTECTION_VARIANTS}."
        )
    cls = _validate_lps_class(lps_class)

    if protection_variant != "standard":
        if cls != "I":
            raise ValueError(
                f"protection_variant {protection_variant!r} is valid only for lps_class='I', got {lps_class!r}."
            )
        return _TABLE_B3_CLASS_I_VARIANTS[protection_variant]

    if cls is None or cls in _UNPROTECTED_CLASSES:
        return 1.0  # IEC 62305-2:2024 Table B.3, row 1: Structure or exposed areas not protected
    return _TABLE_B3_STANDARD_P_LPS[cls]


def p_s(structure_type: str = "wood_masonry") -> float:
    """Return probability ``P_S`` per IEC 62305-2:2024 Table B.4 (p. 57)."""
    if not isinstance(structure_type, str) or structure_type not in _TABLE_B4_P_S:
        raise ValueError(
            f"Unknown structure_type {structure_type!r}; expected one of {tuple(_TABLE_B4_P_S)}."
        )
    return _TABLE_B4_P_S[structure_type]


def r_p(provisions: str = "none") -> float:
    """Return fire-provision reduction factor ``r_p`` per IEC 62305-2:2024 Table B.5 (p. 58)."""
    if not isinstance(provisions, str) or provisions not in _TABLE_B5_R_P:
        raise ValueError(
            f"Unknown provisions {provisions!r}; expected one of {tuple(_TABLE_B5_R_P)}."
        )
    return _TABLE_B5_R_P[provisions]


def map_fire_risk_rf(fire_risk_rf: Union[int, float]) -> str:
    """Map numeric ``fire_risk_rf`` strictly to its IEC 62305-2:2024 Table B.6 level."""
    if isinstance(fire_risk_rf, bool) or not isinstance(fire_risk_rf, (int, float)):
        raise ValueError(f"fire_risk_rf must be a real number, got {fire_risk_rf!r}.")
    val = float(fire_risk_rf)
    if not math.isfinite(val) or val < 0.0:
        raise ValueError(f"fire_risk_rf must be finite and non-negative, got {fire_risk_rf!r}.")
    for ref_val, level in _FIRE_RISK_FLOAT_MAP:
        if val == ref_val:
            return level
    raise ValueError(
        f"Unsupported fire_risk_rf={fire_risk_rf!r}; allowed Table B.6 float values are {{1, 1e-1, 1e-2, 1e-3, 0}} "
        "(explosion zones 1/21 and 2/22 require an explicit fire_risk_level)."
    )


def r_f(fire_risk_level: Union[str, int, float]) -> float:
    """Return fire/explosion reduction factor ``r_f`` per IEC 62305-2:2024 Table B.6 (p. 58)."""
    if isinstance(fire_risk_level, str):
        if fire_risk_level not in _TABLE_B6_R_F:
            raise ValueError(
                f"Unknown fire_risk_level {fire_risk_level!r}; expected one of {tuple(_TABLE_B6_R_F)}."
            )
        return _TABLE_B6_R_F[fire_risk_level]
    mapped_level = map_fire_risk_rf(fire_risk_level)
    return _TABLE_B6_R_F[mapped_level]


def p_b(
    lps_class: Optional[str],
    fire_risk_level: Union[str, int, float],
    structure_type: str = "wood_masonry",
    protection_variant: str = "standard",
    provisions: str = "none",
) -> float:
    """Return physical-damage probability ``P_B = P_S * P_LPS * r_p * r_f`` per Eq. (B.4) (p. 57)."""
    ps_val = p_s(structure_type)
    plps_val = p_lps(lps_class, protection_variant)
    rp_val = r_p(provisions)
    rf_val = r_f(fire_risk_level)
    return float(ps_val * plps_val * rp_val * rf_val)


def p_spd(
    lps_class: Optional[str],
    spd_present: bool,
    spd_coordinated: bool,
    source: str = "S1",
    enhanced_spd_current_ka: Optional[float] = None,
) -> float:
    """Return internal-system failure probability ``P_SPD`` per IEC 62305-2:2024 Table B.7 (p. 60).

    ``source`` must be one of ``{"S1", "S2", "S3", "S4"}``; ``"S1"`` covers both
    inductive (``S1a``) and resistive (``S1b``) coupling per Clause B.5 NOTE 2.
    """
    if not isinstance(source, str) or source not in _VALID_SPD_SOURCES:
        raise ValueError(
            f"Unknown SPD source {source!r}; expected one of {_VALID_SPD_SOURCES} "
            "(S1 covers both S1a and S1b per Clause B.5 NOTE 2)."
        )
    if not isinstance(spd_present, bool) or not isinstance(spd_coordinated, bool):
        raise ValueError("spd_present and spd_coordinated must be booleans.")
    if not spd_present and spd_coordinated:
        raise ValueError("spd_coordinated cannot be True when spd_present is False.")

    cls = _validate_lps_class(lps_class)

    if enhanced_spd_current_ka is not None:
        if isinstance(enhanced_spd_current_ka, bool) or not isinstance(enhanced_spd_current_ka, (int, float)):
            raise ValueError(f"enhanced_spd_current_ka must be numeric, got {enhanced_spd_current_ka!r}.")
        ka_val = float(enhanced_spd_current_ka)
        if not math.isfinite(ka_val) or ka_val <= 0.0:
            raise ValueError(f"enhanced_spd_current_ka must be finite and positive, got {enhanced_spd_current_ka!r}.")
        if not (spd_present and spd_coordinated) or cls != "I":
            raise ValueError("Better-than-LPL-I SPD ratings require lps_class='I' with coordinated SPDs.")
        if source not in ("S2", "S4"):
            raise ValueError(
                f"Better-than-LPL-I Table B.7 rows are defined only for sources 'S2' and 'S4', got {source!r}."
            )
        for ref_ka, ref_pspd in _TABLE_B7_BETTER_THAN_LPL_I_S2_S4:
            if ka_val == ref_ka:
                return ref_pspd
        raise ValueError(
            f"Unsupported enhanced_spd_current_ka={enhanced_spd_current_ka!r}; allowed Table B.7 values are 2.5, 3.75, 5.0 kA."
        )

    if not spd_present or not spd_coordinated:
        return _TABLE_B7_NO_SPD
    if cls is None or cls in _UNPROTECTED_CLASSES:
        # IEC 62305-2:2024 Clause B.5 NOTE 1: coordinated SPD reduces P_C only in LPS-protected structures
        return _TABLE_B7_NO_SPD
    return _TABLE_B7_BY_SOURCE_AND_LPL[source][cls]


def loss(category: str) -> LossValues:
    """Return upper-bound loss fractions from IEC 62305-2:2024 Table C.2 (p. 73)."""
    if not isinstance(category, str) or category not in _TABLE_C2_UPPER_BOUND:
        raise ValueError(
            f"Unknown or missing loss category {category!r}; expected one of {tuple(_TABLE_C2_UPPER_BOUND)}."
        )
    return _TABLE_C2_UPPER_BOUND[category]
