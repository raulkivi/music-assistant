"""Part matching between two music21 scores.

Priority cascade per docs/architecture.md §3 (Layer 1):
    1. Exact part name (case-insensitive)
    2. MIDI program / instrument (TODO: Phase 2)
    3. Positional order
    4. Pitch range heuristic (TODO: Phase 2)

Phase 1 implements name matching with a positional fallback for parts that
have no name match on either side.
"""

from dataclasses import dataclass, field


@dataclass
class PartMatchResult:
    """Result of matching parts between a reference and target score."""

    matched: list[tuple] = field(default_factory=list)  # [(ref_part, tgt_part), ...]
    missing: list = field(default_factory=list)  # ref parts with no match
    extra: list = field(default_factory=list)  # tgt parts with no match


def _part_name(part) -> str:
    return (part.partName or "").strip().lower()


def match_parts(reference_parts, target_parts) -> PartMatchResult:
    """Match parts between two lists of music21 Part objects."""
    result = PartMatchResult()

    unmatched_ref = list(reference_parts)
    unmatched_tgt = list(target_parts)

    # 1. Exact name match (case-insensitive)
    tgt_by_name: dict[str, list] = {}
    for tgt in unmatched_tgt:
        tgt_by_name.setdefault(_part_name(tgt), []).append(tgt)

    still_unmatched_ref = []
    for ref in unmatched_ref:
        candidates = tgt_by_name.get(_part_name(ref))
        if candidates:
            tgt = candidates.pop(0)
            result.matched.append((ref, tgt))
        else:
            still_unmatched_ref.append(ref)
    unmatched_ref = still_unmatched_ref
    unmatched_tgt = [tgt for candidates in tgt_by_name.values() for tgt in candidates]

    # 2. Positional fallback for whatever is left on both sides
    for ref, tgt in zip(unmatched_ref, unmatched_tgt):
        result.matched.append((ref, tgt))

    matched_count = min(len(unmatched_ref), len(unmatched_tgt))
    result.missing.extend(unmatched_ref[matched_count:])
    result.extra.extend(unmatched_tgt[matched_count:])

    return result
