"""Edit-distance (Levenshtein-style) alignment of two note sequences.

Per docs/architecture.md §3 (Layer 4): standard Wagner-Fischer dynamic
programming, substitution cost 0 when note signatures match, 1 otherwise;
insertion/deletion cost 1. Classifies each non-matching pair into
PITCH_CHANGE, DURATION_CHANGE, or SUBSTITUTION based on which dimension(s)
differ.
"""

from dataclasses import dataclass
from typing import Optional

from comparer_mcp.utils import note_signature


@dataclass
class AlignedNote:
    """One step of the alignment between a reference and target note sequence."""

    operation: str  # MATCH | PITCH_CHANGE | DURATION_CHANGE | SUBSTITUTION | INSERTION | DELETION
    reference: Optional[object]  # music21 note/rest/chord, or None for INSERTION
    target: Optional[object]  # music21 note/rest/chord, or None for DELETION


def _classify(ref_note, tgt_note) -> str:
    ref_pitches, ref_duration, _ = note_signature(ref_note)
    tgt_pitches, tgt_duration, _ = note_signature(tgt_note)

    if ref_pitches == tgt_pitches and ref_duration == tgt_duration:
        return "MATCH"
    if ref_pitches == tgt_pitches:
        return "DURATION_CHANGE"
    if ref_duration == tgt_duration:
        return "PITCH_CHANGE"
    return "SUBSTITUTION"


def align_notes(reference: list, target: list) -> list[AlignedNote]:
    """Align two sequences of music21 notes/rests/chords via edit distance."""
    n, m = len(reference), len(target)

    signatures_ref = [note_signature(r) for r in reference]
    signatures_tgt = [note_signature(t) for t in target]

    # dp[i][j] = edit distance between reference[:i] and target[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i
    for j in range(1, m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub_cost = 0 if signatures_ref[i - 1] == signatures_tgt[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + sub_cost,  # match / substitution
            )

    ops: list[AlignedNote] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            sub_cost = 0 if signatures_ref[i - 1] == signatures_tgt[j - 1] else 1
            if dp[i][j] == dp[i - 1][j - 1] + sub_cost:
                kind = _classify(reference[i - 1], target[j - 1])
                ops.append(AlignedNote(kind, reference[i - 1], target[j - 1]))
                i -= 1
                j -= 1
                continue
        if i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append(AlignedNote("DELETION", reference[i - 1], None))
            i -= 1
            continue
        if j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            ops.append(AlignedNote("INSERTION", None, target[j - 1]))
            j -= 1
            continue
        break  # unreachable for a correctly filled DP table

    ops.reverse()
    return ops
