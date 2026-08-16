"""Tests for comparer_mcp.engine."""

import json
from pathlib import Path

import pytest
from music21 import articulations, bar, instrument, key, meter, note, stream
from music21.musicxml.m21ToXml import GeneralObjectExporter

from comparer_mcp.engine import (
    ProcessingError,
    compare,
    compare_files,
    compare_with_annotations,
)

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


def _single_part_score_xml(part_name: str, elements: list) -> str:
    """Build a MusicXML string for one part from a raw list of music21 elements."""
    score = stream.Score()
    part = stream.Part(id=part_name)
    part.partName = part_name
    for el in elements:
        part.append(el)
    score.insert(0, part)
    score.makeMeasures(inPlace=True)
    return GeneralObjectExporter(score).parse().decode("utf-8")


def _two_voice_part_score_xml(part_name: str, voice1_notes: list, voice2_notes: list) -> str:
    """Build a MusicXML string for one part with two explicit voices in a single measure."""
    score = stream.Score()
    part = stream.Part(id=part_name)
    part.partName = part_name
    m = stream.Measure(number=1)
    m.append(meter.TimeSignature("4/4"))
    v1 = stream.Voice(id="1")
    for pitch_name, ql in voice1_notes:
        v1.append(note.Note(pitch_name, quarterLength=ql))
    v2 = stream.Voice(id="2")
    for pitch_name, ql in voice2_notes:
        v2.append(note.Note(pitch_name, quarterLength=ql))
    m.insert(0, v1)
    m.insert(0, v2)
    part.append(m)
    score.insert(0, part)
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


class TestCompareKeyAndTimeSignatures:
    def test_key_signature_diff_is_reported(self):
        notes = [note.Note(p, quarterLength=ql) for p, ql in SATB_NOTES]
        ref = _single_part_score_xml("Soprano", [meter.TimeSignature("4/4"), key.Key("C"), *notes])
        tgt = _single_part_score_xml("Soprano", [meter.TimeSignature("4/4"), key.Key("G"), *notes])

        result = compare(ref, tgt)

        part_diff = result.part_diffs[0]
        assert len(part_diff.key_sig_diffs) == 1
        assert part_diff.key_sig_diffs[0].measure_number == 1
        assert part_diff.key_sig_diffs[0].reference_value == "C major"
        assert part_diff.key_sig_diffs[0].target_value == "G major"
        assert result.summary.key_signature_diffs == 1

    def test_matching_key_signature_reports_no_diff(self):
        notes = [note.Note(p, quarterLength=ql) for p, ql in SATB_NOTES]
        ref = _single_part_score_xml("Soprano", [meter.TimeSignature("4/4"), key.Key("C"), *notes])
        tgt = _single_part_score_xml("Soprano", [meter.TimeSignature("4/4"), key.Key("C"), *notes])

        result = compare(ref, tgt)

        assert result.part_diffs[0].key_sig_diffs == []
        assert result.summary.key_signature_diffs == 0

    def test_time_signature_diff_is_reported(self):
        notes = [note.Note(p, quarterLength=ql) for p, ql in SATB_NOTES]
        ref = _single_part_score_xml("Soprano", [meter.TimeSignature("4/4"), *notes])
        tgt = _single_part_score_xml("Soprano", [meter.TimeSignature("3/4"), *notes])

        result = compare(ref, tgt)

        part_diff = result.part_diffs[0]
        assert len(part_diff.time_sig_diffs) == 1
        assert part_diff.time_sig_diffs[0].reference_value == "4/4"
        assert part_diff.time_sig_diffs[0].target_value == "3/4"
        assert result.summary.time_signature_diffs == 1


class TestCompareVoiceAwareAlignment:
    def test_pitch_change_in_one_voice_is_attributed_to_that_voice(self):
        voice1 = [("C5", 1.0), ("D5", 1.0), ("E5", 1.0), ("F5", 1.0)]
        voice2_ref = [("C4", 1.0), ("D4", 1.0), ("E4", 1.0), ("F4", 1.0)]
        voice2_tgt = [("G4", 1.0), ("D4", 1.0), ("E4", 1.0), ("F4", 1.0)]  # first note changed

        ref = _two_voice_part_score_xml("Soprano", voice1, voice2_ref)
        tgt = _two_voice_part_score_xml("Soprano", voice1, voice2_tgt)

        result = compare(ref, tgt)

        assert result.summary.total_notes_compared == 8
        assert result.summary.notes_pitch_changed == 1
        assert result.summary.notes_identical == 7

        pitch_changes = [
            nd
            for pd in result.part_diffs
            for md in pd.measure_diffs
            for nd in md.note_diffs
            if nd.operation == "PITCH_CHANGE"
        ]
        assert len(pitch_changes) == 1
        assert pitch_changes[0].voice == 2
        assert pitch_changes[0].reference.pitch == "C4"
        assert pitch_changes[0].target.pitch == "G4"

        voice1_ops = {
            nd.operation
            for pd in result.part_diffs
            for md in pd.measure_diffs
            for nd in md.note_diffs
            if nd.voice == 1
        }
        assert voice1_ops == {"MATCH"}


