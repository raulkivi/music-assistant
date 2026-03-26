# MusicXML Comparison: Research & Recommendations

Research date: 2026-03-26

## Goal

Find or build a tool for comprehensive MusicXML comparison that surfaces differences
at multiple levels: missing measures, voices, notes, and quantifies the scale of divergence.

---

## Existing Tools / Libraries

| Tool | Type | Stars | Usefulness |
|------|------|-------|------------|
| **music21** `alpha.analysis.aligner` + `hasher` | Python, note-level stream alignment using edit distance | 2.4k (whole lib) | Closest match but alpha-quality; only compares flat note streams (pitch + duration); no measure/voice/part-level awareness |
| **labocho/musicxmldiff** | Vue/TypeScript web app | 3 | Visual diff, beta, no .mxl support, no `score-timewise`, no API |
| **Shoobx/xmldiff** | Python, generic XML tree diff | 226 | Structural XML comparison — not music-aware. Reports every `<divisions>` difference as equal to a missing note |
| **partitura** (CPJKU) | Python, symbolic music I/O | 338 | Excellent MusicXML parser with rich data model (parts, notes, measures, voices, beat maps) — great foundation to build comparison on, but has no built-in comparison |

### Key finding

**No existing library provides comprehensive, music-aware MusicXML comparison.**

---

## Why Generic XML Diff Fails

MusicXML files representing identical music can differ wildly in XML structure:
- Different `<divisions>` values
- Attribute ordering variations
- Default-vs-explicit values
- Enharmonic spellings (C# vs Db)
- Different voice numbering

A generic XML diff produces noise, not meaningful musical differences.

---

## music21's StreamAligner (Best Existing Match)

Module: `music21.alpha.analysis.aligner`

### What it does
- Uses edit-distance algorithm on hashed note streams
- Supports operations: Insertion, Deletion, Substitution, NoChange
- Produces a `similarityScore` (0.0–1.0)
- Configurable hasher: pitch, duration, offset, octave, intervals, accidentals

### What it lacks
- **Alpha quality** — API may change
- Works only on **flat streams** — no measure/voice/part structure
- No structured diff report (just a similarity score + change list)
- No summary statistics (e.g., "3 missing measures, 12 wrong notes")

### Example usage
```python
from music21 import converter, alpha

score1 = converter.parse('file1.musicxml')
score2 = converter.parse('file2.musicxml')

sa = alpha.analysis.aligner.StreamAligner(
    score1.flatten(), score2.flatten()
)
sa.align()
print(sa.similarityScore)  # 0.0 – 1.0
print(sa.changesCount)     # {Insertion: N, Deletion: N, Substitution: N, NoChange: N}
```

---

## Recommended Approach: Custom Comparator on music21

`music21` is the strongest choice for the parsing layer because:
- Loads MusicXML into a rich hierarchy: `Score → Part → Measure → Voice → Note/Rest/Chord`
- Already has `StreamAligner` for note-level alignment
- Provides `.recurse()` and `.getElementsByClass()` for structured traversal
- Normalizes enharmonics, divisions, offsets — handles "same music, different XML"

### Multi-level comparison design

| Level | What to compare | Metric |
|-------|----------------|--------|
| **Score** | Number of parts, part names/instruments | Parts missing/added |
| **Part** | Measure count, key/time/clef signatures | Structural divergence |
| **Measure** | Number of voices, total duration, barline type | Missing/extra measures |
| **Voice** | Note sequence within each voice | Edit distance via `StreamAligner` |
| **Note** | Pitch, duration, articulations, dynamics, ties | Substitution detail |

### Output structure (proposed)

```python
{
    "similarity_score": 0.87,
    "summary": {
        "parts_missing": ["Alto"],
        "parts_extra": [],
        "measures_missing": 2,
        "measures_extra": 0,
        "notes_different": 14,
        "notes_missing": 3,
        "notes_extra": 1,
    },
    "details": {
        "part_diffs": [...],       # per-part breakdown
        "measure_diffs": [...],    # per-measure breakdown
        "note_diffs": [...],       # individual note changes
    }
}
```

### Estimated scope

~300–500 lines of Python on top of music21 parsing + the existing `StreamAligner`.

---

## Alternative: partitura as parser

`partitura` (Apache 2.0) has a cleaner modern API and direct numpy integration,
making it attractive for batch comparison. However:
- Smaller community (338 stars vs 2.4k)
- No built-in alignment/diff at all
- Would need to build everything from scratch

Use partitura if music21's overhead or alpha-quality aligner is a blocker.

---

## References

- music21 aligner docs: https://www.music21.org/music21docs/moduleReference/moduleAlphaAnalysisAligner.html
- music21 hasher docs: https://www.music21.org/music21docs/moduleReference/moduleAlphaAnalysisHasher.html
- musicxmldiff (web app): https://github.com/labocho/musicxmldiff
- xmldiff (generic): https://github.com/Shoobx/xmldiff
- partitura: https://github.com/CPJKU/partitura
- MusicXML spec (W3C): https://github.com/w3c/musicxml
