"""Tests for comparer_mcp.note_aligner."""

from music21 import note

from comparer_mcp.note_aligner import align_notes


class TestAlignNotes:
    def test_identical_sequences_are_all_matches(self):
        ref = [note.Note("C4", quarterLength=1.0), note.Note("D4", quarterLength=1.0)]
        tgt = [note.Note("C4", quarterLength=1.0), note.Note("D4", quarterLength=1.0)]

        ops = align_notes(ref, tgt)

        assert [op.operation for op in ops] == ["MATCH", "MATCH"]
        assert ops[0].reference is ref[0]
        assert ops[0].target is tgt[0]

    def test_pitch_change_same_duration(self):
        ref = [note.Note("C4", quarterLength=1.0)]
        tgt = [note.Note("D4", quarterLength=1.0)]

        ops = align_notes(ref, tgt)

        assert [op.operation for op in ops] == ["PITCH_CHANGE"]

    def test_duration_change_same_pitch(self):
        ref = [note.Note("C4", quarterLength=1.0)]
        tgt = [note.Note("C4", quarterLength=0.5)]

        ops = align_notes(ref, tgt)

        assert [op.operation for op in ops] == ["DURATION_CHANGE"]

    def test_substitution_both_differ(self):
        ref = [note.Note("C4", quarterLength=1.0)]
        tgt = [note.Note("D4", quarterLength=0.5)]

        ops = align_notes(ref, tgt)

        assert [op.operation for op in ops] == ["SUBSTITUTION"]

    def test_insertion(self):
        ref = [note.Note("C4", quarterLength=1.0)]
        tgt = [note.Note("C4", quarterLength=1.0), note.Note("D4", quarterLength=1.0)]

        ops = align_notes(ref, tgt)

        assert [op.operation for op in ops] == ["MATCH", "INSERTION"]
        assert ops[1].reference is None
        assert ops[1].target is tgt[1]

    def test_deletion(self):
        ref = [note.Note("C4", quarterLength=1.0), note.Note("D4", quarterLength=1.0)]
        tgt = [note.Note("C4", quarterLength=1.0)]

        ops = align_notes(ref, tgt)

        assert [op.operation for op in ops] == ["MATCH", "DELETION"]
        assert ops[1].reference is ref[1]
        assert ops[1].target is None

    def test_empty_reference_is_all_insertions(self):
        tgt = [note.Note("C4", quarterLength=1.0)]

        ops = align_notes([], tgt)

        assert [op.operation for op in ops] == ["INSERTION"]

    def test_empty_target_is_all_deletions(self):
        ref = [note.Note("C4", quarterLength=1.0)]

        ops = align_notes(ref, [])

        assert [op.operation for op in ops] == ["DELETION"]

    def test_both_empty_is_no_ops(self):
        ops = align_notes([], [])
        assert ops == []

    def test_uses_minimal_edit_distance_not_greedy_substitution(self):
        # A single note inserted in the middle should be detected as an
        # INSERTION, not cascade into substitutions for every note after it.
        ref = [
            note.Note("C4", quarterLength=1.0),
            note.Note("D4", quarterLength=1.0),
            note.Note("E4", quarterLength=1.0),
        ]
        tgt = [
            note.Note("C4", quarterLength=1.0),
            note.Note("F4", quarterLength=1.0),
            note.Note("D4", quarterLength=1.0),
            note.Note("E4", quarterLength=1.0),
        ]

        ops = align_notes(ref, tgt)

        assert [op.operation for op in ops] == ["MATCH", "INSERTION", "MATCH", "MATCH"]
