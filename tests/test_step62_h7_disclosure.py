"""Roof-coverage disclosure across the optimizer API, reports and UI."""
import io
import base64
import re
import zlib
from pathlib import Path

import docx
from fastapi.testclient import TestClient
from reportlab.platypus import SimpleDocTemplate

from aegislps_api.main import app
from aegislps_domain.models import Building, Project
from aegislps_reporting.docx_renderer import DOCXReportRenderer
from aegislps_reporting.report_renderer import ReportRenderer

LABEL = 'Roof coverage not verified (H7)'


def test_optimization_api_discloses_unverified_roof_coverage():
    response = TestClient(app).post('/api/v1/optimization/optimize-rods', json={
        'lps_class': 'I', 'building_bounds': [0, 0, 30, 20],
        'roof_height_m': 15, 'targets_to_protect': [{'id': 'target', 'x': 15, 'y': 10, 'z': 15}],
        'iterations': 1,
    })
    assert response.status_code == 200, response.text
    assert LABEL in response.json()['roof_coverage_verification_note']


def test_docx_report_discloses_unverified_roof_coverage():
    project = Project(name='Disclosure test', lps_class='I', building=Building(length_m=30, width_m=20, height_m=15, roof_type='flat'))
    document = docx.Document(io.BytesIO(DOCXReportRenderer.render_docx_report(project, [])))
    assert LABEL in '\n'.join(p.text for p in document.paragraphs)
    assert 'does not contain an optimization result' in '\n'.join(p.text for p in document.paragraphs)


def test_pdf_report_discloses_unverified_roof_coverage(monkeypatch):
    project = Project(name='Disclosure test', lps_class='I', building=Building(length_m=30, width_m=20, height_m=15, roof_type='flat'))
    original_build = SimpleDocTemplate.build
    rendered_text = []
    def capture_build(self, story, *args, **kwargs):
        rendered_text.extend(item.getPlainText() for item in story if hasattr(item, 'getPlainText'))
        return original_build(self, story, *args, **kwargs)
    monkeypatch.setattr(SimpleDocTemplate, 'build', capture_build)
    pdf = ReportRenderer.render_pdf_report(project, [])
    assert pdf.startswith(b'%PDF')
    assert any(LABEL in text and 'does not contain an optimization result' in text for text in rendered_text)
    # Verify the generated PDF content stream itself, not just the input story.
    streams = re.findall(rb'stream\r?\n(.*?)endstream', pdf, re.S)
    decoded = [zlib.decompress(base64.a85decode(stream, adobe=True)) for stream in streams]
    assert any(rb'Roof coverage not verified \(H7\)' in stream for stream in decoded)


def test_frontend_optimization_view_has_visible_disclosure():
    source = (Path(__file__).resolve().parents[1] / 'apps/web/src/App.tsx').read_text()
    view = source.split("{activeTab === 'optimization' && (", 1)[1].split('{/* Reports', 1)[0]
    assert LABEL in view
    assert '<details' not in view
    assert 'optimizationResult.roof_coverage_verification_note' in view
    assert '/api/v1/optimization/optimize-rods' in source
