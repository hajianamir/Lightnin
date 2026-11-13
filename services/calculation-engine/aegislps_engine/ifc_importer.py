"""Clean-room ISO-10303-21 (IFC STEP) bounding-box importer (Step 4.4, H13).

Parses 3D `IFCCARTESIANPOINT` control points from the STEP `DATA` section using
the Python standard library only, derives axis-aligned bounding-box dimensions,
and fails closed (`parsed: False`) when no usable 3D geometry is present.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

_DATA_SECTION_RE = re.compile(r"\bDATA\s*;(.*?)\bENDSEC\s*;", re.IGNORECASE | re.DOTALL)
_CARTESIAN_KEYWORD_RE = re.compile(r"\bIFCCARTESIANPOINT\b", re.IGNORECASE)
_CARTESIAN_POINT_RE = re.compile(
    r"\bIFCCARTESIANPOINT\s*\(\s*\(([^()]*)\)\s*\)", re.IGNORECASE
)
_SI_LENGTH_UNIT_RE = re.compile(
    r"\bIFCSIUNIT\s*\(\s*[^,]+,\s*\.LENGTHUNIT\.\s*,\s*(\.[A-Z_]+\.|\$)\s*,\s*\.METRE\.\s*\)",
    re.IGNORECASE,
)
_IFCROOF_RE = re.compile(r"\bIFCROOF\s*\((.*?)\)\s*;", re.IGNORECASE | re.DOTALL)

_SI_PREFIX_SCALE: Dict[str, float] = {
    "$": 1.0,
    ".METRE.": 1.0,
    ".DECI.": 0.1,
    ".CENTI.": 0.01,
    ".MILLI.": 0.001,
}

_ROOF_ENUM_MAP: Dict[str, str] = {
    ".FLAT_ROOF.": "flat",
    ".GABLE_ROOF.": "gable",
    ".HIP_ROOF.": "hip",
}

_DESIGNER_REVIEW_WARNING = (
    "Imported geometry must be reviewed by qualified designer before calculations."
)
_BBOX_ESTIMATE_WARNING = (
    "Dimensions are an axis-aligned bounding-box estimate from IFCCARTESIANPOINT "
    "control points, not a full IFC placement or BREP geometry evaluation."
)


def _failed_parse(error: str, points_used: int = 0) -> Dict[str, Any]:
    return {
        "parsed": False,
        "error": error,
        "points_used": points_used,
        "detected_building": None,
        "warnings": [_DESIGNER_REVIEW_WARNING],
    }


def _detect_length_scale(data_section: str) -> Tuple[float, Optional[str]]:
    matches = _SI_LENGTH_UNIT_RE.findall(data_section)
    if not matches:
        return 1.0, None
    prefix = matches[0].upper()
    if prefix in _SI_PREFIX_SCALE:
        return _SI_PREFIX_SCALE[prefix], None
    return (
        1.0,
        f"Unrecognized IFCSIUNIT prefix {prefix}; coordinates interpreted in metres.",
    )


def _derive_roof_type(data_section: str) -> Optional[str]:
    roof_matches = _IFCROOF_RE.findall(data_section)
    if not roof_matches:
        return None
    detected: set[str] = set()
    for args_str in roof_matches:
        tokens = [tok.strip().upper() for tok in args_str.split(",") if tok.strip()]
        if not tokens:
            return None
        last_tok = tokens[-1]
        mapped = _ROOF_ENUM_MAP.get(last_tok)
        if mapped is None:
            return None
        detected.add(mapped)
    if len(detected) == 1:
        return next(iter(detected))
    return None


class IFCImporter:
    @staticmethod
    def parse_ifc_building_elements(file_content: bytes) -> dict:
        """
        Derive axis-aligned building dimensions from ISO-10303-21 IFC STEP content.
        """
        if not isinstance(file_content, (bytes, bytearray)):
            raise ValueError("IFC payload must be bytes.")
        if len(file_content) == 0:
            raise ValueError("IFC payload must not be empty (0 bytes).")
        stripped = bytes(file_content).lstrip()
        if not stripped.startswith(b"ISO-10303-21"):
            raise ValueError(
                "Invalid IFC STEP header: payload must start with 'ISO-10303-21'."
            )

        try:
            text = stripped.decode("utf-8")
        except UnicodeDecodeError:
            return _failed_parse("IFC payload is not valid UTF-8 STEP text.")

        uncommented = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        data_match = _DATA_SECTION_RE.search(uncommented)
        if data_match is None:
            return _failed_parse("IFC STEP payload contains no DATA section.")

        data_section = data_match.group(1)
        total_keyword_hits = len(_CARTESIAN_KEYWORD_RE.findall(data_section))
        point_matches = list(_CARTESIAN_POINT_RE.finditer(data_section))
        if total_keyword_hits != len(point_matches):
            return _failed_parse(
                "Malformed IFCCARTESIANPOINT coordinate list in IFC DATA section."
            )
        if not point_matches:
            return _failed_parse(
                "No IFCCARTESIANPOINT entities found in IFC DATA section."
            )

        scale, unit_warning = _detect_length_scale(data_section)
        points_3d: List[Tuple[float, float, float]] = []

        for match in point_matches:
            raw_coords = [tok.strip() for tok in match.group(1).split(",")]
            if len(raw_coords) not in (2, 3) or any(tok == "" for tok in raw_coords):
                return _failed_parse(
                    "IFCCARTESIANPOINT must contain 2 or 3 numeric coordinates."
                )
            parsed_coords: List[float] = []
            for tok in raw_coords:
                try:
                    val = float(tok)
                except ValueError:
                    return _failed_parse(
                        f"Non-numeric coordinate {tok!r} in IFCCARTESIANPOINT."
                    )
                if not math.isfinite(val):
                    return _failed_parse(
                        "Non-finite coordinate value encountered in IFCCARTESIANPOINT."
                    )
                parsed_coords.append(val * scale)

            if len(parsed_coords) == 3:
                points_3d.append(
                    (parsed_coords[0], parsed_coords[1], parsed_coords[2])
                )

        if not points_3d:
            return _failed_parse(
                "No 3D IFCCARTESIANPOINT((x, y, z)) entities found to determine building height."
            )

        xs = [pt[0] for pt in points_3d]
        ys = [pt[1] for pt in points_3d]
        zs = [pt[2] for pt in points_3d]

        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        dz = max(zs) - min(zs)

        if dx <= 0.0 or dy <= 0.0 or dz <= 0.0:
            return _failed_parse(
                "IFCCARTESIANPOINT coordinates have zero extent along at least one axis; "
                "cannot derive positive 3D building dimensions.",
                points_used=len(points_3d),
            )

        length_m = max(dx, dy)
        width_m = min(dx, dy)
        height_m = dz

        warnings: List[str] = [
            _DESIGNER_REVIEW_WARNING,
            _BBOX_ESTIMATE_WARNING,
        ]
        if unit_warning is not None:
            warnings.append(unit_warning)

        roof_type = _derive_roof_type(data_section)
        if roof_type is None:
            warnings.append(
                "Roof type could not be derived from IFC entities; roof_type is null "
                "and must be specified by a qualified designer."
            )

        return {
            "parsed": True,
            "points_used": len(points_3d),
            "detected_building": {
                "length_m": length_m,
                "width_m": width_m,
                "height_m": height_m,
                "roof_type": roof_type,
            },
            "warnings": warnings,
        }
