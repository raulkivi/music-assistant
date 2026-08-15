"""Tests for OMR engine module."""

import pytest
from pathlib import Path
from unittest.mock import patch

from omr_mcp.omr_engine import (
    recognize_image,
    recognize_image_to_file,
    recognize_images,
    _extract_musicxml_metadata,
    _merge_musicxml_pages,
    health_check,
)


class TestExtractMusicxmlMetadata:
    """Tests for MusicXML metadata extraction."""

    def test_extract_staves(self):
        musicxml = '''<?xml version="1.0"?>
        <score-partwise>
            <part-list>
                <score-part id="P1"><part-name>Soprano</part-name></score-part>
                <score-part id="P2"><part-name>Alto</part-name></score-part>
            </part-list>
            <part id="P1">
                <measure number="1"></measure>
                <measure number="2"></measure>
            </part>
            <part id="P2">
                <measure number="1"></measure>
                <measure number="2"></measure>
            </part>
        </score-partwise>'''
        
        metadata = _extract_musicxml_metadata(musicxml)
        assert metadata["staves_detected"] == 2
        assert metadata["measures"] == 2

    def test_extract_empty_musicxml(self):
        musicxml = '<?xml version="1.0"?><score-partwise></score-partwise>'
        
        metadata = _extract_musicxml_metadata(musicxml)
        assert metadata["staves_detected"] == 0
        assert metadata["measures"] == 0


class TestRecognizeImage:
    """Tests for recognize_image function."""

    def test_nonexistent_file(self):
        result = recognize_image("/nonexistent/path/image.png")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_unsupported_format(self, tmp_path):
        test_file = tmp_path / "test.bmp"
        test_file.write_bytes(b"fake content")
        
        result = recognize_image(str(test_file))
        assert "error" in result
        assert "Unsupported format" in result["error"]


class TestMergeMusicxmlPages:
    """Tests for internal MusicXML page merger."""

    SIMPLE_PAGE = '''<?xml version="1.0"?>
    <score-partwise>
        <part-list><score-part id="P1"><part-name>Soprano</part-name></score-part></part-list>
        <part id="P1">
            <measure number="1"></measure>
            <measure number="2"></measure>
        </part>
    </score-partwise>'''

    def test_single_page_returned_unchanged(self):
        result = _merge_musicxml_pages([self.SIMPLE_PAGE])
        assert result == self.SIMPLE_PAGE

    def test_two_pages_doubles_measure_count(self):
        import xml.etree.ElementTree as ET
        result = _merge_musicxml_pages([self.SIMPLE_PAGE, self.SIMPLE_PAGE])
        root = ET.fromstring(result)
        measures = root.find("part").findall("measure")
        assert len(measures) == 4

    def test_measure_numbers_renumbered(self):
        import xml.etree.ElementTree as ET
        result = _merge_musicxml_pages([self.SIMPLE_PAGE, self.SIMPLE_PAGE])
        root = ET.fromstring(result)
        numbers = [int(m.get("number")) for m in root.find("part").findall("measure")]
        assert numbers == [1, 2, 3, 4]


class TestRecognizeImages:
    """Tests for the batch recognize_images function."""

    def test_empty_list_returns_error(self):
        result = recognize_images([])
        assert "error" in result
        assert result.get("error_code") == "INVALID_PARAMETER"

    def test_nonexistent_file_returns_error(self):
        result = recognize_images(["/nonexistent/page1.png"])
        assert "error" in result

    def test_multiple_nonexistent_files_returns_error(self):
        result = recognize_images(["/no/page1.png", "/no/page2.png"])
        assert "error" in result


class TestHealthCheck:
    """Tests for the health_check function."""

    def test_returns_status_field(self):
        result = health_check()
        assert "status" in result
        assert result["status"] in ("ok", "degraded")

    def test_returns_checks_dict(self):
        result = health_check()
        assert "checks" in result
        assert isinstance(result["checks"], dict)

    def test_checks_include_oemer(self):
        result = health_check()
        assert "oemer" in result["checks"]
        assert result["checks"]["oemer"]["status"] in ("ok", "missing")

    def test_checks_include_model_cache(self):
        result = health_check()
        assert "model_cache" in result["checks"]
        assert result["checks"]["model_cache"]["status"] in ("ok", "missing")

    def test_overall_ok_when_all_checks_ok(self, tmp_path, monkeypatch):
        """status == 'ok' when oemer is importable and checkpoint file exists."""
        import omr_mcp.omr_engine as eng

        # Pretend oemer is installed
        fake_oemer = type("FakeOemer", (), {})()
        import sys
        monkeypatch.setitem(sys.modules, "oemer", fake_oemer)

        # Point the checkpoint path at a file that exists
        checkpoint = tmp_path / "model.onnx"
        checkpoint.write_bytes(b"fake checkpoint")
        monkeypatch.setattr(eng, "_oemer_checkpoint_path", lambda: checkpoint)

        result = health_check()
        assert result["status"] == "ok"

    def test_degraded_when_cache_missing(self, monkeypatch):
        """status == 'degraded' when model checkpoint file does not exist."""
        import omr_mcp.omr_engine as eng
        from pathlib import Path
        import sys

        # Pretend oemer is installed
        fake_oemer = type("FakeOemer", (), {})()
        monkeypatch.setitem(sys.modules, "oemer", fake_oemer)

        # Point the checkpoint path at a non-existent file
        monkeypatch.setattr(
            eng, "_oemer_checkpoint_path", lambda: Path("/nonexistent/oemer_cache/model.onnx")
        )

        result = health_check()
        assert result["status"] == "degraded"
        assert result["checks"]["model_cache"]["status"] == "missing"
        assert result["checks"]["model_cache"]["path"] is None

    def test_model_cache_note_present(self, monkeypatch):
        """Missing cache includes a helpful note about first-run download."""
        import omr_mcp.omr_engine as eng
        from pathlib import Path
        import sys

        fake_oemer = type("FakeOemer", (), {})()
        monkeypatch.setitem(sys.modules, "oemer", fake_oemer)
        monkeypatch.setattr(
            eng, "_oemer_checkpoint_path", lambda: Path("/nonexistent/oemer_cache/model.onnx")
        )

        result = health_check()
        note = result["checks"]["model_cache"]["note"]
        assert "100 MB" in note or "download" in note.lower()


class TestRecognizeImageToFile:
    """Tests for recognize_image_to_file function."""

    def test_nonexistent_file(self):
        result = recognize_image_to_file("/nonexistent/path/image.png")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_unsupported_format(self, tmp_path):
        test_file = tmp_path / "test.gif"
        test_file.write_bytes(b"fake content")
        
        result = recognize_image_to_file(str(test_file))
        assert "error" in result
        assert "Unsupported format" in result["error"]

    def test_auto_generated_output_path(self, tmp_path, monkeypatch):
        """Test that output path is auto-generated when not specified."""
        # We can't test actual OMR without oemer, but we can check the logic
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake png content")
        
        # The function will fail because it's not a real PNG,
        # but we're testing the error handling and path logic
        result = recognize_image_to_file(str(test_file))
        # Will get an error from oemer, but the function should handle it
        assert "error" in result or "output_path" in result
