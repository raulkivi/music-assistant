"""Key/time signature comparison and voice grouping for comparer-mcp.

Phase 2 (docs/PLAN.md): key/time signature diffs with measure locations, plus
voice-aware grouping so note_aligner can align voice-by-voice instead of a
single sequence with every voice's notes interleaved by offset (Phase 1
behaviour, see docs/HANDOVER.md).
"""

from music21 import key as key_mod
from music21 import meter as meter_mod

from comparer_mcp.models import SignatureDiff


def _key_repr(ks) -> str:
    """Human-readable key signature, e.g. 'G major' or '2 sharps'.

    music21.key.Key (tonic + mode known) renders as 'G major' via str(); a
    bare music21.key.KeySignature (fifths only, no mode) does not, so it is
    described by its sharps/flats count instead.
    """
    if getattr(ks, "tonic", None) is not None:
        return str(ks)
    sharps = ks.sharps
    if sharps == 0:
        return "0 sharps"
    count = abs(sharps)
    kind = "sharp" if sharps > 0 else "flat"
    return f"{count} {kind}{'s' if count != 1 else ''}"


def _time_repr(ts) -> str:
    return ts.ratioString


def _signature_changes(part, cls, repr_fn) -> dict[int, str]:
    """Map measure_number -> repr(value) for measures where a `cls` element
    (KeySignature or TimeSignature) is explicitly present, i.e. where the
    signature changes."""
    changes = {}
    for m in part.getElementsByClass("Measure"):
        for el in m.getElementsByClass(cls):
            changes[m.number] = repr_fn(el)
    return changes


def _diff_signature_changes(ref_changes: dict, tgt_changes: dict) -> list[SignatureDiff]:
    """Compare two change-point maps at every measure where the reference
    has an explicit signature, carrying the target's most recent value
    forward to that same measure number."""
    diffs = []
    tgt_current = None
    tgt_index = 0
    tgt_items = sorted(tgt_changes.items())

    for number in sorted(ref_changes):
        while tgt_index < len(tgt_items) and tgt_items[tgt_index][0] <= number:
            tgt_current = tgt_items[tgt_index][1]
            tgt_index += 1
        ref_value = ref_changes[number]
        if ref_value != tgt_current:
            diffs.append(
                SignatureDiff(measure_number=number, reference_value=ref_value, target_value=tgt_current)
            )
    return diffs


def compare_key_signatures(ref_part, tgt_part) -> list[SignatureDiff]:
    """Key signature differences between two parts, at measures where the
    reference part's key signature changes."""
    ref_changes = _signature_changes(ref_part, key_mod.KeySignature, _key_repr)
    tgt_changes = _signature_changes(tgt_part, key_mod.KeySignature, _key_repr)
    return _diff_signature_changes(ref_changes, tgt_changes)


def compare_time_signatures(ref_part, tgt_part) -> list[SignatureDiff]:
    """Time signature differences between two parts, at measures where the
    reference part's time signature changes."""
    ref_changes = _signature_changes(ref_part, meter_mod.TimeSignature, _time_repr)
    tgt_changes = _signature_changes(tgt_part, meter_mod.TimeSignature, _time_repr)
    return _diff_signature_changes(ref_changes, tgt_changes)


def measure_voices(measure) -> dict:
    """Map voice number -> ordered list of notes/rests within that voice.

    A measure with no explicit multi-voice content (measure.voices empty) is
    treated as a single voice numbered 1.
    """
    voices = measure.voices
    if not voices:
        return {1: sorted(measure.notesAndRests, key=lambda n: n.offset)}

    result = {}
    for v in voices:
        try:
            vid = int(v.id)
        except (TypeError, ValueError):
            vid = v.id
        result[vid] = sorted(v.notesAndRests, key=lambda n: n.offset)
    return result


def match_voices(ref_voices: dict, tgt_voices: dict) -> list[tuple]:
    """Pair up voices between a reference and target measure.

    Cascade: 1) same voice number, 2) positional fallback for whatever is
    left on both sides. Voices with no counterpart are paired against an
    empty list (all their notes surface as INSERTION/DELETION).

    Returns a list of (voice_number, ref_notes, tgt_notes) triples.
    """
    ref_ids = sorted(ref_voices, key=str)
    tgt_ids = sorted(tgt_voices, key=str)

    matched_ids = [vid for vid in ref_ids if vid in tgt_voices]
    unmatched_ref = [vid for vid in ref_ids if vid not in tgt_voices]
    unmatched_tgt = [vid for vid in tgt_ids if vid not in ref_voices]

    pairs = [(vid, ref_voices[vid], tgt_voices[vid]) for vid in matched_ids]

    n = min(len(unmatched_ref), len(unmatched_tgt))
    for ref_vid, tgt_vid in zip(unmatched_ref[:n], unmatched_tgt[:n]):
        pairs.append((ref_vid, ref_voices[ref_vid], tgt_voices[tgt_vid]))
    for ref_vid in unmatched_ref[n:]:
        pairs.append((ref_vid, ref_voices[ref_vid], []))
    for tgt_vid in unmatched_tgt[n:]:
        pairs.append((tgt_vid, [], tgt_voices[tgt_vid]))

    return pairs
