"""Manual, real-microphone tests for pitch_mcp (TR-3 in docs/requirements.md).

Not run in CI or by a plain `pytest` invocation — opt in with:

    VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m manual

Sing along with the fixture phrase in tests/fixtures/reference.musicxml
(starting on C4, 90 BPM) while these run.
"""

import time
from pathlib import Path

import pytest

from pitch_mcp.engine import (
    get_position,
    load_score,
    start_monitoring,
    stop_monitoring,
)

FIXTURE_MUSICXML = (Path(__file__).parent / "fixtures" / "reference.musicxml").read_text()


@pytest.mark.manual
class TestRealMicrophoneLifecycle:
    def test_load_start_poll_stop(self):
        result = load_score(FIXTURE_MUSICXML, "Soprano")
        sid = result["session_id"]

        try:
            start_monitoring(sid)

            # Give the audio callback a few seconds to accumulate frames
            # while the tester sings along with the fixture phrase.
            time.sleep(5.0)

            pos = get_position(sid)
            assert pos["session_id"] == sid
            assert pos["status"] in ("on_pitch", "sharp", "flat", "no_signal")

            summary = stop_monitoring(sid)["summary"]
            print(f"\nSession summary: {summary}")
            assert summary["accuracy_histogram"]["on_pitch"] + \
                summary["accuracy_histogram"]["sharp"] + \
                summary["accuracy_histogram"]["flat"] > 0, (
                "No pitch was detected — check the microphone is live and "
                "singing was audible during the 5s window."
            )
        except Exception:
            stop_monitoring(sid)
            raise

    def test_tempo_bpm_override_is_accepted(self):
        result = load_score(FIXTURE_MUSICXML, "Soprano")
        sid = result["session_id"]
        try:
            start_monitoring(sid, tempo_bpm=70)
            time.sleep(2.0)
            pos = get_position(sid)
            assert pos["session_id"] == sid
        finally:
            stop_monitoring(sid)
