"""
Input validation and music21 conversion helpers for comparer-mcp.

No MCP SDK imports and no comparison orchestration logic here.
"""

from typing import Optional

from comparer_mcp.models import NoteInfo


def validate_musicxml(musicxml: str) -> tuple[bool, str]:
    """Return (True, '') if the string looks like MusicXML, else (False, reason)."""
    if not musicxml or not musicxml.strip():
        return False, "MusicXML string is empty."
    if "<score-partwise" not in musicxml and "<score-timewise" not in musicxml:
        return False, (
            "Input does not appear to be MusicXML: "
            "no <score-partwise> or <score-timewise> root element found."
        )
    return True, ""


def note_to_info(note_obj) -> NoteInfo:
    """Convert a music21 Note/Rest/Chord into a NoteInfo snapshot."""
    is_rest = note_obj.isRest
    is_chord = note_obj.isChord

    midi: Optional[int]
    if is_rest:
        pitch_str = "rest"
        midi = None
    elif is_chord:
        pitches = sorted(note_obj.pitches, key=lambda p: p.midi)
        pitch_str = ",".join(p.nameWithOctave for p in pitches)
        midi = pitches[0].midi
    else:
        pitch_str = note_obj.pitch.nameWithOctave
        midi = note_obj.pitch.midi

    tie_type = note_obj.tie.type if note_obj.tie is not None else None

    lyrics = None
    note_lyrics = getattr(note_obj, "lyrics", None)
    if note_lyrics:
        texts = [lyric.text for lyric in note_lyrics if lyric.text]
        if texts:
            lyrics = " ".join(texts)

    return NoteInfo(
        pitch=pitch_str,
        midi=midi,
        duration=float(note_obj.duration.quarterLength),
        duration_type=note_obj.duration.type or "complex",
        is_rest=is_rest,
        is_chord=is_chord,
        tie=tie_type,
        lyrics=lyrics,
    )


def note_signature(note_obj) -> tuple:
    """Hashable signature used for edit-distance alignment.

    Two notes are considered a MATCH by the aligner when their signatures are
    equal: same pitch(es), same duration, same rest/non-rest status.
    """
    if note_obj.isRest:
        pitches: tuple = ()
    elif note_obj.isChord:
        pitches = tuple(sorted(p.midi for p in note_obj.pitches))
    else:
        pitches = (note_obj.pitch.midi,)
    return (pitches, round(float(note_obj.duration.quarterLength), 6), note_obj.isRest)
