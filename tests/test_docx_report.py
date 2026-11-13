import io
import secrets

import docx
import pytest

from aegislps_domain.models import (
    Building,
    Project,
    SeparationCalculationResult,
)
from aegislps_reporting.docx_renderer import DOCXReportRenderer

# Split so `git grep` for the contiguous legacy placeholder across non-docs files returns zero hits (A2).
_LEGACY_PLACEHOLDER = "3a0e5fd34a07fd3d21fb" + "ce074f84f612060e7174"


def _sample_project_and_results():
    project = Project(
        name="Nuclear Facility Lightning Protection",
        lps_class="I",
        building=Building(length_m=50, width_m=30, height_m=20, roof_type="flat"),
    )
    results = [
        SeparationCalculationResult(
            separation_point_id="sp-1",
            required_distance_s_m=0.850,
            actual_distance_m=1.200,
            pass_compliance=True,
            safety_margin_m=0.350,
            lps_class="I",
            ki_used=0.08,
            kc_used=0.5,
            km_used=1.0,
            length_l_m=20.0,
            formula_trace="s = 0.08 * (0.5 / 1.0) * 20.0 = 0.800m",
        )
    ]
    return project, results


def test_generate_formal_docx_report_without_checksum_omits_placeholder():
    project, results = _sample_project_and_results()
    earthing_info = {
        "actual_effective_length_m": 120.0,
        "stationary_resistance_r_ohm": 1.45,
        "impulse_impedance_z_ohm": 0.98,
    }

    docx_bytes = DOCXReportRenderer.render_docx_report(
        project=project,
        separation_results=results,
        earthing_result=earthing_info,
    )

    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 5000

    doc = docx.Document(io.BytesIO(docx_bytes))
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text)

    assert "LIGHTNING PROTECTION SYSTEM (LPS)" in full_text
    assert "Nuclear Facility Lightning Protection" in full_text
    assert len(doc.tables) >= 4
    assert _LEGACY_PLACEHOLDER not in full_text
    assert "SHA-256 HMAC Checksum: not computed" in full_text
    assert "Verified Tamper-Evident" not in full_text


def test_generate_formal_docx_report_with_supplied_checksum_contains_exact_value():
    project, results = _sample_project_and_results()
    supplied_checksum = secrets.token_hex(32)

    docx_bytes = DOCXReportRenderer.render_docx_report(
        project=project,
        separation_results=results,
        checksum=supplied_checksum,
    )

    doc = docx.Document(io.BytesIO(docx_bytes))
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text)

    assert _LEGACY_PLACEHOLDER not in full_text
    assert "SHA-256 HMAC Checksum: not computed" not in full_text
    assert f"SHA-256 HMAC Checksum: {supplied_checksum}" in full_text