class TestCompareOptions:
    def test_part_filter_restricts_comparison(self):
        changed_alto = list(SATB_NOTES)
        changed_alto[0] = ("G4", 1.0)
        ref = _score_xml({"Soprano": SATB_NOTES, "Alto": SATB_NOTES})
        tgt = _score_xml({"Soprano": SATB_NOTES, "Alto": changed_alto})

        result = compare(ref, tgt, options={"part_filter": ["Soprano"]})

        assert result.summary.parts_matched == 1
        assert result.summary.parts_missing == []
        assert result.summary.parts_extra == []
        assert result.similarity_score == pytest.approx(1.0)

    def test_measure_range_restricts_comparison(self):
        changed = list(SATB_NOTES)
        changed[4] = ("G4", 1.0)  # first note of measure 2
        ref = _score_xml({"Soprano": SATB_NOTES})
        tgt = _score_xml({"Soprano": changed})

        result = compare(ref, tgt, options={"measure_range": [1, 1]})

        assert result.similarity_score == pytest.approx(1.0)
        all_note_diffs = [
            nd for pd in result.part_diffs for md in pd.measure_diffs for nd in md.note_diffs
        ]
        assert all_note_diffs and all(nd.measure_number == 1 for nd in all_note_diffs)

    def test_ignore_articulations_blanks_articulation_diffs(self):
        notes_ref = [note.Note(p, quarterLength=ql) for p, ql in SATB_NOTES]
        notes_tgt = [note.Note(p, quarterLength=ql) for p, ql in SATB_NOTES]
        notes_tgt[0].articulations = [articulations.Staccato()]
        ref = _single_part_score_xml("Soprano", notes_ref)
        tgt = _single_part_score_xml("Soprano", notes_tgt)

        result = compare(ref, tgt, options={"ignore_articulations": True})

        all_note_diffs = [
            nd for pd in result.part_diffs for md in pd.measure_diffs for nd in md.note_diffs
        ]
        assert all_note_diffs
        assert all(
            nd.target is None or nd.target.articulations == [] for nd in all_note_diffs
        )
        assert all(
            nd.reference is None or nd.reference.articulations == [] for nd in all_note_diffs
        )

    def test_invalid_measure_range_raises(self):
        xml = _score_xml({"Soprano": SATB_NOTES})
        with pytest.raises(ProcessingError) as exc_info:
            compare(xml, xml, options={"measure_range": [5, 1]})
        assert exc_info.value.error_code == "INVALID_PARAMETER"

    def test_invalid_part_filter_raises(self):
        xml = _score_xml({"Soprano": SATB_NOTES})
        with pytest.raises(ProcessingError) as exc_info:
            compare(xml, xml, options={"part_filter": "Soprano"})
        assert exc_info.value.error_code == "INVALID_PARAMETER"

    def test_normalize_pitch_aligns_transposing_instruments(self):
        ref_score = stream.Score()
        ref_part = stream.Part(id="Clarinet")
        ref_part.partName = "Clarinet"
        ref_part.atSoundingPitch = False
        ref_part.insert(0, instrument.Clarinet())
        ref_part.insert(0, meter.TimeSignature("4/4"))
        ref_part.insert(0, note.Note("D5", quarterLength=4.0))
        ref_score.insert(0, ref_part)
        ref_xml = GeneralObjectExporter(ref_score).parse().decode("utf-8")

        tgt_score = stream.Score()
        tgt_part = stream.Part(id="Flute")
        tgt_part.partName = "Flute"
        tgt_part.insert(0, instrument.Flute())
        tgt_part.insert(0, meter.TimeSignature("4/4"))
        tgt_part.insert(0, note.Note("C5", quarterLength=4.0))
        tgt_score.insert(0, tgt_part)
        tgt_xml = GeneralObjectExporter(tgt_score).parse().decode("utf-8")

        without_normalize = compare(ref_xml, tgt_xml)
        assert without_normalize.similarity_score < 1.0

        with_normalize = compare(ref_xml, tgt_xml, options={"normalize_pitch": True})
        assert with_normalize.similarity_score == pytest.approx(1.0)

    def test_expand_repeats_unfolds_simple_repeat(self):
        ref_score = stream.Score()
        ref_part = stream.Part(id="Soprano")
        ref_part.partName = "Soprano"
        m1 = stream.Measure(number=1)
        m1.append(meter.TimeSignature("4/4"))
        m1.leftBarline = bar.Repeat(direction="start")
        m1.append(note.Note("C4", quarterLength=4.0))
        m2 = stream.Measure(number=2)
        m2.append(note.Note("D4", quarterLength=4.0))
        m2.rightBarline = bar.Repeat(direction="end")
        ref_part.append(m1)
        ref_part.append(m2)
        ref_score.insert(0, ref_part)
        ref_xml = GeneralObjectExporter(ref_score).parse().decode("utf-8")

        # target already has the repeat written out in full (4 measures)
        tgt_xml = _score_xml({"Soprano": [("C4", 4.0), ("D4", 4.0), ("C4", 4.0), ("D4", 4.0)]})

        without_expand = compare(ref_xml, tgt_xml)
        assert without_expand.similarity_score < 1.0

        with_expand = compare(ref_xml, tgt_xml, options={"expand_repeats": True})
        assert with_expand.similarity_score == pytest.approx(1.0)

    def test_expand_repeats_failure_is_processing_error(self):
        # An unclosed repeat start (no matching end) makes music21's
        # expandRepeats() raise ExpanderException; confirm it's converted to
        # a reportable ProcessingError instead of crashing.
        score = stream.Score()
        part = stream.Part(id="Soprano")
        part.partName = "Soprano"
        m1 = stream.Measure(number=1)
        m1.append(meter.TimeSignature("4/4"))
        m1.leftBarline = bar.Repeat(direction="start")
        m1.append(note.Note("C4", quarterLength=4.0))
        m2 = stream.Measure(number=2)
        m2.append(note.Note("D4", quarterLength=4.0))
        part.append(m1)
        part.append(m2)
        score.insert(0, part)
        xml = GeneralObjectExporter(score).parse().decode("utf-8")

        with pytest.raises(ProcessingError) as exc_info:
            compare(xml, xml, options={"expand_repeats": True})
        assert exc_info.value.error_code == "PROCESSING_FAILED"


