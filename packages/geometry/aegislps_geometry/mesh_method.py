import math
from typing import Any, List, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")


def _check_finite_float(name: str, v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name} must be a finite number, not bool; got {v!r}.")
    val = float(v)
    if not math.isfinite(val):
        raise ValueError(f"{name} must be finite, got {v!r}.")
    return val


def _check_nonnegative_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val < 0.0:
        raise ValueError(f"{name} must be >= 0, got {v!r}.")
    return val


def _check_positive_finite_float(name: str, v: Any) -> float:
    val = _check_finite_float(name, v)
    if val <= 0.0:
        raise ValueError(f"{name} must be > 0, got {v!r}.")
    return val


class RoofProtrusion(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str
    x: float
    y: float
    z: float
    height_above_roof_m: float
    is_metallic: bool = True  # unused in validate_mesh_design

    @field_validator("x", "y", "z", mode="before")
    @classmethod
    def _validate_coords(cls, v: Any, info) -> float:
        return _check_finite_float(info.field_name, v)

    @field_validator("height_above_roof_m", mode="before")
    @classmethod
    def _validate_height(cls, v: Any) -> float:
        return _check_nonnegative_finite_float("height_above_roof_m", v)

    @field_validator("is_metallic", mode="before")
    @classmethod
    def _validate_is_metallic(cls, v: Any) -> bool:
        if not isinstance(v, bool):
            raise ValueError(f"is_metallic must be a strict boolean, got {v!r}.")
        return v


class MeshMethodInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    lps_class: str  # I: 5x5m, II: 10x10m, III: 15x15m, IV: 20x20m
    # roof_length_m and roof_width_m are unused in validate_mesh_design; required for API consistency.
    roof_length_m: float
    roof_width_m: float
    mesh_grid_dx_m: float
    mesh_grid_dy_m: float
    has_perimeter_conductor: bool
    protrusions: List[RoofProtrusion] = Field(default_factory=list)

    @field_validator("lps_class", mode="before")
    @classmethod
    def _validate_lps_class(cls, v: Any) -> str:
        if not isinstance(v, str) or v not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {v!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        return v

    @field_validator(
        "roof_length_m",
        "roof_width_m",
        "mesh_grid_dx_m",
        "mesh_grid_dy_m",
        mode="before",
    )
    @classmethod
    def _validate_positive_dimensions(cls, v: Any, info) -> float:
        return _check_positive_finite_float(info.field_name, v)

    @field_validator("has_perimeter_conductor", mode="before")
    @classmethod
    def _validate_perimeter_flag(cls, v: Any) -> bool:
        if not isinstance(v, bool):
            raise ValueError(
                f"has_perimeter_conductor must be a strict boolean, got {v!r}."
            )
        return v


class MeshValidationResult(BaseModel):
    lps_class: str
    max_permitted_mesh_dim_m: float
    actual_mesh_dimensions: Tuple[float, float]
    mesh_size_compliant: bool
    perimeter_conductor_compliant: bool
    unprotected_protrusions_count: int
    is_fully_compliant: bool
    status: str
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class MeshMethodEngine:
    """
    IEC 62305-3 Section 5.2.3 Mesh Method Design & Validation Engine.

    Validates:
    - Standard mesh grid dimensions (Table 2):
      Class I: 5m x 5m
      Class II: 10m x 10m
      Class III: 15m x 15m
      Class IV: 20m x 20m
    - Roof perimeter conductor placement along the outer edge.
    - Protrusion exposure checks: Protrusions above the roof surface cannot be protected
      by a mesh alone and require supplementary air-termination rods or bonding.
    """

    MAX_MESH_DIMENSIONS = {
        "I": 5.0,
        "II": 10.0,
        "III": 15.0,
        "IV": 20.0,
    }

    def validate_mesh_design(self, inp: MeshMethodInput) -> MeshValidationResult:
        if not isinstance(inp.lps_class, str) or inp.lps_class not in self.MAX_MESH_DIMENSIONS:
            raise ValueError(
                f"Unknown LPS class {inp.lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        _check_positive_finite_float("roof_length_m", inp.roof_length_m)
        _check_positive_finite_float("roof_width_m", inp.roof_width_m)
        dx = _check_positive_finite_float("mesh_grid_dx_m", inp.mesh_grid_dx_m)
        dy = _check_positive_finite_float("mesh_grid_dy_m", inp.mesh_grid_dy_m)
        if not isinstance(inp.has_perimeter_conductor, bool):
            raise ValueError(
                f"has_perimeter_conductor must be a strict boolean, got {inp.has_perimeter_conductor!r}."
            )

        max_dim = self.MAX_MESH_DIMENSIONS[inp.lps_class]
        actual_dims = (dx, dy)

        mesh_ok = (dx <= max_dim) and (dy <= max_dim)
        perimeter_ok = inp.has_perimeter_conductor

        warnings = []
        recommendations = []

        if not mesh_ok:
            warnings.append(
                f"Mesh grid spacing ({inp.mesh_grid_dx_m}m x {inp.mesh_grid_dy_m}m) exceeds "
                f"maximum allowable dimension ({max_dim}m x {max_dim}m) for LPS Class {inp.lps_class}."
            )
            recommendations.append(
                f"Reduce mesh conductor spacing to <= {max_dim}m x {max_dim}m."
            )

        if not perimeter_ok:
            warnings.append(
                "Perimeter ring conductor missing along the outer edge of the roof structure."
            )
            recommendations.append(
                "Install closed continuous loop conductor at the roof perimeter."
            )

        unprotected_protrusions = 0
        for prot in inp.protrusions:
            h_prot = _check_nonnegative_finite_float(
                "height_above_roof_m", prot.height_above_roof_m
            )
            if h_prot > 0.3:  # Protrusions > 30cm cannot be protected by roof mesh alone
                unprotected_protrusions += 1
                warnings.append(
                    f"Rooftop protrusion '{prot.id}' (height {h_prot:.2f}m) penetrates mesh plane. "
                    "Must be protected with air-termination rod or direct equipotential bond."
                )

        fully_compliant = mesh_ok and perimeter_ok and (unprotected_protrusions == 0)
        status = "COMPLIANT" if fully_compliant else "NON_COMPLIANT_VIOLATION"

        return MeshValidationResult(
            lps_class=inp.lps_class,
            max_permitted_mesh_dim_m=max_dim,
            actual_mesh_dimensions=actual_dims,
            mesh_size_compliant=mesh_ok,
            perimeter_conductor_compliant=perimeter_ok,
            unprotected_protrusions_count=unprotected_protrusions,
            is_fully_compliant=fully_compliant,
            status=status,
            warnings=warnings,
            recommendations=recommendations,
        )
