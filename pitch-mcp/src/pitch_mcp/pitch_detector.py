"""
Pitch detector for pitch-mcp.

Primary backend: librosa (pYIN algorithm) — pure Python, no system dependencies,
excellent accuracy for monophonic singing voice.

Optional backend: crepe (CNN-based, higher accuracy for noisy environments, requires
TensorFlow — install manually and set PITCH_BACKEND=crepe).

Backend is selected by the PITCH_BACKEND environment variable (default: librosa).
"""

import logging
import os
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Confidence threshold for crepe (pYIN uses voiced/unvoiced flags instead)
_CREPE_CONFIDENCE_THRESHOLD = 0.5


def get_backend() -> str:
    """Return the active pitch detection backend name."""
    return os.environ.get("PITCH_BACKEND", "librosa").lower()


def detect_pitches(audio_path: str) -> list[tuple[float, float, float]]:
    """Detect pitches from a WAV file.

    Args:
        audio_path: Path to a WAV file (any sample rate; stereo is mixed to mono).

    Returns:
        List of (time_sec, freq_hz, confidence) tuples for voiced frames only.
        Only frames with a detected pitch > 0 Hz are returned.

    Raises:
        RuntimeError: if the backend is unavailable or the file cannot be read.
        FileNotFoundError: if audio_path does not exist.
    """
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path!r}")

    backend = get_backend()

    if backend == "crepe":
        return _detect_crepe(audio_path)
    else:
        return _detect_librosa(audio_path)


def _detect_librosa(audio_path: str) -> list[tuple[float, float, float]]:
    """Detect pitches using librosa's pYIN algorithm.

    pYIN is a probabilistic extension of YIN, well-suited for monophonic singing voice.
    It returns voiced/unvoiced flags per frame, avoiding false pitch detections.
    """
    try:
        import librosa
    except ImportError as e:
        raise RuntimeError(
            f"librosa is not available: {e}. Install it with: pip install librosa"
        )

    try:
        y, sr = librosa.load(audio_path, sr=None, mono=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load audio file {audio_path!r}: {e}")

    if len(y) == 0:
        return []

    hop_length = 512
    fmin = librosa.note_to_hz("C2")   # ~65 Hz — Bass lowest
    fmax = librosa.note_to_hz("C7")   # ~2093 Hz — Soprano highest

    try:
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y,
            fmin=fmin,
            fmax=fmax,
            sr=sr,
            hop_length=hop_length,
        )
    except Exception as e:
        raise RuntimeError(f"pYIN pitch detection failed: {e}")

    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

    results: list[tuple[float, float, float]] = []
    for t, freq, voiced, prob in zip(times, f0, voiced_flag, voiced_prob):
        if voiced and not np.isnan(freq) and freq > 0:
            results.append((round(float(t), 4), round(float(freq), 2), round(float(prob), 4)))

    return results


def _detect_crepe(audio_path: str) -> list[tuple[float, float, float]]:
    """Detect pitches using the CREPE CNN model (requires TensorFlow)."""
    try:
        import crepe
        from scipy.io import wavfile
    except ImportError as e:
        raise RuntimeError(
            f"crepe or scipy not available: {e}. "
            "Install with: pip install crepe tensorflow"
        )

    sr, audio = wavfile.read(audio_path)

    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    elif audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    time, frequency, confidence, _ = crepe.predict(audio, sr, viterbi=True, verbose=0)

    results: list[tuple[float, float, float]] = []
    for t, f, c in zip(time, frequency, confidence):
        if f > 0 and c >= _CREPE_CONFIDENCE_THRESHOLD:
            results.append((round(float(t), 4), round(float(f), 2), round(float(c), 4)))

    return results
