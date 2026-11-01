import pytest
import io
import docx
from aegislps_domain.models import Project, Building, ConductorNode, SeparationPoint, SeparationCalculationResult
from aegislps_reporting.docx_renderer import DOCXReportRenderer

def test_generate_formal_docx_report():
    project = Project(
        name="Nuclear Facility Lightning Protection",
        lps_class="I",
        building=Building(length_m=50, width_m=30, height_m=20, roof_type="flat")
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
            formula_trace="s = 0.08 * (0.5 / 1.0) * 20.0 = 0.800m"
        )
    ]
    earthing_info = {
        "actual_effective_length_m": 120.0,
        "stationary_resistance_r_ohm": 1.45,
        "impulse_impedance_z_ohm": 0.98
    }

    docx_bytes = DOCXReportRenderer.render_docx_report(
        project=project,
        separation_results=results,
        earthing_result=earthing_info
    )

    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 5000

    # Parse generated docx with python-docx
    doc = docx.Document(io.BytesIO(docx_bytes))
    headings = [p.text for p in doc.paragraphs if p.text]
    full_text = " ".join([p.text for p in doc.paragraphs])

    assert "LIGHTNING PROTECTION SYSTEM (LPS)" in full_text
    assert "Nuclear Facility Lightning Protection" in full_text
    assert len(doc.tables) >= 4 # Meta table, Summary table, Separation table, BOM table, Schedule table
