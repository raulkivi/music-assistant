"""Unit tests for musicxml_abc_mcp.utils."""

from musicxml_abc_mcp.utils import validate_abc_str, validate_musicxml


class TestValidateMusicxml:
    def test_valid_score_partwise(self):
        ok, err = validate_musicxml(
            '<?xml version="1.0"?><score-partwise version="3.1"></score-partwise>'
        )
        assert ok is True
        assert err == ""

    def test_valid_score_timewise(self):
        ok, err = validate_musicxml(
            '<?xml version="1.0"?><score-timewise></score-timewise>'
        )
        assert ok is True

    def test_empty_string(self):
        ok, err = validate_musicxml("")
        assert ok is False
        assert "empty" in err.lower()

    def test_whitespace_only(self):
        ok, err = validate_musicxml("   \n  ")
        assert ok is False

    def test_not_musicxml(self):
        ok, err = validate_musicxml("<html><body>Hello</body></html>")
        assert ok is False
        assert "score-partwise" in err or "score-timewise" in err

    def test_abc_string_rejected(self):
        ok, err = validate_musicxml("X:1\nT:Test\nM:4/4\nL:1/8\nK:C\nCDEF|]")
        assert ok is False


class TestValidateAbcStr:
    def test_valid_abc(self):
        ok, err = validate_abc_str("X:1\nT:Test\nM:4/4\nL:1/8\nK:C\nCDEF|]")
        assert ok is True
        assert err == ""

    def test_empty_string(self):
        ok, err = validate_abc_str("")
        assert ok is False
        assert "empty" in err.lower()

    def test_whitespace_only(self):
        ok, err = validate_abc_str("   ")
        assert ok is False

    def test_any_nonempty_string(self):
        ok, err = validate_abc_str("hello")
        assert ok is True
