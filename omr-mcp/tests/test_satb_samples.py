"""Unit tests using real SATB sample files (no oemer invocation).

Skipped automatically if the test_samples/ directories are absent (e.g. in CI
before download scripts are run).  Run normally with:

    VIRTUAL_ENV= .venv/bin/pytest tests/test_satb_samples.py -v

All tests here exercise utility functions only (validate_image_path,
get_image_info, _extract_musicxml_metadata) — no OMR engine is invoked.
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from omr_mcp.utils import validate_image_path, get_image_info, SUPPORTED_IMAGE_FORMATS
from omr_mcp.omr_engine import _extract_musicxml_metadata

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SAMPLES_ROOT = Path(__file__).parent.parent / "test_samples"
PDMX_DIR = SAMPLES_ROOT / "pdmx_satb_samples"
CPDL_DIR = SAMPLES_ROOT / "cpdl_satb_samples"
PDMX_PNG_DIR = PDMX_DIR / "png"
PDMX_MXL_DIR = PDMX_DIR / "mxl"

# Skip the entire module when samples haven't been downloaded yet.
pytestmark = pytest.mark.skipif(
    not (PDMX_DIR / "png").exists(),
    reason="SATB samples not downloaded — run test_samples/download_pdmx_satb.py first",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_mxl_as_xml_string(mxl_path: Path) -> str:
    """Open a .mxl archive and return the inner MusicXML content as a string."""
    with zipfile.ZipFile(mxl_path) as z:
        xml_names = [
            n for n in z.namelist()
            if n.endswith((".xml", ".musicxml")) and "META-INF" not in n
        ]
        assert xml_names, f"No XML entry found inside {mxl_path.name}"
        with z.open(xml_names[0]) as f:
            return f.read().decode("utf-8")


# ---------------------------------------------------------------------------
# CPDL samples — human-readable piece names
# ---------------------------------------------------------------------------

# (piece_name, expected_page_count)
CPDL_PIECES_WITH_PNGS = [
    ("If_ye_love_me_-_Thomas_Tallis", 1),
    ("Ave_verum_corpus_-_William_Byrd", 4),
    ("Locus_iste_-_Bruckner", 3),
    ("Sicut_cervus_-_Palestrina", 4),
]

CPDL_ALL_PIECES = [
    "If_ye_love_me_-_Thomas_Tallis",
    "Ave_verum_corpus_-_William_Byrd",
    "Locus_iste_-_Bruckner",
    "O_magnum_mysterium_-_Victoria",
    "Sicut_cervus_-_Palestrina",
]


class TestCPDLImageValidation:
    """Real SATB PNGs from CPDL pass validate_image_path."""

    @pytest.mark.parametrize("piece_name,page_count", CPDL_PIECES_WITH_PNGS)
    def test_all_pages_pass_validation(self, piece_name, page_count):
        piece_dir = CPDL_DIR / piece_name
        if not piece_dir.exists():
            pytest.skip(f"CPDL sample not present: {piece_name}")

        for page_num in range(1, page_count + 1):
            png = piece_dir / f"{piece_name}_page{page_num:02d}.png"
            assert png.exists(), f"Expected page file missing: {png.name}"
            is_valid, error = validate_image_path(str(png))
            assert is_valid, f"Page {page_num} of {piece_name} failed: {error}"

    @pytest.mark.parametrize("piece_name,page_count", CPDL_PIECES_WITH_PNGS)
    def test_all_pages_use_supported_format(self, piece_name, page_count):
        piece_dir = CPDL_DIR / piece_name
        if not piece_dir.exists():
            pytest.skip(f"CPDL sample not present: {piece_name}")

        for png in piece_dir.glob("*.png"):
            assert png.suffix.lower() in SUPPORTED_IMAGE_FORMATS, (
                f"{png.name} has unsupported suffix {png.suffix!r}"
            )


class TestCPDLImageInfo:
    """Real SATB PNGs from CPDL return sensible image metadata."""

    @pytest.mark.parametrize("piece_name,_", CPDL_PIECES_WITH_PNGS)
    def test_page01_has_reasonable_dimensions(self, piece_name, _):
        piece_dir = CPDL_DIR / piece_name
        if not piece_dir.exists():
            pytest.skip(f"CPDL sample not present: {piece_name}")

        png = piece_dir / f"{piece_name}_page01.png"
        if not png.exists():
            pytest.skip(f"page01 not found for {piece_name}")

        info = get_image_info(str(png))
        assert info["width"] > 200, "Width suspiciously small for a sheet music page"
        assert info["height"] > 200, "Height suspiciously small for a sheet music page"
        assert info["format"] == "PNG"
        assert info["file_size"] > 0

    @pytest.mark.parametrize("piece_name,page_count", CPDL_PIECES_WITH_PNGS)
    def test_all_pages_have_minimum_dimensions(self, piece_name, page_count):
        piece_dir = CPDL_DIR / piece_name
        if not piece_dir.exists():
            pytest.skip(f"CPDL sample not present: {piece_name}")

        for page_num in range(1, page_count + 1):
            png = piece_dir / f"{piece_name}_page{page_num:02d}.png"
            if not png.exists():
                continue
            info = get_image_info(str(png))
            assert info["width"] >= 100, f"{png.name}: width {info['width']} < 100"
            assert info["height"] >= 100, f"{png.name}: height {info['height']} < 100"


class TestCPDLMxlMetadata:
    """MXL files for CPDL SATB pieces have expected structure."""

    @pytest.mark.parametrize("piece_name", CPDL_ALL_PIECES)
    def test_mxl_file_exists(self, piece_name):
        piece_dir = CPDL_DIR / piece_name
        if not piece_dir.exists():
            pytest.skip(f"CPDL sample not present: {piece_name}")

        mxl = piece_dir / f"{piece_name}.mxl"
        assert mxl.exists(), f"MXL file missing for {piece_name}"

    @pytest.mark.parametrize("piece_name", CPDL_ALL_PIECES)
    def test_mxl_is_valid_xml(self, piece_name):
        piece_dir = CPDL_DIR / piece_name
        if not piece_dir.exists():
            pytest.skip(f"CPDL sample not present: {piece_name}")

        mxl = piece_dir / f"{piece_name}.mxl"
        if not mxl.exists():
            pytest.skip(f"MXL not found for {piece_name}")

        xml_string = _load_mxl_as_xml_string(mxl)
        root = ET.fromstring(xml_string)
        assert root is not None

    @pytest.mark.parametrize("piece_name", CPDL_ALL_PIECES)
    def test_mxl_has_at_least_two_satb_parts(self, piece_name):
        """SATB pieces must have ≥ 2 parts (typically 4)."""
        piece_dir = CPDL_DIR / piece_name
        if not piece_dir.exists():
            pytest.skip(f"CPDL sample not present: {piece_name}")

        mxl = piece_dir / f"{piece_name}.mxl"
        if not mxl.exists():
            pytest.skip(f"MXL not found for {piece_name}")

        xml_string = _load_mxl_as_xml_string(mxl)
        metadata = _extract_musicxml_metadata(xml_string)
        assert metadata["staves_detected"] >= 2, (
            f"{piece_name}: expected ≥2 parts for SATB, "
            f"got {metadata['staves_detected']}"
        )

    @pytest.mark.parametrize("piece_name", CPDL_ALL_PIECES)
    def test_mxl_has_measures(self, piece_name):
        piece_dir = CPDL_DIR / piece_name
        if not piece_dir.exists():
            pytest.skip(f"CPDL sample not present: {piece_name}")

        mxl = piece_dir / f"{piece_name}.mxl"
        if not mxl.exists():
            pytest.skip(f"MXL not found for {piece_name}")

        xml_string = _load_mxl_as_xml_string(mxl)
        metadata = _extract_musicxml_metadata(xml_string)
        assert metadata["measures"] > 0, f"{piece_name}: no measures found in MXL"


# ---------------------------------------------------------------------------
# PDMX samples — hash-named files
# ---------------------------------------------------------------------------

# Stable representative subset used across multiple test classes
PDMX_SINGLE_PAGE_IDS = [
    "Qmb5Q3qcB6vQZrDKxUp8kajvLcHVRRxby1tgo7iZBCfzgH",
    "Qmb5f7trYCXBdNDqHirQ82fXJ7npCBTWwHasVzWkSQxiMP",
]
PDMX_MULTI_PAGE_ID = "Qmb6okFHL9g7Hmq7pyercQMePwTHxhiEvYkyKcYH1Z2cK9"  # 3 pages


class TestPDMXImageValidation:
    """PDMX SATB PNG files pass image validation."""

    @pytest.mark.parametrize("piece_id", PDMX_SINGLE_PAGE_IDS)
    def test_single_page_png_is_valid(self, piece_id):
        png = PDMX_PNG_DIR / f"{piece_id}_page01.png"
        if not png.exists():
            pytest.skip(f"PNG not found: {png.name}")

        is_valid, error = validate_image_path(str(png))
        assert is_valid, f"Validation failed for {piece_id}: {error}"

    def test_multi_page_first_png_is_valid(self):
        png = PDMX_PNG_DIR / f"{PDMX_MULTI_PAGE_ID}_page01.png"
        if not png.exists():
            pytest.skip("Multi-page piece page01 not found")

        is_valid, error = validate_image_path(str(png))
        assert is_valid, f"Validation failed: {error}"

    def test_all_pdmx_pngs_pass_validation(self):
        if not PDMX_PNG_DIR.exists():
            pytest.skip("PDMX PNG directory not found")

        pngs = list(PDMX_PNG_DIR.glob("*.png"))
        assert len(pngs) > 0, "No PNGs in PDMX sample directory"

        failures = []
        for png in pngs:
            is_valid, error = validate_image_path(str(png))
            if not is_valid:
                failures.append(f"{png.name}: {error}")
        assert not failures, "Some PDMX PNGs failed validation:\n" + "\n".join(failures)


class TestPDMXMxlMetadata:
    """PDMX SATB MXL files parse correctly and have expected structure."""

    @pytest.mark.parametrize("piece_id", PDMX_SINGLE_PAGE_IDS)
    def test_mxl_has_parts_and_measures(self, piece_id):
        mxl = PDMX_MXL_DIR / f"{piece_id}.mxl"
        if not mxl.exists():
            pytest.skip(f"MXL not found: {mxl.name}")

        xml_string = _load_mxl_as_xml_string(mxl)
        metadata = _extract_musicxml_metadata(xml_string)
        assert metadata["staves_detected"] >= 1, f"{piece_id}: no staves"
        assert metadata["measures"] >= 1, f"{piece_id}: no measures"

    def test_all_pdmx_mxls_are_parseable(self):
        if not PDMX_MXL_DIR.exists():
            pytest.skip("PDMX MXL directory not found")

        mxls = list(PDMX_MXL_DIR.glob("*.mxl"))
        assert len(mxls) > 0, "No MXL files in PDMX sample directory"

        failures = []
        for mxl in mxls:
            try:
                xml_string = _load_mxl_as_xml_string(mxl)
                metadata = _extract_musicxml_metadata(xml_string)
                assert isinstance(metadata["staves_detected"], int)
                assert isinstance(metadata["measures"], int)
            except Exception as exc:
                failures.append(f"{mxl.name}: {exc}")
        assert not failures, "Some PDMX MXLs failed to parse:\n" + "\n".join(failures)


class TestPDMXMultiPagePiece:
    """Multi-page PDMX piece has the expected number of sequential PNG pages."""

    def test_multi_page_piece_has_at_least_two_pages(self):
        if not PDMX_PNG_DIR.exists():
            pytest.skip("PDMX PNG directory not found")

        pages = sorted(PDMX_PNG_DIR.glob(f"{PDMX_MULTI_PAGE_ID}_page*.png"))
        assert len(pages) >= 2, (
            f"Expected ≥2 pages for multi-page piece, found {len(pages)}"
        )

    def test_multi_page_piece_pages_are_sequentially_numbered(self):
        if not PDMX_PNG_DIR.exists():
            pytest.skip("PDMX PNG directory not found")

        pages = sorted(PDMX_PNG_DIR.glob(f"{PDMX_MULTI_PAGE_ID}_page*.png"))
        page_nums = [int(p.stem.split("_page")[1]) for p in pages]
        assert page_nums == list(range(1, len(page_nums) + 1)), (
            f"Page numbers not sequential: {page_nums}"
        )

    def test_multi_page_has_paired_mxl(self):
        mxl = PDMX_MXL_DIR / f"{PDMX_MULTI_PAGE_ID}.mxl"
        assert mxl.exists(), "Paired MXL missing for multi-page piece"


# ---------------------------------------------------------------------------
# Cross-corpus: every PNG piece must have a paired MXL
# ---------------------------------------------------------------------------

class TestPairedMxlCoverage:
    """Each PNG-bearing piece in both corpora must have a corresponding MXL."""

    def test_all_pdmx_png_pieces_have_mxl(self):
        if not PDMX_PNG_DIR.exists():
            pytest.skip("PDMX PNG directory not found")

        png_piece_ids = {p.stem.split("_page")[0] for p in PDMX_PNG_DIR.glob("*.png")}
        mxl_ids = {p.stem for p in PDMX_MXL_DIR.glob("*.mxl")}
        missing = png_piece_ids - mxl_ids
        assert not missing, f"PDMX pieces with PNGs but no MXL: {missing}"

    def test_all_cpdl_png_pieces_have_mxl(self):
        if not CPDL_DIR.exists():
            pytest.skip("CPDL directory not found")

        errors = []
        for piece_dir in sorted(CPDL_DIR.iterdir()):
            if not piece_dir.is_dir():
                continue
            has_pngs = any(piece_dir.glob("*.png"))
            has_mxl = any(piece_dir.glob("*.mxl"))
            if has_pngs and not has_mxl:
                errors.append(piece_dir.name)
        assert not errors, f"CPDL pieces with PNGs but no MXL: {errors}"
