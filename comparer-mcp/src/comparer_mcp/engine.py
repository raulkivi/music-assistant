"""
Core comparison engine for comparer-mcp.

No MCP SDK imports here — this module is independently unit-testable, per
docs/architecture.md §2.

Orchestrates the layered comparison pipeline:
    part_matcher.match_parts()   -> matched/missing/extra parts
    (measure matching by number, inline below)
    note_aligner.align_notes()   -> per-measure note-level diff operations

Phase 1 scope (see docs/PLAN.md): part + measure + note-level comparison and
a weighted similarity score. Key/time signature diffs, voice-aware alignment,
and articulation/tie comparison are Phase 2.
"""

from pathlib import Path
from typing import Optional

from music21 import converter

from comparer_mcp.models import (
    ComparisonResult,
    ComparisonSummary,
    MeasureDiff,
    NoteDiff,
    PartDiff,
)
from comparer_mcp.note_aligner import align_notes
from comparer_mcp.part_matcher import match_parts
from comparer_mcp.utils import note_to_info, validate_musicxml

# Note-diff operations that count as "partial matches" in the note-score term
# of the similarity formula (docs/architecture.md §5): right on one axis,
# wrong on the other.
_PARTIAL_MATCH_OPS = {"PITCH_CHANGE", "DURATION_CHANGE"}

_STRUCTURE_WEIGHT = 0.3
_NOTE_WEIGHT = 0.7


class ProcessingError(Exception):
    """Raised when a comparison step fails in an expected, reportable way."""

    def __init__(self, message: str, error_code: str = "PROCESSING_FAILED"):
        super().__init__(message)
        self.error_code = error_code


def _parse_score_from_string(xml_str: str):
    ok, reason = validate_musicxml(xml_str)
    if not ok:
        raise ProcessingError(reason, "INVALID_INPUT")
    try:
        return converter.parseData(xml_str, format="musicxml")
    except Exception as e:
        raise ProcessingError(f"Failed to parse MusicXML: {e}", "INVALID_INPUT")


def _parse_score_from_path(path: Path):
    # music21's path-based parser auto-detects and decompresses .mxl, unlike
    # the raw-string path above — so file input goes through this instead of
    # reading text and reusing _parse_score_from_string.
    try:
        return converter.parse(str(path))
    except Exception as e:
        raise ProcessingError(f"Failed to parse MusicXML file: {e}", "INVALID_INPUT")


def _measure_map(part) -> dict:
    """Map measure number -> Measure for a music21 Part."""
    return {m.number: m for m in part.getElementsByClass("Measure")}


def _measure_notes(measure) -> list:
    """Notes and rests in a measure, in score order.

    Flattens voices (Phase 1 does not do voice-aware alignment — see
    docs/PLAN.md Phase 2).
    """
    return sorted(measure.flatten().notesAndRests, key=lambda n: n.offset)


def _interval_error(ref_info, tgt_info) -> Optional[int]:
    if ref_info is None or tgt_info is None:
        return None
    if ref_info.midi is None or tgt_info.midi is None:
        return None
    return abs(tgt_info.midi - ref_info.midi)


def _compare_measure(measure_number: int, ref_measure, tgt_measure) -> MeasureDiff:
    ref_notes = _measure_notes(ref_measure)
    tgt_notes = _measure_notes(tgt_measure)

    aligned = align_notes(ref_notes, tgt_notes)

    note_diffs = []
    for op in aligned:
        ref_info = note_to_info(op.reference) if op.reference is not None else None
        tgt_info = note_to_info(op.target) if op.target is not None else None
        beat = float(op.reference.beat) if op.reference is not None else float(op.target.beat)
        note_diffs.append(
            NoteDiff(
                measure_number=measure_number,
                beat=beat,
                voice=1,  # Phase 1: voices are flattened, see _measure_notes
                operation=op.operation,
                reference=ref_info,
                target=tgt_info,
                interval_error=_interval_error(ref_info, tgt_info),
            )
        )

    similarity = _note_score(note_diffs)

    ref_voice_count = len(ref_measure.voices) or 1
    tgt_voice_count = len(tgt_measure.voices) or 1

    return MeasureDiff(
        measure_number=measure_number,
        similarity_score=similarity,
        voice_count_reference=ref_voice_count,
        voice_count_target=tgt_voice_count,
        note_diffs=note_diffs,
    )


def _note_score(note_diffs: list) -> float:
    if not note_diffs:
        return 1.0
    identical = sum(1 for nd in note_diffs if nd.operation == "MATCH")
    partial = sum(1 for nd in note_diffs if nd.operation in _PARTIAL_MATCH_OPS)
    return (identical + 0.5 * partial) / len(note_diffs)


