"""Integration tests for pitch_mcp (TR-2 in docs/requirements.md).

Runs `analyze_recording` against the committed fixture pair in
`tests/fixtures/` instead of audio synthesized in-memory per test.
"""

import math
from pathlib import Path

import pytest

from pitch_mcp.engine import analyze_recording

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_WAV = FIXTURES_DIR / "soprano_phrase.wav"
FIXTURE_MUSICXML = FIXTURES_DIR / "reference.musicxml"


@pytest.mark.integration
class TestAnalyzeRecordingFixture:
    def _run(self):
        musicxml = FIXTURE_MUSICXML.read_text()
        return analyze_recording(str(FIXTURE_WAV), musicxml, "Soprano")

    def test_note_accuracy_has_entries(self):
        result = self._run()
        assert len(result["note_accuracy"]) > 0

    def test_avg_accuracy_cents_is_finite(self):
        result = self._run()
        avg = result["avg_accuracy_cents"]
        assert avg is not None
        assert math.isfinite(avg)

    def test_measures_covered_matches_fixture(self):
        result = self._run()
        assert result["measures_covered"] == 5

    def test_runs_without_a_microphone(self):
        # No sounddevice/portaudio interaction anywhere in this path —
        # offline analysis must work on a machine with no audio hardware.
        result = self._run()
        assert "note_accuracy" in result
