"""Tests for comparer_mcp.measure_comparator."""

from music21 import key, meter, note, stream

from comparer_mcp.measure_comparator import (
    compare_key_signatures,
    compare_time_signatures,
    match_voices,
    measure_voices,
)


def _part_with_measures(*measures):
    part = stream.Part()
    for m in measures:
        part.append(m)
    return part


def _measure(number, elements=None, notes=None):
    m = stream.Measure(number=number)
    for el in elements or []:
        m.append(el)
    for n in notes or []:
        m.append(n)
    return m


class TestCompareKeySignatures:
    def test_identical_key_signatures_produce_no_diff(self):
        ref = _part_with_measures(_measure(1, [key.Key("G")]))
        tgt = _part_with_measures(_measure(1, [key.Key("G")]))

        assert compare_key_signatures(ref, tgt) == []

    def test_different_initial_key_signature_is_reported(self):
        ref = _part_with_measures(_measure(1, [key.Key("G")]))
        tgt = _part_with_measures(_measure(1, [key.Key("D")]))

        diffs = compare_key_signatures(ref, tgt)

        assert len(diffs) == 1
        assert diffs[0].measure_number == 1
        assert diffs[0].reference_value == "G major"
        assert diffs[0].target_value == "D major"

    def test_target_missing_key_signature_reports_none(self):
        ref = _part_with_measures(_measure(1, [key.Key("G")]))
        tgt = _part_with_measures(_measure(1, []))

        diffs = compare_key_signatures(ref, tgt)

        assert diffs[0].target_value is None

    def test_key_change_mid_piece_is_reported_at_its_measure(self):
        ref = _part_with_measures(
            _measure(1, [key.Key("C")]),
            _measure(2, []),
            _measure(3, [key.Key("G")]),
        )
        tgt = _part_with_measures(
            _measure(1, [key.Key("C")]),
            _measure(2, []),
            _measure(3, [key.Key("D")]),
        )

        diffs = compare_key_signatures(ref, tgt)

        assert [d.measure_number for d in diffs] == [3]
        assert diffs[0].reference_value == "G major"
        assert diffs[0].target_value == "D major"

    def test_bare_key_signature_reports_sharps_count(self):
        ref = _part_with_measures(_measure(1, [key.KeySignature(2)]))
        tgt = _part_with_measures(_measure(1, [key.KeySignature(-1)]))

        diffs = compare_key_signatures(ref, tgt)

        assert diffs[0].reference_value == "2 sharps"
        assert diffs[0].target_value == "1 flat"


class TestCompareTimeSignatures:
    def test_identical_time_signatures_produce_no_diff(self):
        ref = _part_with_measures(_measure(1, [meter.TimeSignature("4/4")]))
        tgt = _part_with_measures(_measure(1, [meter.TimeSignature("4/4")]))

        assert compare_time_signatures(ref, tgt) == []

    def test_different_time_signature_is_reported(self):
        ref = _part_with_measures(_measure(1, [meter.TimeSignature("4/4")]))
        tgt = _part_with_measures(_measure(1, [meter.TimeSignature("3/4")]))

        diffs = compare_time_signatures(ref, tgt)

        assert len(diffs) == 1
        assert diffs[0].reference_value == "4/4"
        assert diffs[0].target_value == "3/4"

    def test_time_signature_change_mid_piece_is_reported_at_its_measure(self):
        ref = _part_with_measures(
            _measure(1, [meter.TimeSignature("4/4")]),
            _measure(2, [meter.TimeSignature("3/4")]),
        )
        tgt = _part_with_measures(
            _measure(1, [meter.TimeSignature("4/4")]),
            _measure(2, []),
        )

        diffs = compare_time_signatures(ref, tgt)

        assert [d.measure_number for d in diffs] == [2]
        assert diffs[0].target_value == "4/4"  # carried forward from measure 1


class TestMeasureVoices:
    def test_measure_without_voices_is_a_single_voice(self):
        m = _measure(1, notes=[note.Note("C4", quarterLength=1.0), note.Note("D4", quarterLength=1.0)])

        voices = measure_voices(m)

        assert list(voices) == [1]
        assert [n.nameWithOctave for n in voices[1]] == ["C4", "D4"]

    def test_measure_with_voices_splits_by_voice_id(self):
        m = stream.Measure(number=1)
        v1 = stream.Voice(id="1")
        v1.append(note.Note("C4", quarterLength=1.0))
        v2 = stream.Voice(id="2")
        v2.append(note.Note("C3", quarterLength=1.0))
        m.insert(0, v1)
        m.insert(0, v2)

        voices = measure_voices(m)

        assert set(voices) == {1, 2}
        assert [n.nameWithOctave for n in voices[1]] == ["C4"]
        assert [n.nameWithOctave for n in voices[2]] == ["C3"]


class TestMatchVoices:
    def test_matches_by_same_voice_number(self):
        ref = {1: ["r1"], 2: ["r2"]}
        tgt = {1: ["t1"], 2: ["t2"]}

        pairs = match_voices(ref, tgt)

        assert sorted(pairs) == [(1, ["r1"], ["t1"]), (2, ["r2"], ["t2"])]

    def test_falls_back_to_position_for_unmatched_ids(self):
        ref = {1: ["r1"]}
        tgt = {2: ["t2"]}

        pairs = match_voices(ref, tgt)

        assert pairs == [(1, ["r1"], ["t2"])]

    def test_extra_reference_voice_pairs_with_empty_target(self):
        ref = {1: ["r1"], 2: ["r2"]}
        tgt = {1: ["t1"]}

        pairs = match_voices(ref, tgt)

        assert (2, ["r2"], []) in pairs

    def test_extra_target_voice_pairs_with_empty_reference(self):
        ref = {1: ["r1"]}
        tgt = {1: ["t1"], 2: ["t2"]}

        pairs = match_voices(ref, tgt)

        assert (2, [], ["t2"]) in pairs
