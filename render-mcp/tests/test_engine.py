"""Tests for render_mcp.engine."""

import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from render_mcp.engine import (
    ProcessingError,
    _get_pdf_page_count,
    _get_image_dimensions,
    detect_backend,
    musescore_available,
    render_to_pdf,
    render_to_image,
    verovio_available,
)

# ---------------------------------------------------------------------------
# Shared fixture: minimal valid MusicXML
# ---------------------------------------------------------------------------

SIMPLE_MUSICXML = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Soprano</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>4</duration><type>whole</type>
      </note>
    </measure>
  </part>
</score-partwise>"""


# ---------------------------------------------------------------------------
# detect_backend
# ---------------------------------------------------------------------------

class TestDetectBackend:
    def test_returns_string_or_none(self):
        result = detect_backend()
        assert result in ("musescore", "verovio", None)

    def test_musescore_available_is_bool(self):
        assert isinstance(musescore_available(), bool)

    def test_verovio_available_is_bool(self):
        assert isinstance(verovio_available(), bool)

    def test_verovio_is_available(self):
        # verovio is installed in the dev venv
        assert verovio_available() is True

    def test_backend_is_not_none(self):
        # At least verovio is installed
        assert detect_backend() is not None


# ---------------------------------------------------------------------------
# render_to_pdf — no backend available
# ---------------------------------------------------------------------------

class TestRenderToPdfNoBackend:
    def test_raises_when_no_backend(self, tmp_path):
        with (
            patch("render_mcp.engine._MUSESCORE_CMD", None),
            patch("render_mcp.engine._VEROVIO_AVAILABLE", False),
        ):
            with pytest.raises(ProcessingError) as exc:
                render_to_pdf(SIMPLE_MUSICXML, str(tmp_path / "out.pdf"))
            assert exc.value.error_code == "PROCESSING_FAILED"
            assert "backend" in str(exc.value).lower()


# ---------------------------------------------------------------------------
# render_to_pdf — MuseScore path (mocked subprocess)
# ---------------------------------------------------------------------------

class TestRenderToPdfMuseScore:
    def test_calls_musescore_subprocess(self, tmp_path):
        out_pdf = tmp_path / "out.pdf"
        # Pre-create the file so the existence check passes
        out_pdf.write_bytes(b"%PDF-1.4 fake")

        mock_result = MagicMock()
        mock_result.returncode = 0

        with (
            patch("render_mcp.engine._MUSESCORE_CMD", "mscore4"),
            patch("render_mcp.engine._VEROVIO_AVAILABLE", False),
            patch("render_mcp.engine.subprocess.run", return_value=mock_result) as mock_run,
            patch("render_mcp.engine._get_pdf_page_count", return_value=3),
        ):
            path, pages = render_to_pdf(SIMPLE_MUSICXML, str(out_pdf))

        assert path == str(out_pdf)
        assert pages == 3
        args = mock_run.call_args[0][0]
        assert "mscore4" in args
        assert str(out_pdf) in args

    def test_raises_on_nonzero_returncode(self, tmp_path):
        out_pdf = tmp_path / "out.pdf"

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Something went wrong"

        with (
            patch("render_mcp.engine._MUSESCORE_CMD", "mscore4"),
            patch("render_mcp.engine._VEROVIO_AVAILABLE", False),
            patch("render_mcp.engine.subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(ProcessingError) as exc:
                render_to_pdf(SIMPLE_MUSICXML, str(out_pdf))
            assert exc.value.error_code == "PROCESSING_FAILED"

    def test_raises_when_output_file_missing(self, tmp_path):
        out_pdf = tmp_path / "out.pdf"

        mock_result = MagicMock()
        mock_result.returncode = 0

        with (
            patch("render_mcp.engine._MUSESCORE_CMD", "mscore4"),
            patch("render_mcp.engine._VEROVIO_AVAILABLE", False),
            patch("render_mcp.engine.subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(ProcessingError) as exc:
                render_to_pdf(SIMPLE_MUSICXML, str(out_pdf))
            assert exc.value.error_code == "PROCESSING_FAILED"


# ---------------------------------------------------------------------------
# render_to_image — no backend available
# ---------------------------------------------------------------------------

class TestRenderToImageNoBackend:
    def test_raises_when_no_backend(self, tmp_path):
        with (
            patch("render_mcp.engine._MUSESCORE_CMD", None),
            patch("render_mcp.engine._VEROVIO_AVAILABLE", False),
        ):
            with pytest.raises(ProcessingError) as exc:
                render_to_image(SIMPLE_MUSICXML, 1, "png", 150, str(tmp_path / "out.png"))
            assert exc.value.error_code == "PROCESSING_FAILED"


# ---------------------------------------------------------------------------
# _get_pdf_page_count
# ---------------------------------------------------------------------------

class TestGetPdfPageCount:
    def test_returns_zero_for_missing_file(self, tmp_path):
        count = _get_pdf_page_count(str(tmp_path / "nonexistent.pdf"))
        assert count == 0


# ---------------------------------------------------------------------------
# _get_image_dimensions
# ---------------------------------------------------------------------------

class TestGetImageDimensions:
    def test_png_dimensions(self, tmp_path):
        import struct, zlib

        def _make_minimal_png(width: int, height: int) -> bytes:
            """Build a minimal valid single-pixel PNG for testing."""
            raw = b"\x00" + b"\x00" * (width * 3)  # filter byte + RGB row
            raw = raw * height
            compressed = zlib.compress(raw)
            chunks = []

            def chunk(tag: bytes, data: bytes) -> bytes:
                length = struct.pack(">I", len(data))
                crc = struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
                return length + tag + data + crc

            ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
            chunks.append(chunk(b"IHDR", ihdr))
            chunks.append(chunk(b"IDAT", compressed))
            chunks.append(chunk(b"IEND", b""))
            return b"\x89PNG\r\n\x1a\n" + b"".join(chunks)

        png_path = tmp_path / "test.png"
        png_path.write_bytes(_make_minimal_png(100, 200))
        w, h = _get_image_dimensions(str(png_path))
        assert w == 100
        assert h == 200


# ---------------------------------------------------------------------------
# Integration tests — require real fixtures and backends
# ---------------------------------------------------------------------------

FIXTURE_DIR = (
    Path(__file__).parent.parent.parent
    / "omr-mcp"
    / "test_samples"
    / "pdmx_satb_samples"
    / "mxl"
)


def _read_mxl(path: Path) -> str:
    """Extract MusicXML content from an MXL (ZIP) file."""
    with zipfile.ZipFile(path) as zf:
        xml_names = [
            n for n in zf.namelist()
            if n.endswith(".xml") and "META-INF" not in n
        ]
        if not xml_names:
            raise ValueError(f"No XML content found in {path}")
        return zf.read(xml_names[0]).decode("utf-8")


@pytest.mark.integration
class TestIntegration:
    def test_fixture_dir_exists(self):
        assert FIXTURE_DIR.exists(), f"Fixture dir not found: {FIXTURE_DIR}"

    def test_verovio_backend_available(self):
        assert verovio_available(), "Verovio must be installed for integration tests"

    def test_render_to_pdf_produces_file(self, tmp_path):
        fixtures = sorted(FIXTURE_DIR.glob("*.mxl"))
        assert fixtures

        musicxml_str = _read_mxl(fixtures[0])
        out_pdf = str(tmp_path / "output.pdf")

        with patch("render_mcp.engine._MUSESCORE_CMD", None):
            pdf_path, page_count = render_to_pdf(musicxml_str, out_pdf)

        assert Path(pdf_path).exists()
        assert Path(pdf_path).stat().st_size > 100
        assert page_count >= 1

    def test_render_to_pdf_page_count_matches_reader(self, tmp_path):
        fixtures = sorted(FIXTURE_DIR.glob("*.mxl"))
        assert fixtures

        musicxml_str = _read_mxl(fixtures[0])
        out_pdf = str(tmp_path / "output.pdf")

        with patch("render_mcp.engine._MUSESCORE_CMD", None):
            _, page_count = render_to_pdf(musicxml_str, out_pdf)

        actual = _get_pdf_page_count(out_pdf)
        assert actual == page_count

    def test_render_to_image_png(self, tmp_path):
        fixtures = sorted(FIXTURE_DIR.glob("*.mxl"))
        assert fixtures

        musicxml_str = _read_mxl(fixtures[0])
        out_png = str(tmp_path / "output.png")

        with patch("render_mcp.engine._MUSESCORE_CMD", None):
            result = render_to_image(musicxml_str, 1, "png", 150, out_png)

        assert Path(out_png).exists()
        assert result["format"] == "png"
        assert result["page"] == 1
        assert result["total_pages"] >= 1
        assert result["width_px"] > 0
        assert result["height_px"] > 0
        assert result["backend"] == "verovio"

    def test_render_to_image_svg(self, tmp_path):
        fixtures = sorted(FIXTURE_DIR.glob("*.mxl"))
        assert fixtures

        musicxml_str = _read_mxl(fixtures[0])
        out_svg = str(tmp_path / "output.svg")

        with patch("render_mcp.engine._MUSESCORE_CMD", None):
            result = render_to_image(musicxml_str, 1, "svg", 150, out_svg)

        assert Path(out_svg).exists()
        content = Path(out_svg).read_text()
        assert "<svg" in content
        assert result["format"] == "svg"

    def test_page_out_of_range_raises(self, tmp_path):
        fixtures = sorted(FIXTURE_DIR.glob("*.mxl"))
        assert fixtures

        musicxml_str = _read_mxl(fixtures[0])

        with patch("render_mcp.engine._MUSESCORE_CMD", None):
            with pytest.raises(ProcessingError) as exc:
                render_to_image(musicxml_str, 999, "png", 150, str(tmp_path / "out.png"))
        assert exc.value.error_code == "INVALID_PARAMETER"

    def test_invalid_musicxml_raises(self, tmp_path):
        with patch("render_mcp.engine._MUSESCORE_CMD", None):
            with pytest.raises(ProcessingError) as exc:
                render_to_pdf("not xml", str(tmp_path / "out.pdf"))
        assert exc.value.error_code == "INVALID_INPUT"

    def test_higher_dpi_produces_larger_png(self, tmp_path):
        fixtures = sorted(FIXTURE_DIR.glob("*.mxl"))
        assert fixtures

        musicxml_str = _read_mxl(fixtures[0])

        with patch("render_mcp.engine._MUSESCORE_CMD", None):
            r72 = render_to_image(musicxml_str, 1, "png", 72, str(tmp_path / "72dpi.png"))
            r300 = render_to_image(musicxml_str, 1, "png", 300, str(tmp_path / "300dpi.png"))

        assert r300["width_px"] > r72["width_px"]
        assert r300["height_px"] > r72["height_px"]
