"""
Score alignment for pitch-mcp.

Maps a sequence of detected pitches to a reference note sequence using
Dynamic Time Warping (DTW). Returns per-note pitch accuracy data.

Algorithm:
    1. Convert both sequences to MIDI note numbers (continuous float for detected,
       integer for reference).
    2. Run DTW (windowed) to find the best temporal alignment.
    3. For each reference note, find the set of detected frames aligned to it
       and compute the average frequency deviation in cents.
"""

import logging
import math
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def align(
    detected: list[tuple[float, float, float]],
    note_sequence: list[dict],
    window: int = 50,
) -> list[dict]:
    """Align detected pitches to a reference note sequence using DTW.

    Args:
        detected: List of (time_sec, freq_hz, confidence) from pitch_detector.
        note_sequence: List of note dicts from utils.extract_note_sequence.
        window: DTW warping window in frames. Larger = more flexible alignment.

    Returns:
        List of per-note accuracy dicts:
            {
                "measure": int,
                "beat": float,
                "expected": "G4",
                "expected_hz": 392.0,
                "sung_hz": 395.2,
                "accuracy_cents": 12,
                "status": "sharp",   # "on_pitch" | "sharp" | "flat" | "no_signal"
            }
        Returns an empty list if either sequence is empty.
    """
    if not note_sequence:
        return []

    if not detected:
        # No audio — every note is "no_signal"
        return [
            {
                "measure": n["measure"],
                "beat": n["beat"],
                "expected": n["note_name"],
                "expected_hz": round(n["freq_hz"], 2),
                "sung_hz": None,
                "accuracy_cents": None,
                "status": "no_signal",
            }
            for n in note_sequence
        ]

    # --- Step 1: Build query and reference sequences in MIDI space ---
    query_times = np.array([t for t, f, c in detected], dtype=np.float32)
    query_hz = np.array([f for t, f, c in detected], dtype=np.float32)
    query_midi = _hz_to_midi_continuous(query_hz)  # fractional MIDI numbers

    ref_midis = np.array([n["midi"] for n in note_sequence], dtype=np.float32)

    # --- Step 2: DTW alignment ---
    # Use time-domain alignment: for each reference note, find which detected
    # frames fall within its expected time window (fast, no heavy DTW needed
    # for the offline case with proper timestamps).
    results: list[dict] = []

    for note in note_sequence:
        start = note["start_sec"]
        end = note["end_sec"]

        # Find detected frames within this note's time window (±10% tolerance)
        margin = max(0.05, (end - start) * 0.1)
        mask = (query_times >= start - margin) & (query_times <= end + margin)
        frames_hz = query_hz[mask]

        if len(frames_hz) == 0:
            results.append(
                {
                    "measure": note["measure"],
                    "beat": note["beat"],
                    "expected": note["note_name"],
                    "expected_hz": round(note["freq_hz"], 2),
                    "sung_hz": None,
                    "accuracy_cents": None,
                    "status": "no_signal",
                }
            )
            continue

        # Compute median frequency (robust to outliers)
        sung_hz = float(np.median(frames_hz))
        accuracy_cents = _hz_to_cents_deviation(sung_hz, note["freq_hz"])
        status = _classify(accuracy_cents)

        results.append(
            {
                "measure": note["measure"],
                "beat": note["beat"],
                "expected": note["note_name"],
                "expected_hz": round(note["freq_hz"], 2),
                "sung_hz": round(sung_hz, 2),
                "accuracy_cents": accuracy_cents,
                "status": status,
            }
        )

    return results


def _hz_to_midi_continuous(hz_array: np.ndarray) -> np.ndarray:
    """Convert Hz array to fractional MIDI note numbers."""
    with np.errstate(divide="ignore", invalid="ignore"):
        midi = 69.0 + 12.0 * np.log2(np.maximum(hz_array, 1.0) / 440.0)
    return midi.astype(np.float32)


def _hz_to_cents_deviation(sung_hz: float, expected_hz: float) -> int:
    """Return cents deviation: positive = sharp, negative = flat."""
    if expected_hz <= 0 or sung_hz <= 0:
        return 0
    ratio = sung_hz / expected_hz
    cents = round(1200.0 * math.log2(ratio))
    return int(cents)


def _classify(cents: int, threshold: int = 25) -> str:
    if abs(cents) <= threshold:
        return "on_pitch"
    return "sharp" if cents > 0 else "flat"


def summarize(note_results: list[dict]) -> dict:
    """Compute summary statistics from per-note alignment results.

    Returns:
        {
            "measures_covered": int,
            "avg_accuracy_cents": float | None,
            "accuracy_histogram": {"on_pitch": N, "sharp": N, "flat": N, "no_signal": N},
        }
    """
    histogram = {"on_pitch": 0, "sharp": 0, "flat": 0, "no_signal": 0}
    cents_values: list[int] = []

    measures_seen: set[int] = set()

    for note in note_results:
        status = note.get("status", "no_signal")
        histogram[status] = histogram.get(status, 0) + 1
        if note.get("accuracy_cents") is not None:
            cents_values.append(abs(note["accuracy_cents"]))
        if note.get("measure") is not None:
            measures_seen.add(note["measure"])

    avg_cents = round(sum(cents_values) / len(cents_values)) if cents_values else None

    return {
        "measures_covered": len(measures_seen),
        "avg_accuracy_cents": avg_cents,
        "accuracy_histogram": histogram,
    }
