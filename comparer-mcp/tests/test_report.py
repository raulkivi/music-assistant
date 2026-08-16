"""Tests for comparer_mcp.report — human-readable comparison summaries.

Builds ComparisonResult objects directly (no music21, no MCP) since
report.py is a pure function of the data model, per docs/conventions.md's
separation of concerns.
"""

from comparer_mcp.models import (
    ComparisonResult,
    ComparisonSummary,
    MeasureDiff,
    NoteDiff,
    NoteInfo,
    PartDiff,
    SignatureDiff,
)
from comparer_mcp.report import generate_report


def _summary(**overrides) -> ComparisonSummary:
    defaults = dict(
        total_parts_reference=1,
        total_parts_target=1,
        parts_matched=1,
        parts_missing=[],
        parts_extra=[],
        total_measures=1,
        measures_missing=0,
        measures_extra=0,
        total_notes_compared=0,
        notes_identical=0,
        notes_pitch_changed=0,
        notes_duration_changed=0,
        notes_substituted=0,
        notes_missing=0,
        notes_extra=0,
        key_signature_diffs=0,
        time_signature_diffs=0,
    )
    defaults.update(overrides)
    return ComparisonSummary(**defaults)


def _note_info(pitch="C4") -> NoteInfo:
    return NoteInfo(
        pitch=pitch,
        midi=60,
        duration=1.0,
        duration_type="quarter",
        is_rest=False,
        is_chord=False,
        tie=None,
        lyrics=None,
    )


def _pitch_change(measure_number, interval_error) -> NoteDiff:
    return NoteDiff(
        measure_number=measure_number,
        beat=1.0,
        voice=1,
        operation="PITCH_CHANGE",
        reference=_note_info("C4"),
        target=_note_info("D4"),
        interval_error=interval_error,
    )


class TestHeadline:
    def test_perfect_match_headline(self):
        result = ComparisonResult(similarity_score=1.0, summary=_summary())
        report = generate_report(result)
        assert "100%" in report
        assert "nearly identical" in report

    def test_substantial_difference_headline(self):
        result = ComparisonResult(similarity_score=0.4, summary=_summary())
        report = generate_report(result)
        assert "40%" in report
        assert "substantial differences" in report


class TestStructuralChanges:
    def test_missing_part_is_reported(self):
        result = ComparisonResult(
            similarity_score=0.5, summary=_summary(parts_missing=["Alto"])
        )
        report = generate_report(result)
        assert "Alto" in report
        assert "missing" in report.lower()

    def test_extra_part_is_reported(self):
        result = ComparisonResult(
            similarity_score=0.9, summary=_summary(parts_extra=["Descant"])
        )
        report = generate_report(result)
        assert "Descant" in report
        assert "added" in report.lower()

    def test_no_structural_changes_omits_the_lines(self):
        result = ComparisonResult(similarity_score=1.0, summary=_summary())
        report = generate_report(result)
        assert "missing from target" not in report.lower()
        assert "added in target" not in report.lower()


class TestPartLevelDetail:
    def test_missing_and_extra_measures_reported(self):
        part_diff = PartDiff(
            part_name="Soprano",
            reference_part_id="Soprano",
            target_part_id="Soprano",
            similarity_score=0.8,
            measures_missing=[5],
            measures_extra=[9],
        )
        result = ComparisonResult(similarity_score=0.8, summary=_summary(), part_diffs=[part_diff])
        report = generate_report(result)
        assert "Soprano" in report
        assert "5" in report
        assert "9" in report

    def test_key_signature_change_reported(self):
        part_diff = PartDiff(
            part_name="Tenor",
            reference_part_id="Tenor",
            target_part_id="Tenor",
            similarity_score=0.9,
            key_sig_diffs=[
                SignatureDiff(measure_number=12, reference_value="G major", target_value="D major")
            ],
        )
        result = ComparisonResult(similarity_score=0.9, summary=_summary(), part_diffs=[part_diff])
        report = generate_report(result)
        assert "Tenor" in report
        assert "G major" in report
        assert "D major" in report
        assert "12" in report


class TestNoteDiffGrouping:
    def test_constant_interval_error_is_reported_as_transposition(self):
        measure_diff = MeasureDiff(
            measure_number=17,
            similarity_score=0.0,
            voice_count_reference=1,
            voice_count_target=1,
            note_diffs=[_pitch_change(17, 3), _pitch_change(18, 3)],
        )
        part_diff = PartDiff(
            part_name="Bass",
            reference_part_id="Bass",
            target_part_id="Bass",
            similarity_score=0.5,
            measure_diffs=[measure_diff],
        )
        result = ComparisonResult(similarity_score=0.5, summary=_summary(), part_diffs=[part_diff])
        report = generate_report(result)
        assert "transposed" in report.lower()
        assert "3 semitone" in report

    def test_varying_interval_error_falls_back_to_generic_count(self):
        measure_diff = MeasureDiff(
            measure_number=1,
            similarity_score=0.0,
            voice_count_reference=1,
            voice_count_target=1,
            note_diffs=[_pitch_change(1, 1), _pitch_change(2, 5)],
        )
        part_diff = PartDiff(
            part_name="Bass",
            reference_part_id="Bass",
            target_part_id="Bass",
            similarity_score=0.5,
            measure_diffs=[measure_diff],
        )
        result = ComparisonResult(similarity_score=0.5, summary=_summary(), part_diffs=[part_diff])
        report = generate_report(result)
        assert "transposed" not in report.lower()
        assert "pitch change" in report.lower()

    def test_match_operations_are_not_mentioned(self):
        measure_diff = MeasureDiff(
            measure_number=1,
            similarity_score=1.0,
            voice_count_reference=1,
            voice_count_target=1,
            note_diffs=[
                NoteDiff(
                    measure_number=1,
                    beat=1.0,
                    voice=1,
                    operation="MATCH",
                    reference=_note_info(),
                    target=_note_info(),
                )
            ],
        )
        part_diff = PartDiff(
            part_name="Soprano",
            reference_part_id="Soprano",
            target_part_id="Soprano",
            similarity_score=1.0,
            measure_diffs=[measure_diff],
        )
        result = ComparisonResult(similarity_score=1.0, summary=_summary(), part_diffs=[part_diff])
        report = generate_report(result)
        assert "Soprano" not in report

    def test_measure_range_is_reported_for_multi_measure_runs(self):
        measure_diff_a = MeasureDiff(
            measure_number=17,
            similarity_score=0.0,
            voice_count_reference=1,
            voice_count_target=1,
            note_diffs=[_pitch_change(17, 3)],
        )
        measure_diff_b = MeasureDiff(
            measure_number=18,
            similarity_score=0.0,
            voice_count_reference=1,
            voice_count_target=1,
            note_diffs=[_pitch_change(18, 3)],
        )
        part_diff = PartDiff(
            part_name="Tenor",
            reference_part_id="Tenor",
            target_part_id="Tenor",
            similarity_score=0.5,
            measure_diffs=[measure_diff_a, measure_diff_b],
        )
        result = ComparisonResult(similarity_score=0.5, summary=_summary(), part_diffs=[part_diff])
        report = generate_report(result)
        assert "17" in report and "18" in report
