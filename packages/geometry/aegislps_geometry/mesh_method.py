from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

class RoofProtrusion(BaseModel):
    id: str
    x: float
    y: float
    z: float
    height_above_roof_m: float
    is_metallic: bool = True

class MeshMethodInput(BaseModel):
    lps_class: str = "I" # I: 5x5m, II: 10x10m, III: 15x15m, IV: 20x20m
    roof_length_m: float = 30.0
    roof_width_m: float = 20.0
    mesh_grid_dx_m: float = 5.0
    mesh_grid_dy_m: float = 5.0
    has_perimeter_conductor: bool = True
    protrusions: List[RoofProtrusion] = Field(default_factory=list)

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
        "IV": 20.0
    }

    def validate_mesh_design(self, inp: MeshMethodInput) -> MeshValidationResult:
        max_dim = self.MAX_MESH_DIMENSIONS.get(inp.lps_class, 5.0)
        actual_dims = (float(inp.mesh_grid_dx_m), float(inp.mesh_grid_dy_m))

        mesh_ok = (inp.mesh_grid_dx_m <= max_dim) and (inp.mesh_grid_dy_m <= max_dim)
        perimeter_ok = inp.has_perimeter_conductor

        warnings = []
        recommendations = []

        if not mesh_ok:
            warnings.append(
                f"Mesh grid spacing ({inp.mesh_grid_dx_m}m x {inp.mesh_grid_dy_m}m) exceeds "
                f"maximum allowable dimension ({max_dim}m x {max_dim}m) for LPS Class {inp.lps_class}."
            )
            recommendations.append(f"Reduce mesh conductor spacing to <= {max_dim}m x {max_dim}m.")

        if not perimeter_ok:
            warnings.append("Perimeter ring conductor missing along the outer edge of the roof structure.")
            recommendations.append("Install closed continuous loop conductor at the roof perimeter.")

        unprotected_protrusions = 0
        for prot in inp.protrusions:
            if prot.height_above_roof_m > 0.3: # Protrusions > 30cm cannot be protected by roof mesh alone
                unprotected_protrusions += 1
                warnings.append(
                    f"Rooftop protrusion '{prot.id}' (height {prot.height_above_roof_m:.2f}m) penetrates mesh plane. "
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
            recommendations=recommendations
        )
