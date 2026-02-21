"""Tests for render_mcp.utils."""

from render_mcp.utils import (
    validate_musicxml,
    validate_image_format,
    validate_dpi,
    validate_page,
    generate_pdf_path,
    generate_image_path,
    RENDER_OUTPUT_DIR,
)


class TestValidateMusicxml:
    def test_valid_score_partwise(self):
        ok, err = validate_musicxml('<score-partwise version="3.1"><part-list/></score-partwise>')
        assert ok
        assert err == ""

    def test_valid_score_timewise(self):
        ok, err = validate_musicxml("<score-timewise/>")
        assert ok

    def test_empty_string(self):
        ok, err = validate_musicxml("")
        assert not ok
        assert "empty" in err.lower()

    def test_whitespace_only(self):
        ok, err = validate_musicxml("   \n  ")
        assert not ok

    def test_invalid_xml(self):
        ok, err = validate_musicxml("not xml at all")
        assert not ok
        assert "Invalid XML" in err

    def test_wrong_root_element(self):
        ok, err = validate_musicxml("<root><child/></root>")
        assert not ok
        assert "score-partwise" in err

    def test_xml_with_namespace(self):
        ok, err = validate_musicxml(
            '<score-partwise xmlns="http://www.musicxml.org/dtds/partwise.dtd"/>'
        )
        assert ok


class TestValidateImageFormat:
    def test_png_valid(self):
        ok, err = validate_image_format("png")
        assert ok
        assert err == ""

    def test_svg_valid(self):
        ok, err = validate_image_format("svg")
        assert ok

    def test_invalid_format(self):
        ok, err = validate_image_format("jpg")
        assert not ok
        assert "jpg" in err

    def test_empty_string(self):
        ok, err = validate_image_format("")
        assert not ok

    def test_pdf_invalid(self):
        ok, err = validate_image_format("pdf")
        assert not ok


class TestValidateDpi:
    def test_valid_150(self):
        ok, err = validate_dpi(150)
        assert ok
        assert err == ""

    def test_valid_lower_bound(self):
        ok, err = validate_dpi(72)
        assert ok

    def test_valid_upper_bound(self):
        ok, err = validate_dpi(600)
        assert ok

    def test_too_low(self):
        ok, err = validate_dpi(71)
        assert not ok
        assert "72" in err

    def test_too_high(self):
        ok, err = validate_dpi(601)
        assert not ok
        assert "600" in err

    def test_not_integer(self):
        ok, err = validate_dpi(150.5)
        assert not ok


class TestValidatePage:
    def test_page_1(self):
        ok, err = validate_page(1)
        assert ok
        assert err == ""

    def test_page_10(self):
        ok, err = validate_page(10)
        assert ok

    def test_page_zero(self):
        ok, err = validate_page(0)
        assert not ok

    def test_page_negative(self):
        ok, err = validate_page(-1)
        assert not ok

    def test_not_integer(self):
        ok, err = validate_page(1.5)
        assert not ok


class TestGeneratePaths:
    def test_returns_provided_pdf_path(self):
        result = generate_pdf_path("/custom/path/score.pdf")
        assert result == "/custom/path/score.pdf"

    def test_generates_pdf_path_when_none(self):
        result = generate_pdf_path(None)
        assert result.endswith(".pdf")
        assert RENDER_OUTPUT_DIR in result

    def test_returns_provided_image_path(self):
        result = generate_image_path("/custom/path/score.png", "png")
        assert result == "/custom/path/score.png"

    def test_generates_png_path_when_none(self):
        result = generate_image_path(None, "png")
        assert result.endswith(".png")
        assert RENDER_OUTPUT_DIR in result

    def test_generates_svg_path_when_none(self):
        result = generate_image_path(None, "svg")
        assert result.endswith(".svg")
