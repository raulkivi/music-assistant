"""Integration tests for OMR engine.

Run with:
    uv run pytest tests/ -v -m integration

These tests invoke real oemer OMR on fixture PNGs and are intentionally excluded
from the default ``pytest`` run because they are slow (3-5 min per page on CPU).
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from omr_mcp.omr_engine import recognize_image

SAMPLES_DIR = Path(__file__).parent.parent / "test_samples" / "pdmx_satb_samples"
PNG_DIR = SAMPLES_DIR / "png"
MXL_DIR = SAMPLES_DIR / "mxl"

# Two single-page pieces (full score fits on one PNG → can compare measure count too)
SINGLE_PAGE_PIECES = [
    "Qmb5Q3qcB6vQZrDKxUp8kajvLcHVRRxby1tgo7iZBCfzgH",
    "Qmb5f7trYCXBdNDqHirQ82fXJ7npCBTWwHasVzWkSQxiMP",
]
# One multi-page piece — test page01 only; only compare part count, not measures
MULTI_PAGE_PIECE = "Qmb6okFHL9g7Hmq7pyercQMePwTHxhiEvYkyKcYH1Z2cK9"

ALL_TEST_PIECES = SINGLE_PAGE_PIECES + [MULTI_PAGE_PIECE]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_mxl(mxl_path: Path) -> ET.Element:
    """Open a .mxl (zipped MusicXML) and return the parsed, namespace-stripped root."""
    with zipfile.ZipFile(mxl_path) as z:
        xml_names = [
            n for n in z.namelist()
            if n.endswith((".xml", ".musicxml")) and "META-INF" not in n
        ]
        with z.open(xml_names[0]) as f:
            root = ET.parse(f).getroot()
    return _strip_ns(root)


def _strip_ns(element: ET.Element) -> ET.Element:
    """Remove XML namespace prefixes from all tags in-place."""
    for el in element.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}")[1]
    return element


def _part_count(root: ET.Element) -> int:
    return len(root.findall("part"))


def _measure_count_first_part(root: ET.Element) -> int:
    part = root.find("part")
    if part is None:
        return 0
    return len(part.findall("measure"))


# ---------------------------------------------------------------------------
# Basic OMR correctness — run on all 3 fixture pieces
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("piece_id", ALL_TEST_PIECES)
class TestRecognizeImageIntegration:
    """Each PNG must produce valid, non-empty MusicXML with at least one part and measure."""

    def test_returns_musicxml_string(self, piece_id):
        png = PNG_DIR / f"{piece_id}_page01.png"
        result = recognize_image(str(png))
        assert "error" not in result, f"OMR error on {piece_id}: {result.get('error')}"
        musicxml = result.get("musicxml", "")
        assert isinstance(musicxml, str) and musicxml, "musicxml must be a non-empty string"

    def test_musicxml_is_valid_xml(self, piece_id):
        png = PNG_DIR / f"{piece_id}_page01.png"
        result = recognize_image(str(png))
        root = ET.fromstring(result["musicxml"])  # raises ParseError if invalid
        assert root is not None

    def test_has_at_least_one_part_and_measure(self, piece_id):
        png = PNG_DIR / f"{piece_id}_page01.png"
        result = recognize_image(str(png))
        root = _strip_ns(ET.fromstring(result["musicxml"]))
        parts = root.findall("part")
        assert len(parts) >= 1, "Expected at least one <part> element"
        measures = parts[0].findall("measure")
        assert len(measures) >= 1, "Expected at least one <measure> in first part"

    def test_metadata_fields_populated(self, piece_id):
        png = PNG_DIR / f"{piece_id}_page01.png"
        result = recognize_image(str(png))
        meta = result.get("metadata", {})
        assert meta.get("staves_detected", 0) >= 1, "staves_detected should be ≥ 1"
        assert meta.get("measures", 0) >= 1, "measures should be ≥ 1"
        assert meta.get("processing_time_ms", 0) > 0, "processing_time_ms should be > 0"
        assert meta.get("engine") == "oemer"


# ---------------------------------------------------------------------------
# Ground-truth comparison — single-page pieces only
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("piece_id", SINGLE_PAGE_PIECES)
class TestGroundTruthComparison:
    """Compare oemer structural output against ground-truth MXL for single-page pieces."""

    def test_part_count_within_tolerance(self, piece_id):
        """oemer part count should match ground truth ± 1 (oemer may split or merge staves)."""
        png = PNG_DIR / f"{piece_id}_page01.png"
        mxl = MXL_DIR / f"{piece_id}.mxl"

        result = recognize_image(str(png))
        oemer_root = _strip_ns(ET.fromstring(result["musicxml"]))
        gt_root = _read_mxl(mxl)

        oemer_parts = _part_count(oemer_root)
        gt_parts = _part_count(gt_root)
        assert abs(oemer_parts - gt_parts) <= 1, (
            f"{piece_id}: part count oemer={oemer_parts} vs ground_truth={gt_parts}"
        )

    def test_measure_count_within_tolerance(self, piece_id):
        """Measure count should be within 20 % of ground truth (oemer is approximate)."""
        png = PNG_DIR / f"{piece_id}_page01.png"
        mxl = MXL_DIR / f"{piece_id}.mxl"

        result = recognize_image(str(png))
        oemer_root = _strip_ns(ET.fromstring(result["musicxml"]))
        gt_root = _read_mxl(mxl)

        oemer_measures = _measure_count_first_part(oemer_root)
        gt_measures = _measure_count_first_part(gt_root)

        tolerance = max(2, int(gt_measures * 0.20))
        assert abs(oemer_measures - gt_measures) <= tolerance, (
            f"{piece_id}: measure count oemer={oemer_measures} vs ground_truth={gt_measures} "
            f"(tolerance ±{tolerance})"
        )