def _compare_part(ref_part, tgt_part) -> PartDiff:
    ref_measures = _measure_map(ref_part)
    tgt_measures = _measure_map(tgt_part)

    all_numbers = sorted(set(ref_measures) | set(tgt_measures))
    measure_diffs = []
    measures_missing = []
    measures_extra = []

    for number in all_numbers:
        ref_measure = ref_measures.get(number)
        tgt_measure = tgt_measures.get(number)
        if ref_measure is None:
            measures_extra.append(number)
        elif tgt_measure is None:
            measures_missing.append(number)
        else:
            measure_diffs.append(_compare_measure(number, ref_measure, tgt_measure))

    all_note_diffs = [nd for md in measure_diffs for nd in md.note_diffs]
    note_score = _note_score(all_note_diffs)
    matched_measures = len(measure_diffs)
    total_measures = max(len(ref_measures), len(tgt_measures)) or 1
    structure_score = matched_measures / total_measures
    similarity = _STRUCTURE_WEIGHT * structure_score + _NOTE_WEIGHT * note_score

    return PartDiff(
        part_name=ref_part.partName or tgt_part.partName or "",
        reference_part_id=str(ref_part.id),
        target_part_id=str(tgt_part.id),
        similarity_score=similarity,
        measure_diffs=measure_diffs,
        measures_missing=measures_missing,
        measures_extra=measures_extra,
    )


def _build_summary(match_result, part_diffs: list) -> ComparisonSummary:
    all_note_diffs = [nd for pd in part_diffs for md in pd.measure_diffs for nd in md.note_diffs]

    def _count(op):
        return sum(1 for nd in all_note_diffs if nd.operation == op)

    measures_missing = sum(len(pd.measures_missing) for pd in part_diffs)
    measures_extra = sum(len(pd.measures_extra) for pd in part_diffs)
    total_measures = sum(len(pd.measure_diffs) for pd in part_diffs) + measures_missing + measures_extra

    return ComparisonSummary(
        total_parts_reference=len(match_result.matched) + len(match_result.missing),
        total_parts_target=len(match_result.matched) + len(match_result.extra),
        parts_matched=len(match_result.matched),
        parts_missing=[p.partName for p in match_result.missing],
        parts_extra=[p.partName for p in match_result.extra],
        total_measures=total_measures,
        measures_missing=measures_missing,
        measures_extra=measures_extra,
        total_notes_compared=len(all_note_diffs),
        notes_identical=_count("MATCH"),
        notes_pitch_changed=_count("PITCH_CHANGE"),
        notes_duration_changed=_count("DURATION_CHANGE"),
        notes_substituted=_count("SUBSTITUTION"),
        notes_missing=_count("DELETION"),
        notes_extra=_count("INSERTION"),
        # Key/time signature comparison is Phase 2 (docs/PLAN.md).
        key_signature_diffs=0,
        time_signature_diffs=0,
    )


def _overall_similarity(match_result, part_diffs: list) -> float:
    total_parts = max(
        len(match_result.matched) + len(match_result.missing),
        len(match_result.matched) + len(match_result.extra),
    ) or 1
    part_structure_score = len(match_result.matched) / total_parts

    all_note_diffs = [nd for pd in part_diffs for md in pd.measure_diffs for nd in md.note_diffs]
    note_score = _note_score(all_note_diffs)

    total_measure_positions = sum(
        len(pd.measure_diffs) + len(pd.measures_missing) + len(pd.measures_extra) for pd in part_diffs
    )
    matched_measure_positions = sum(len(pd.measure_diffs) for pd in part_diffs)
    measure_structure_score = (
        matched_measure_positions / total_measure_positions if total_measure_positions else 1.0
    )

    structure_score = part_structure_score * measure_structure_score
    return _STRUCTURE_WEIGHT * structure_score + _NOTE_WEIGHT * note_score


def _compare_scores(reference, target) -> ComparisonResult:
    match_result = match_parts(list(reference.parts), list(target.parts))
    part_diffs = [_compare_part(ref, tgt) for ref, tgt in match_result.matched]

    return ComparisonResult(
        similarity_score=_overall_similarity(match_result, part_diffs),
        summary=_build_summary(match_result, part_diffs),
        part_diffs=part_diffs,
    )


def compare(reference_xml: str, target_xml: str, options: Optional[dict] = None) -> ComparisonResult:
    """Compare two MusicXML strings and return a full ComparisonResult."""
    reference = _parse_score_from_string(reference_xml)
    target = _parse_score_from_string(target_xml)
    return _compare_scores(reference, target)


def compare_files(reference: str, target: str, options: Optional[dict] = None) -> ComparisonResult:
    """Compare two MusicXML files (.musicxml, .xml, or compressed .mxl) and
    return a full ComparisonResult."""
    ref_path = Path(reference)
    tgt_path = Path(target)

    if not ref_path.exists():
        raise ProcessingError(f"Reference file not found: {reference}", "FILE_NOT_FOUND")
    if not tgt_path.exists():
        raise ProcessingError(f"Target file not found: {target}", "FILE_NOT_FOUND")

    reference_score = _parse_score_from_path(ref_path)
    target_score = _parse_score_from_path(tgt_path)
    return _compare_scores(reference_score, target_score)
