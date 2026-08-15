"""Tests for comparer_mcp.utils."""

from music21 import chord, note, pitch, tie

from comparer_mcp.utils import note_signature, note_to_info, validate_musicxml


class TestValidateMusicxml:
    def test_empty_string_is_invalid(self):
        ok, reason = validate_musicxml("")
        assert ok is False
        assert "empty" in reason.lower()

    def test_whitespace_only_is_invalid(self):
        ok, reason = validate_musicxml("   \n  ")
        assert ok is False

    def test_missing_root_element_is_invalid(self):
        ok, reason = validate_musicxml("<not-musicxml/>")
        assert ok is False
        assert "musicxml" in reason.lower()

    def test_score_partwise_is_valid(self):
        ok, reason = validate_musicxml("<score-partwise>...</score-partwise>")
        assert ok is True
        assert reason == ""

    def test_score_timewise_is_valid(self):
        ok, reason = validate_musicxml("<score-timewise>...</score-timewise>")
        assert ok is True


class TestNoteToInfo:
    def test_simple_note(self):
        n = note.Note("C#5", quarterLength=0.5)
        info = note_to_info(n)
        assert info.pitch == "C#5"
        assert info.midi == 73
        assert info.duration == 0.5
        assert info.duration_type == "eighth"
        assert info.is_rest is False
        assert info.is_chord is False
        assert info.tie is None
        assert info.lyrics is None

    def test_rest(self):
        r = note.Rest(quarterLength=1.0)
        info = note_to_info(r)
        assert info.pitch == "rest"
        assert info.midi is None
        assert info.is_rest is True
        assert info.duration_type == "quarter"

    def test_chord_sorts_pitches_and_uses_lowest_midi(self):
        c = chord.Chord(["E4", "C4", "G4"])
        info = note_to_info(c)
        assert info.is_chord is True
        assert info.pitch == "C4,E4,G4"
        assert info.midi == pitch.Pitch("C4").midi

    def test_tie_start(self):
        n = note.Note("D4")
        n.tie = tie.Tie("start")
        info = note_to_info(n)
        assert info.tie == "start"

    def test_lyrics(self):
        n = note.Note("D4")
        n.addLyric("Al")
        info = note_to_info(n)
        assert info.lyrics == "Al"

    def test_no_lyrics_is_none(self):
        n = note.Note("D4")
        info = note_to_info(n)
        assert info.lyrics is None


class TestNoteSignature:
    def test_identical_notes_have_identical_signature(self):
        a = note.Note("C4", quarterLength=1.0)
        b = note.Note("C4", quarterLength=1.0)
        assert note_signature(a) == note_signature(b)

    def test_different_pitch_differs(self):
        a = note.Note("C4", quarterLength=1.0)
        b = note.Note("D4", quarterLength=1.0)
        assert note_signature(a) != note_signature(b)

    def test_different_duration_differs(self):
        a = note.Note("C4", quarterLength=1.0)
        b = note.Note("C4", quarterLength=0.5)
        assert note_signature(a) != note_signature(b)

    def test_rest_signature_has_no_pitches(self):
        r = note.Rest(quarterLength=1.0)
        pitches, duration, is_rest = note_signature(r)
        assert pitches == ()
        assert is_rest is True

    def test_chord_signature_is_sorted_pitch_tuple(self):
        c1 = chord.Chord(["E4", "C4", "G4"])
        c2 = chord.Chord(["C4", "G4", "E4"])
        assert note_signature(c1) == note_signature(c2)
