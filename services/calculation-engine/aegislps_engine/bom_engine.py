import math
from typing import Any, List
from pydantic import BaseModel

_VALID_LPS_CLASSES = ("I", "II", "III", "IV")


def _require_positive_finite_float(name: str, val: Any) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(f"{name} must be a finite number > 0, not bool; got {val!r}.")
    fval = float(val)
    if not math.isfinite(fval) or fval <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {val!r}.")
    return fval


def _require_positive_int(name: str, val: Any) -> int:
    if isinstance(val, bool) or not isinstance(val, int):
        raise ValueError(f"{name} must be a strict int >= 1, not bool; got {val!r}.")
    if val < 1:
        raise ValueError(f"{name} must be >= 1, got {val!r}.")
    return val


class BOMItem(BaseModel):
    category: str  # air_termination, down_conductor, earthing, spd, fasteners
    item_code: str
    description: str
    quantity: float
    unit: str  # m, pcs, sets


class InspectionChecklistItem(BaseModel):
    clause: str
    item: str
    criterion: str
    frequency_years: int
    inspection_method: str  # visual, electrical_continuity, soil_resistance


class ProjectBOMResult(BaseModel):
    project_name: str
    lps_class: str
    items: List[BOMItem]
    inspection_schedule: List[InspectionChecklistItem]
    total_components_count: int


class BOMAndLifecycleEngine:
    """
    Automated Bill of Materials (BOM) Takeoff & IEC 62305-3 Table E.2 Periodic Maintenance Checklist Engine.
    """

    def generate_project_bom(
        self,
        project_name: str,
        lps_class: str,
        building_length_m: float,
        building_width_m: float,
        building_height_m: float,
        rod_count: int,
        down_conductor_count: int,
    ) -> ProjectBOMResult:
        if not isinstance(project_name, str) or not project_name.strip():
            raise ValueError(
                f"project_name must be a non-empty string, got {project_name!r}."
            )
        if not isinstance(lps_class, str) or lps_class not in _VALID_LPS_CLASSES:
            raise ValueError(
                f"Unknown LPS class {lps_class!r}; expected one of {_VALID_LPS_CLASSES}."
            )
        b_len = _require_positive_finite_float("building_length_m", building_length_m)
        b_wid = _require_positive_finite_float("building_width_m", building_width_m)
        b_hgt = _require_positive_finite_float("building_height_m", building_height_m)
        n_rods = _require_positive_int("rod_count", rod_count)
        n_dc = _require_positive_int("down_conductor_count", down_conductor_count)

        items = []

        # 1. Air Termination
        items.append(
            BOMItem(
                category="air_termination",
                item_code="AT-ROD-3M-CU",
                description="Air termination rod 3.0m copper-clad steel (16mm dia)",
                quantity=float(n_rods),
                unit="pcs",
            )
        )
        roof_perim_m = 2.0 * (b_len + b_wid)
        items.append(
            BOMItem(
                category="air_termination",
                item_code="COND-50CU-RND",
                description="Copper round conductor 8mm (50 mm2) for roof perimeter ring",
                quantity=round(roof_perim_m * 1.1, 1),
                unit="m",
            )
        )

        # 2. Down Conductors
        dc_len_total = n_dc * b_hgt
        items.append(
            BOMItem(
                category="down_conductor",
                item_code="COND-50CU-RND",
                description="Copper round conductor 8mm (50 mm2) for down conductors",
                quantity=round(dc_len_total * 1.1, 1),
                unit="m",
            )
        )
        items.append(
            BOMItem(
                category="fasteners",
                item_code="CLAMP-DC-SCREW",
                description="Heavy duty conductor fasteners with expansion anchors",
                quantity=float(int(dc_len_total / 0.8)),
                unit="pcs",
            )
        )
        items.append(
            BOMItem(
                category="down_conductor",
                item_code="TEST-JOINT-CU",
                description="Measuring / disconnect test joint box (IP65 rated)",
                quantity=float(n_dc),
                unit="pcs",
            )
        )

        # 3. Earthing System
        earth_ring_len = 2.0 * (b_len + b_wid + 8.0)  # 1m offset around building
        items.append(
            BOMItem(
                category="earthing",
                item_code="EARTH-STRIP-CU",
                description="Type B copper earthing strip 30x3.5mm buried at 0.5m",
                quantity=round(earth_ring_len * 1.05, 1),
                unit="m",
            )
        )
        items.append(
            BOMItem(
                category="earthing",
                item_code="EARTH-ROD-3M",
                description="Type A vertical earth rod 3.0m with driving stud",
                quantity=float(n_dc),
                unit="pcs",
            )
        )

        # 4. SPDs
        items.append(
            BOMItem(
                category="spd",
                item_code="SPD-T1-25KA",
                description="Type 1 Spark Gap SPD (I_imp=25kA 10/350us) for main switchboard",
                quantity=1.0,
                unit="sets",
            )
        )
        items.append(
            BOMItem(
                category="spd",
                item_code="SPD-T2-40KA",
                description="Type 2 Varistor SPD (I_n=20kA, I_max=40kA 8/20us) for sub-boards",
                quantity=2.0,
                unit="sets",
            )
        )

        # IEC 62305-3 Table E.2 Periodic Maintenance Schedule
        # Class I/II: Visual 1 year, Complete electrical 2 years
        # Class III/IV: Visual 2 years, Complete electrical 4 years
        if lps_class in ("I", "II"):
            vis_freq = 1
            elec_freq = 2
        else:  # ("III", "IV") validated above
            vis_freq = 2
            elec_freq = 4

        checklist = [
            InspectionChecklistItem(
                clause="IEC 62305-3 §E.7.2",
                item="Visual conductor inspection",
                criterion="No mechanical detachment, corrosion, or flashover witness marks on conductors",
                frequency_years=vis_freq,
                inspection_method="visual",
            ),
            InspectionChecklistItem(
                clause="IEC 62305-3 §E.7.2",
                item="Bonding continuity measurement",
                criterion="Electrical resistance across all joints and bonding points <= 0.2 ohm",
                frequency_years=elec_freq,
                inspection_method="electrical_continuity",
            ),
            InspectionChecklistItem(
                clause="IEC 62305-3 §E.7.2",
                item="Earthing resistance measurement",
                criterion="Overall earth system resistance <= 10.0 ohm measured at test joints",
                frequency_years=elec_freq,
                inspection_method="soil_resistance",
            ),
            InspectionChecklistItem(
                clause="IEC 62305-4 §E.7.3",
                item="SPD status indicator check",
                criterion="Optical status flags green, no blown surge protection cartridges",
                frequency_years=vis_freq,
                inspection_method="visual",
            ),
        ]

        return ProjectBOMResult(
            project_name=project_name,
            lps_class=lps_class,
            items=items,
            inspection_schedule=checklist,
            total_components_count=len(items),
        )
