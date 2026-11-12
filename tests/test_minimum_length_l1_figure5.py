"""Reference, domain, and consumer-consistency tests for minimum electrode length l1(rho).

Primary source:
- IEC 62305-3:2024, Clause 5.4.2.2, Figure 5 (p. 34).
- Graphical reading tolerance: ±0.5 m.
- Figure 5 NOTE 1: Classes III and IV are independent of soil resistivity (5.0 m).
- Figure 5 NOTE 4: Figure 5 is defined up to rho = 3000 ohm.m (no extrapolation).
"""

import io
import docx
import pytest

from aegislps_domain.models import Building, Project
from aegislps_engine.earthing import (
    EarthingAssessmentInput,
    EarthingEngine,
    SoilLayerModel,
)
from aegislps_reporting.docx_renderer import DOCXReportRenderer


@pytest.mark.parametrize(
    "rho,expected_m",
    [
        (100.0, 5.0),
        (500.0, 5.0),
        (1000.0, 20.0),
        (2000.0, 50.0),
        (3000.0, 80.0),
    ],
)
def test_class_i_l1_figure5_values(rho: float, expected_m: float) -> None:
    """IEC 62305-3:2024 Clause 5.4.2.2, Figure 5 (p. 34) Class I curve (±0.5 m)."""
    computed = EarthingEngine.get_iec_min_length_l1("I", rho)
    assert abs(computed - expected_m) <= 0.5

    res = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(rho_upper_ohm_m=rho),
            electrode_type="type_b_ring",
            ring_radius_m=15.0,
            conductor_diameter_m=0.01,
            peak_impulse_current_ka=100.0,
        )
    )
    assert res.minimum_length_l1_m == pytest.approx(round(computed, 2), abs=1e-9)


@pytest.mark.parametrize(
    "rho,expected_m",
    [
        (100.0, 5.0),
        (800.0, 5.0),
        (1000.0, 9.0),
        (2000.0, 28.7),
        (3000.0, 48.5),
    ],
)
def test_class_ii_l1_figure5_values(rho: float, expected_m: float) -> None:
    """IEC 62305-3:2024 Clause 5.4.2.2, Figure 5 (p. 34) Class II curve (±0.5 m)."""
    computed = EarthingEngine.get_iec_min_length_l1("II", rho)
    assert abs(computed - expected_m) <= 0.5


@pytest.mark.parametrize("lps_cls", ["III", "IV"])
@pytest.mark.parametrize("rho", [100.0, 1000.0, 3000.0])
def test_class_iii_and_iv_l1_constant_per_note1(lps_cls: str, rho: float) -> None:
    """IEC 62305-3:2024 Clause 5.4.2.2, Figure 5 NOTE 1 (p. 34): constant 5.0 m."""
    assert EarthingEngine.get_iec_min_length_l1(lps_cls, rho) == 5.0


@pytest.mark.parametrize(
    "bad_rho",
    [0.0, -1.0, 3000.01, 3001.0, float("nan"), float("inf"), -float("inf"), True, False],
)
def test_out_of_domain_rho_raises_value_error(bad_rho) -> None:
    """rho <= 0, rho > 3000 ohm.m, or non-finite rho raises ValueError (no extrapolation)."""
    with pytest.raises(ValueError):
        EarthingEngine.get_iec_min_length_l1("I", bad_rho)


@pytest.mark.parametrize("bad_class", ["", "V", "0", "i", None, 1])
def test_unknown_class_raises_value_error(bad_class) -> None:
    """Unknown LPS class raises ValueError."""
    with pytest.raises(ValueError):
        EarthingEngine.get_iec_min_length_l1(bad_class, 500.0)


def test_docx_renderer_prints_computed_l1_not_constant_5() -> None:
    """DOCXReportRenderer prints computed Class I l1 at rho=2000 (~50.0 m), not 5.0 m."""
    project = Project(
        name="Step 2.4 l1 Consistency Check",
        lps_class="I",
        building=Building(length_m=30.0, width_m=20.0, height_m=12.0, roof_type="flat"),
    )
    earthing_res = EarthingEngine().evaluate_earthing_system(
        EarthingAssessmentInput(
            lps_class="I",
            soil=SoilLayerModel(rho_upper_ohm_m=2000.0),
            electrode_type="type_b_ring",
            ring_radius_m=15.0,
            conductor_diameter_m=0.01,
            peak_impulse_current_ka=100.0,
        )
    )
    assert abs(earthing_res.minimum_length_l1_m - 50.0) <= 0.5

    # Case 1: full EarthingEngine result dict passed to DOCXReportRenderer
    docx_bytes_from_engine = DOCXReportRenderer.render_docx_report(
        project=project,
        separation_results=[],
        earthing_result=earthing_res.model_dump(),
    )
    doc_1 = docx.Document(io.BytesIO(docx_bytes_from_engine))
    text_1 = " ".join(p.text for p in doc_1.paragraphs if p.text)
    assert f"IEC 62305-3 minimum l1 = {earthing_res.minimum_length_l1_m:.1f} m" in text_1
    assert "IEC 62305-3 minimum l1 = 5.0 m" not in text_1

    # Case 2: partial dict without precomputed minimum_length_l1_m
    docx_bytes_computed = DOCXReportRenderer.render_docx_report(
        project=project,
        separation_results=[],
        earthing_result={"effective_soil_resistivity_ohm_m": 2000.0},
    )
    doc_2 = docx.Document(io.BytesIO(docx_bytes_computed))
    text_2 = " ".join(p.text for p in doc_2.paragraphs if p.text)
    assert "IEC 62305-3 minimum l1 = 50.0 m" in text_2
    assert "IEC 62305-3 minimum l1 = 5.0 m" not in text_2
