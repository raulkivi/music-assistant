"""Dataclasses for comparer-mcp's comparison result tree.

No MCP or music21 imports here — pure data shapes, per docs/architecture.md §4.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NoteInfo:
    """Snapshot of a single note's properties."""

    pitch: str  # e.g. "C#5", "rest", or "C4,E4,G4" for a chord
    midi: Optional[int]  # MIDI number of the lowest pitch; None for rests
    duration: float  # in quarter lengths
    duration_type: str  # "quarter", "eighth", etc.
    is_rest: bool
    is_chord: bool
    tie: Optional[str]  # "start" | "stop" | "continue" | None
    lyrics: Optional[str]


@dataclass
class NoteDiff:
    """Single note-level difference."""

    measure_number: int
    beat: float  # beat position within measure
    voice: int
    operation: str  # MATCH | PITCH_CHANGE | DURATION_CHANGE | SUBSTITUTION | INSERTION | DELETION
    reference: Optional[NoteInfo]  # None for INSERTION
    target: Optional[NoteInfo]  # None for DELETION
    interval_error: Optional[int] = None  # semitones, for pitch differences


@dataclass
class SignatureDiff:
    """Key or time signature that differs between reference and target."""

    measure_number: int
    reference_value: str  # e.g. "G major", "3/4"
    target_value: Optional[str]  # None if missing


@dataclass
class MeasureDiff:
    """Comparison result for one matched pair of measures."""

    measure_number: int
    similarity_score: float
    voice_count_reference: int
    voice_count_target: int
    note_diffs: list[NoteDiff] = field(default_factory=list)


@dataclass
class PartDiff:
    """Comparison result for one matched pair of parts."""

    part_name: str
    reference_part_id: str
    target_part_id: str
    similarity_score: float
    key_sig_diffs: list[SignatureDiff] = field(default_factory=list)
    time_sig_diffs: list[SignatureDiff] = field(default_factory=list)
    measure_diffs: list[MeasureDiff] = field(default_factory=list)
    measures_missing: list[int] = field(default_factory=list)  # measure numbers
    measures_extra: list[int] = field(default_factory=list)


@dataclass
class ComparisonSummary:
    """Aggregate statistics."""

    total_parts_reference: int
    total_parts_target: int
    parts_matched: int
    parts_missing: list[str]  # in reference but not target
    parts_extra: list[str]  # in target but not reference
    total_measures: int
    measures_missing: int
    measures_extra: int
    total_notes_compared: int
    notes_identical: int
    notes_pitch_changed: int
    notes_duration_changed: int
    notes_substituted: int
    notes_missing: int  # in reference but not target
    notes_extra: int  # in target but not reference
    key_signature_diffs: int
    time_signature_diffs: int


@dataclass
class ComparisonResult:
    """Top-level result of comparing two MusicXML files."""

    similarity_score: float  # 0.0 (completely different) - 1.0 (identical)
    summary: ComparisonSummary
    part_diffs: list[PartDiff] = field(default_factory=list)