class TestCompareWithAnnotations:
    def test_returns_result_scores_and_aligned_pairs(self):
        ref = _score_xml({"Soprano": SATB_NOTES})
        changed = list(SATB_NOTES)
        changed[0] = ("D4", 1.0)  # was C4
        tgt = _score_xml({"Soprano": changed})

        result, reference_score, target_score, aligned_pairs = compare_with_annotations(ref, tgt)

        assert result.similarity_score < 1.0
        assert isinstance(reference_score, stream.Score)
        assert isinstance(target_score, stream.Score)
        assert len(aligned_pairs) == len(SATB_NOTES)

        pitch_change_pairs = [
            (note_diff, aligned)
            for note_diff, aligned in aligned_pairs
            if note_diff.operation == "PITCH_CHANGE"
        ]
        assert len(pitch_change_pairs) == 1
        note_diff, aligned = pitch_change_pairs[0]
        # The aligned reference/target objects belong to reference_score/target_score
        # (not the original pre-parse scores) so that annotator.py can color and
        # re-serialize exactly what was compared.
        assert aligned.reference in reference_score.recurse().notes
        assert aligned.target in target_score.recurse().notes


class TestCompareResultToDict:
    def test_to_dict_is_json_serializable(self):
        xml = _score_xml({"Soprano": SATB_NOTES})

        result = compare(xml, xml)
        payload = json.dumps(result.to_dict())

        parsed = json.loads(payload)
        assert parsed["similarity_score"] == pytest.approx(1.0)
        assert parsed["part_diffs"][0]["measure_diffs"][0]["note_diffs"][0]["operation"] == "MATCH"


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

    def test_unsupported_file_extension_raises_unsupported_format(self, tmp_path):
        ref_path = tmp_path / "reference.musicxml"
        tgt_path = tmp_path / "target.pdf"
        ref_path.write_text(_score_xml({"Soprano": SATB_NOTES}))
        tgt_path.write_text("not a musicxml file")

        with pytest.raises(ProcessingError) as exc_info:
            compare_files(str(ref_path), str(tgt_path))
        assert exc_info.value.error_code == "UNSUPPORTED_FORMAT"

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
