import math
from typing import Any, List
from pydantic import BaseModel, ConfigDict, Field, field_validator

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")
# Validated against the installation type already used in this module (plus ASCII facade spelling).
_VALID_AMBIENT_INSTALLATION_TYPES = ("outdoor_façade", "outdoor_facade")
_HVI_SPECS = {
    "HVI_light_75": {
        "s_equiv_air": 0.75,  # meters equivalent separation in air
        "s_equiv_solid": 1.50,  # meters equivalent in solid
        "max_length_m": 25.0,
        "impulse_withstand_kv": 150.0,
    },
    "HVI_standard_90": {
        "s_equiv_air": 0.90,
        "s_equiv_solid": 1.80,
        "max_length_m": 35.0,
        "impulse_withstand_kv": 200.0,
    },
}


def _check_positive_finite_float(name: str, v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name} must be a finite number > 0, not bool; got {v!r}.")
    val = float(v)
    if not math.isfinite(val) or val <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {v!r}.")
    return val


class HVIConductorSelectionInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    lps_class: str
    required_equivalent_separation_s_air_m: float
    down_conductor_route_length_m: float
    hvi_conductor_model: str  # HVI_light_75 (s_equiv=0.75m), HVI_standard_90 (s_equiv=0.90m)
    ambient_installation_type: str

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        return v

    @field_validator(
        "required_equivalent_separation_s_air_m",
        "down_conductor_route_length_m",
        mode="before",
    )
    @classmethod
    def _validate_positive_lengths(cls, v: Any, info) -> float:
        return _check_positive_finite_float(info.field_name, v)

    @field_validator("hvi_conductor_model", mode="before")
    @classmethod
    def _validate_model(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _HVI_SPECS:
            raise ValueError(
                f"Unknown hvi_conductor_model {v!r}; expected one of {tuple(_HVI_SPECS)}."
            )
        return v

    @field_validator("ambient_installation_type", mode="before")
    @classmethod
    def _validate_ambient_type(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_AMBIENT_INSTALLATION_TYPES:
            raise ValueError(
                f"Unknown ambient_installation_type {v!r}; expected one of {_VALID_AMBIENT_INSTALLATION_TYPES}."
            )
        return v


class HVIConductorSelectionResult(BaseModel):
    hvi_conductor_model: str
    equivalent_separation_distance_se_m: float
    required_s_air_m: float
    is_adequate_insulation: bool
    max_permitted_route_length_m: float
    length_limit_exceeded: bool
    requires_capacitive_sealing_ground: bool
    status: str
    technical_specifications: List[str] = Field(default_factory=list)


class HVIConductorAssistant:
    """
    High-Voltage Insulated (HVI) Down-Conductor Selection & Verification Engine.

    Evaluates:
    - High-voltage impulse dielectric withstand (equivalent separation distance in solid insulation s_e)
    - Capacitive semi-conductive shield sheath grounding at sealing ends to control electric field stress
    - Maximum permissible conductor length limits under lightning impulse steepness.
    """

    HVI_SPECS = _HVI_SPECS

    def evaluate_hvi_selection(
        self, inp: HVIConductorSelectionInput
    ) -> HVIConductorSelectionResult:
        if not isinstance(inp.lps_class, str) or inp.lps_class not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {inp.lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        if (
            not isinstance(inp.ambient_installation_type, str)
            or inp.ambient_installation_type not in _VALID_AMBIENT_INSTALLATION_TYPES
        ):
            raise ValueError(
                f"Unknown ambient_installation_type {inp.ambient_installation_type!r}; "
                f"expected one of {_VALID_AMBIENT_INSTALLATION_TYPES}."
            )
        if not isinstance(inp.hvi_conductor_model, str) or inp.hvi_conductor_model not in self.HVI_SPECS:
            raise ValueError(
                f"Unknown hvi_conductor_model {inp.hvi_conductor_model!r}; expected one of {tuple(self.HVI_SPECS)}."
            )
        req_s = _check_positive_finite_float(
            "required_equivalent_separation_s_air_m",
            inp.required_equivalent_separation_s_air_m,
        )
        route_len = _check_positive_finite_float(
            "down_conductor_route_length_m", inp.down_conductor_route_length_m
        )

        spec = self.HVI_SPECS[inp.hvi_conductor_model]

        is_adequate = spec["s_equiv_air"] >= req_s
        len_exceeded = route_len > spec["max_length_m"]

        specs = [
            f"Rated equivalent separation distance in air: s_e = {spec['s_equiv_air']} m.",
            f"Rated impulse withstand voltage: {spec['impulse_withstand_kv']} kV (1.2/50 us waveform).",
            f"Maximum permissible continuous route length: {spec['max_length_m']} m.",
            "Mandatory capacitive control: Outer semi-conductive sheath must be bonded to equipotential bar at sealing end.",
        ]

        if not is_adequate:
            specs.append(
                f"WARNING: Required separation distance ({req_s:.2f}m) exceeds HVI rated s_e ({spec['s_equiv_air']}m). Upgrade to HVI_standard_90 or parallel paths."
            )
        if len_exceeded:
            specs.append(
                f"WARNING: Route length ({route_len}m) exceeds manufacturer max length ({spec['max_length_m']}m)."
            )

        status = (
            "COMPLIANT_APPROVED"
            if (is_adequate and not len_exceeded)
            else "NON_COMPLIANT_HAZARD"
        )

        return HVIConductorSelectionResult(
            hvi_conductor_model=inp.hvi_conductor_model,
            equivalent_separation_distance_se_m=spec["s_equiv_air"],
            required_s_air_m=req_s,
            is_adequate_insulation=is_adequate,
            max_permitted_route_length_m=spec["max_length_m"],
            length_limit_exceeded=len_exceeded,
            requires_capacitive_sealing_ground=True,
            status=status,
            technical_specifications=specs,
        )
