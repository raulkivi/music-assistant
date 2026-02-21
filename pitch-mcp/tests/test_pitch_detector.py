"""Unit tests for pitch_mcp.pitch_detector."""

import math
import os
import tempfile

import numpy as np
import pytest
from scipy.io.wavfile import write as wav_write

from pitch_mcp.pitch_detector import detect_pitches, get_backend


def _make_sine_wav(freq_hz: float, duration_sec: float = 2.0, sr: int = 22050) -> str:
    """Create a temporary WAV file with a sine wave at the given frequency.

    Returns the path to the temp file (caller must delete it).
    """
    t = np.linspace(0, duration_sec, int(sr * duration_sec))
    audio = (0.5 * np.sin(2 * np.pi * freq_hz * t)).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    wav_write(path, sr, (audio * 32767).astype(np.int16))
    return path


class TestGetBackend:
    def test_default_is_librosa(self):
        old = os.environ.pop("PITCH_BACKEND", None)
        try:
            assert get_backend() == "librosa"
        finally:
            if old is not None:
                os.environ["PITCH_BACKEND"] = old

    def test_env_override(self):
        old = os.environ.get("PITCH_BACKEND")
        os.environ["PITCH_BACKEND"] = "crepe"
        try:
            assert get_backend() == "crepe"
        finally:
            if old is None:
                del os.environ["PITCH_BACKEND"]
            else:
                os.environ["PITCH_BACKEND"] = old


class TestDetectPitches:
    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            detect_pitches("/nonexistent/audio.wav")

    def test_a4_sine_detected(self):
        path = _make_sine_wav(440.0)
        try:
            pitches = detect_pitches(path)
            assert len(pitches) > 0, "Should detect voiced frames in a sine wave"
            freqs = [f for t, f, c in pitches]
            avg = sum(freqs) / len(freqs)
            # pYIN should be very accurate on a clean sine wave
            assert abs(avg - 440.0) < 5.0, f"Expected ~440 Hz, got {avg:.1f} Hz"
        finally:
            os.unlink(path)

    def test_result_format(self):
        path = _make_sine_wav(440.0)
        try:
            pitches = detect_pitches(path)
            for item in pitches:
                assert len(item) == 3
                t, f, c = item
                assert t >= 0
                assert f > 0
                assert 0 <= c <= 1
        finally:
            os.unlink(path)

    def test_g4_sine_detected(self):
        # G4 = 392 Hz
        g4_hz = 440.0 * (2 ** (-5 / 12))
        path = _make_sine_wav(g4_hz)
        try:
            pitches = detect_pitches(path)
            assert len(pitches) > 0
            freqs = [f for t, f, c in pitches]
            avg = sum(freqs) / len(freqs)
            assert abs(avg - g4_hz) < 10.0, f"Expected ~{g4_hz:.1f} Hz, got {avg:.1f} Hz"
        finally:
            os.unlink(path)

    def test_times_are_increasing(self):
        path = _make_sine_wav(440.0)
        try:
            pitches = detect_pitches(path)
            times = [t for t, f, c in pitches]
            assert times == sorted(times)
        finally:
            os.unlink(path)

    def test_stereo_wav_accepted(self):
        sr = 22050
        t = np.linspace(0, 1.0, sr)
        mono = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        stereo = np.stack([mono, mono], axis=1)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        wav_write(path, sr, (stereo * 32767).astype(np.int16))
        try:
            pitches = detect_pitches(path)
            assert len(pitches) > 0
        finally:
            os.unlink(path)
