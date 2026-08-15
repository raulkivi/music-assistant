"""Tests for comparer_mcp.engine."""

from pathlib import Path

import pytest
from music21 import meter, note, stream
from music21.musicxml.m21ToXml import GeneralObjectExporter

from comparer_mcp.engine import ProcessingError, compare, compare_files

_SATB_MXL_DIR = Path(__file__).parents[2] / "omr-mcp" / "test_samples" / "pdmx_satb_samples" / "mxl"


def _score_xml(parts: dict) -> str:
    """Build a MusicXML string from {part_name: [(pitch_or_None, quarterLength), ...]}."""
    score = stream.Score()
    for part_name, notes in parts.items():
        part = stream.Part(id=part_name)
        part.partName = part_name
        part.append(meter.TimeSignature("4/4"))
        for pitch_name, ql in notes:
            if pitch_name is None:
                part.append(note.Rest(quarterLength=ql))
            else:
                part.append(note.Note(pitch_name, quarterLength=ql))
        score.insert(0, part)
    score.makeMeasures(inPlace=True)
    return GeneralObjectExporter(score).parse().decode("utf-8")


SATB_NOTES = [("C4", 1.0), ("D4", 1.0), ("E4", 1.0), ("F4", 1.0)] * 2  # 2 measures of 4/4


class TestCompareIdenticalScores:
    def test_similarity_is_one(self):
        xml = _score_xml({"Soprano": SATB_NOTES, "Alto": SATB_NOTES})

        result = compare(xml, xml)

        assert result.similarity_score == pytest.approx(1.0)
        assert result.summary.parts_matched == 2
        assert result.summary.parts_missing == []
        assert result.summary.parts_extra == []
        assert result.summary.notes_missing == 0
        assert result.summary.notes_extra == 0

    def test_all_note_diffs_are_matches(self):
        xml = _score_xml({"Soprano": SATB_NOTES})

        result = compare(xml, xml)

        all_ops = [
            nd.operation
            for pd in result.part_diffs
            for md in pd.measure_diffs
            for nd in md.note_diffs
        ]
        assert all_ops and all(op == "MATCH" for op in all_ops)


class TestComparePitchChanges:
    def test_single_pitch_change_is_detected(self):
        ref = _score_xml({"Soprano": SATB_NOTES})
        changed = list(SATB_NOTES)
        changed[0] = ("D4", 1.0)  # was C4
        tgt = _score_xml({"Soprano": changed})

        result = compare(ref, tgt)

        assert result.summary.notes_pitch_changed == 1
        assert result.similarity_score < 1.0

        pitch_changes = [
            nd
            for pd in result.part_diffs
            for md in pd.measure_diffs
            for nd in md.note_diffs
            if nd.operation == "PITCH_CHANGE"
        ]
        assert len(pitch_changes) == 1
        assert pitch_changes[0].reference.pitch == "C4"
        assert pitch_changes[0].target.pitch == "D4"
        assert pitch_changes[0].interval_error == 2  # C4->D4 is 2 semitones


class TestCompareMissingParts:
    def test_missing_part_reported(self):
        ref = _score_xml({"Soprano": SATB_NOTES, "Alto": SATB_NOTES})
        tgt = _score_xml({"Soprano": SATB_NOTES})

        result = compare(ref, tgt)

        assert result.summary.parts_missing == ["Alto"]
        assert result.summary.parts_matched == 1
        assert result.similarity_score < 1.0

    def test_extra_part_reported(self):
        ref = _score_xml({"Soprano": SATB_NOTES})
        tgt = _score_xml({"Soprano": SATB_NOTES, "Descant": SATB_NOTES})

        result = compare(ref, tgt)

        assert result.summary.parts_extra == ["Descant"]


class TestCompareMissingMeasures:
    def test_extra_measure_in_target_reported(self):
        ref = _score_xml({"Soprano": SATB_NOTES})
        tgt = _score_xml({"Soprano": SATB_NOTES + [("G4", 1.0)] * 4})

        result = compare(ref, tgt)

        part_diff = result.part_diffs[0]
        assert part_diff.measures_extra == [3]
        assert result.summary.measures_extra == 1


class TestCompareInvalidInput:
    def test_empty_reference_raises_processing_error(self):
        with pytest.raises(ProcessingError) as exc_info:
            compare("", "<score-partwise></score-partwise>")
        assert exc_info.value.error_code == "INVALID_INPUT"

    def test_unparseable_xml_raises_processing_error(self):
        with pytest.raises(ProcessingError) as exc_info:
            compare("<score-partwise>not real musicxml<<<", "<score-partwise></score-partwise>")
        assert exc_info.value.error_code == "INVALID_INPUT"


class TestCompareFiles:
    def test_missing_reference_file_raises_file_not_found(self, tmp_path):
        target = tmp_path / "target.musicxml"
        target.write_text(_score_xml({"Soprano": SATB_NOTES}))

        with pytest.raises(ProcessingError) as exc_info:
            compare_files(str(tmp_path / "nonexistent.musicxml"), str(target))
        assert exc_info.value.error_code == "FILE_NOT_FOUND"

    def test_compares_two_files(self, tmp_path):
        ref_path = tmp_path / "ref.musicxml"
        tgt_path = tmp_path / "tgt.musicxml"
        xml = _score_xml({"Soprano": SATB_NOTES})
        ref_path.write_text(xml)
        tgt_path.write_text(xml)

        result = compare_files(str(ref_path), str(tgt_path))

        assert result.similarity_score == pytest.approx(1.0)


@pytest.mark.integration
class TestCompareRealSatbFixtures:
    """End-to-end tests against real compressed .mxl SATB scores shared with
    omr-mcp (docs/PLAN.md Phase 3 notes engine reuse across servers)."""

    def test_identical_real_score_is_similarity_one(self):
        mxl_files = sorted(_SATB_MXL_DIR.glob("*.mxl"))
        assert mxl_files, f"No .mxl fixtures found under {_SATB_MXL_DIR}"

        result = compare_files(str(mxl_files[0]), str(mxl_files[0]))

        assert result.similarity_score == pytest.approx(1.0)
        assert result.summary.parts_missing == []
        assert result.summary.parts_extra == []

    def test_different_real_scores_are_not_identical(self):
        mxl_files = sorted(_SATB_MXL_DIR.glob("*.mxl"))
        assert len(mxl_files) >= 2, f"Need at least 2 .mxl fixtures under {_SATB_MXL_DIR}"

        result = compare_files(str(mxl_files[0]), str(mxl_files[1]))

        assert 0.0 <= result.similarity_score < 1.0
