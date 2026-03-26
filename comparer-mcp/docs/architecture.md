# MusicXML Comparer — Vision & Architecture

Created: 2026-03-26
Status: Design draft
Parent research: [../../docs/musicxml-comparison-research.md](../../docs/musicxml-comparison-research.md)

---

## 1. Purpose

An independent MCP server (`comparer-mcp`) for **music-aware comparison** of two
MusicXML files. Like all servers in this project, it follows the conventions in
[../../docs/conventions.md](../../docs/conventions.md) and separates MCP protocol (`server.py`) from
business logic (`engine.py`). It provides a structured, multi-level diff report
that answers:

- **Are these the same piece?** (global similarity score)
- **What is the scale of difference?** (missing parts, measures, voices)
- **Where exactly do they differ?** (per-note detail with measure/beat locations)

### Primary use cases

| Use case | Description |
|----------|-------------|
| **Version / arrangement comparison** | Compare different versions of the same piece (e.g. simplified vs full arrangement, editor A vs editor B) to understand exactly what changed — added harmonies, removed voices, transposed sections, altered rhythms |
| **OMR quality evaluation** | Compare `omr-mcp` output against a known-good reference MusicXML to measure recognition accuracy |
| **Round-trip fidelity** | Verify MusicXML → ABC → MusicXML through `musicxml-abc-mcp` preserves music content |
| **Regression testing** | Detect regressions when OMR models or conversion logic change |
| **Score editing validation** | Confirm that LLM-driven edits (via ABC notation) only changed intended elements |
| **Choir rehearsal preparation** | A conductor compares two editions of a choral work to decide which to use, seeing at a glance which measures/voices differ |

---

## 2. High-Level Architecture

```
┌───────────────────────────────────────────────────────────┐
│                      MCP Client                           │
│        (Claude Desktop / web app / test script)           │
└──────────────────────────┬────────────────────────────────┘
                           │  stdio (JSON-RPC)
┌──────────────────────────▼────────────────────────────────┐
│                     server.py                             │
│                                                           │
│  compare_musicxml()       → full diff JSON                │
│  compare_musicxml_files() → full diff JSON                │
│  quick_similarity()       → score + summary               │
│  list_changes()           → filtered note diffs           │
│  health_check()           → status                        │
│  list_capabilities()      → server metadata               │
└──────────────────────────┬────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────┐
│                     engine.py                             │
│              (NO mcp imports — unit-testable)             │
│                                                           │
│  compare(ref_xml, tgt_xml, options) → ComparisonResult    │
│  compare_files(ref_path, tgt_path, options)               │
│                                                           │
│  Internally delegates to:                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │  1. ScoreComparator  (comparator.py)            │     │
│   │     └─ 2. PartMatcher  (part_matcher.py)        │     │
│   │         └─ 3. MeasureComparator                 │     │
│   │             └─ 4. NoteAligner (note_aligner.py) │     │
│   └─────────────────────────────────────────────────┘     │
└──────────────────────────┬────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────┐
│                    music21 library                         │
│   converter.parse() → Score → Part → Measure → Note       │
│   alpha.analysis.aligner.StreamAligner (edit distance)     │
└───────────────────────────────────────────────────────────┘
```

---

## 3. Comparison Pipeline — Layer by Layer

### Layer 1: Score-Level Comparison

Compares the top-level structure of both scores.

**Inputs:** Two `music21.stream.Score` objects.

**Compares:**
- Number and names of parts (Soprano, Alto, Tenor, Bass)
- Title, composer metadata
- Total measure count

**Part matching strategy:**
Match parts between scores using a priority cascade:
1. Exact part name match (case-insensitive)
2. MIDI program / instrument match
3. Positional order (first↔first, second↔second)
4. Best-effort by note range (soprano range → soprano)

**Output:**
- List of matched part pairs: `[(part_a, part_b), ...]`
- Unmatched parts in A → "missing from target"
- Unmatched parts in B → "extra in target"

### Layer 2: Part-Level Comparison

For each matched part pair, compare structural attributes.

**Compares:**
- Key signatures and where they change
- Time signatures and where they change
- Clef assignments
- Measure count mismatch (part-local)

**Measure matching strategy:**
- Primary: Match by measure number
- Handle pickup measures (measure 0 or anacrusis)
- Handle repeat expansions / unrolling differences

**Output per part:**
- Measures present in A but missing in B (and vice versa)
- Key/time/clef signature differences with measure locations

### Layer 3: Measure-Level Comparison

For each matched measure pair within a part, compare contents.

**Compares:**
- Number of voices
- Total sounding duration
- Presence of rests vs notes

**Voice matching strategy:**
- Match by voice number (most MusicXML uses voice 1, 2, ...)
- Fallback: match by pitch range centroid if voice numbers differ

**Output per measure:**
- Voice count mismatch
- Duration mismatch
- Flag: structurally identical / minor differences / major differences

### Layer 4: Voice-Level Alignment

For each matched voice pair within a measure, align the note sequences.

**Core algorithm:** Edit-distance alignment (Levenshtein-style), leveraging
`music21.alpha.analysis.aligner.StreamAligner` internally or a custom implementation
if the alpha API is insufficient.

**Hash dimensions per note element:**
- MIDI pitch (integer)
- Duration in quarter lengths (float)
- Is rest (boolean)
- Is chord (boolean) — and if so, all pitches sorted

**Operations detected:**
| Operation | Meaning |
|-----------|---------|
| `MATCH` | Notes are identical |
| `PITCH_CHANGE` | Same position/duration, different pitch |
| `DURATION_CHANGE` | Same pitch, different duration |
| `SUBSTITUTION` | Both pitch and duration differ |
| `INSERTION` | Note present in target but not reference |
| `DELETION` | Note present in reference but not target |

### Layer 5: Note-Level Detail

For each non-matching note pair, produce a detailed diff.

**Compares (when both notes exist):**
- Pitch: MIDI number, enharmonic spelling, octave
- Duration: quarter-length value, notated type (eighth, quarter, etc.)
- Accidentals: explicit vs implied by key signature
- Ties: start/stop/continue
- Articulations: staccato, accent, fermata, etc.
- Dynamics: attached dynamic markings
- Lyrics: text syllables

**Output per note diff:**
```python
NoteDiff(
    measure_number=14,
    beat=2.5,
    voice=1,
    operation="PITCH_CHANGE",
    reference=NoteInfo(pitch="C#5", duration=0.5, midi=73),
    target=NoteInfo(pitch="D5", duration=0.5, midi=74),
    interval_error=1,  # semitones off
)
```

---

## 4. Data Model

```python
@dataclass
class ComparisonResult:
    """Top-level result of comparing two MusicXML files."""
    similarity_score: float          # 0.0 (completely different) – 1.0 (identical)
    summary: ComparisonSummary
    part_diffs: list[PartDiff]

@dataclass
class ComparisonSummary:
    """Aggregate statistics."""
    total_parts_reference: int
    total_parts_target: int
    parts_matched: int
    parts_missing: list[str]         # in reference but not target
    parts_extra: list[str]           # in target but not reference
    total_measures: int
    measures_missing: int
    measures_extra: int
    total_notes_compared: int
    notes_identical: int
    notes_pitch_changed: int
    notes_duration_changed: int
    notes_substituted: int
    notes_missing: int               # in reference but not target
    notes_extra: int                 # in target but not reference
    key_signature_diffs: int
    time_signature_diffs: int

@dataclass
class PartDiff:
    """Comparison result for one matched pair of parts."""
    part_name: str
    reference_part_id: str
    target_part_id: str
    similarity_score: float
    key_sig_diffs: list[SignatureDiff]
    time_sig_diffs: list[SignatureDiff]
    measure_diffs: list[MeasureDiff]
    measures_missing: list[int]      # measure numbers
    measures_extra: list[int]

@dataclass
class MeasureDiff:
    """Comparison result for one matched pair of measures."""
    measure_number: int
    similarity_score: float
    voice_count_reference: int
    voice_count_target: int
    note_diffs: list[NoteDiff]

@dataclass
class NoteDiff:
    """Single note-level difference."""
    measure_number: int
    beat: float                      # beat position within measure
    voice: int
    operation: str                   # MATCH | PITCH_CHANGE | DURATION_CHANGE | ...
    reference: NoteInfo | None       # None for INSERTION
    target: NoteInfo | None          # None for DELETION
    interval_error: int | None       # semitones, for pitch differences

@dataclass
class NoteInfo:
    """Snapshot of a single note's properties."""
    pitch: str                       # e.g. "C#5", "rest"
    midi: int | None                 # MIDI number, None for rests
    duration: float                  # in quarter lengths
    duration_type: str               # "quarter", "eighth", etc.
    is_rest: bool
    is_chord: bool
    tie: str | None                  # "start" | "stop" | "continue" | None
    lyrics: str | None

@dataclass
class SignatureDiff:
    """Key or time signature that differs between reference and target."""
    measure_number: int
    reference_value: str             # e.g. "G major", "3/4"
    target_value: str | None         # None if missing
```

---

## 5. Similarity Score Calculation

The global `similarity_score` is a weighted aggregate:

```
similarity = w_structure × structure_score + w_notes × note_score

where:
  structure_score = matched_parts / max(parts_ref, parts_tgt)
                  × matched_measures / max(measures_ref, measures_tgt)

  note_score = (notes_identical + 0.5 × partial_matches) / total_notes_compared

  partial_matches = notes with only pitch OR only duration wrong

Default weights:
  w_structure = 0.3
  w_notes     = 0.7
```

This ensures that a file with the right structure but many wrong notes still
scores lower than a file that gets most notes right but is missing a measure.

---

## 6. Public API

```python
from comparer_mcp.engine import compare, compare_files

# From file paths
result: ComparisonResult = compare_files(
    reference="reference.musicxml",
    target="omr_output.musicxml",
)

# From MusicXML strings
result: ComparisonResult = compare(
    reference_xml="<score-partwise>...</score-partwise>",
    target_xml="<score-partwise>...</score-partwise>",
)

# Quick similarity check
score = result.similarity_score          # 0.0 – 1.0

# Summary
print(result.summary.notes_missing)      # 3
print(result.summary.parts_missing)      # ["Alto"]

# Iterate note-level diffs
for part_diff in result.part_diffs:
    for measure_diff in part_diff.measure_diffs:
        for note_diff in measure_diff.note_diffs:
            if note_diff.operation != "MATCH":
                print(f"m{note_diff.measure_number} beat {note_diff.beat}: "
                      f"{note_diff.operation} "
                      f"{note_diff.reference} → {note_diff.target}")

# Structured export
import json
print(json.dumps(result.to_dict(), indent=2))
```

---

## 7. Module Layout

```
comparer-mcp/
├── pyproject.toml
├── .python-version              # 3.11
├── README.md
├── SETUP.md
├── TROUBLESHOOTING.md
├── install.sh
├── .github/
│   └── copilot-instructions.md
├── src/
│   └── comparer_mcp/
│       ├── __init__.py
│       ├── server.py            # MCP tool definitions, dispatches to engine
│       ├── engine.py            # ScoreComparator — orchestrates the pipeline
│       │                        # (NO mcp imports — independently testable)
│       ├── part_matcher.py      # Part matching logic (name, instrument, range)
│       ├── measure_comparator.py # Measure-level structural comparison
│       ├── note_aligner.py      # Voice/note alignment using edit distance
│       ├── models.py            # Dataclasses: ComparisonResult, NoteDiff, etc.
│       └── utils.py             # Validation, pitch names, duration formatting
├── tests/
│   ├── __init__.py
│   ├── test_engine.py           # End-to-end comparison tests (unit)
│   ├── test_server.py           # Tool schemas, error propagation, list_capabilities
│   ├── test_part_matcher.py     # Part matching edge cases
│   ├── test_note_aligner.py     # Alignment algorithm tests
│   ├── test_utils.py
│   └── fixtures/
│       ├── simple_ref.musicxml
│       ├── simple_target.musicxml
│       ├── missing_part.musicxml
│       ├── transposed.musicxml
│       ├── version_a.musicxml   # Same piece, original arrangement
│       └── version_b.musicxml   # Same piece, modified arrangement
├── examples/
│   ├── claude_desktop_config.json
│   ├── continue_config.json
│   ├── cursor_mcp.json
│   ├── windsurf_mcp.json
│   └── zed_settings.json
└── docs/
    ├── HANDOVER.md
    ├── PLAN.md
    ├── requirements.md
    └── architecture.md          # (this document)
```

---

## 8. MCP Server — Tools

`comparer-mcp` is a full MCP server, deployed identically to the other servers
(stdio transport, `uv run comparer-mcp`). All tool handlers are `async def`.
All error responses use `{"error": "...", "error_code": "..."}` per conventions.

| Tool | Input | Output |
|------|-------|--------|
| `compare_musicxml` | `reference_xml` (string), `target_xml` (string), optional `options` | Full `ComparisonResult` JSON |
| `compare_musicxml_files` | `reference_path` (string), `target_path` (string), optional `options` | Full `ComparisonResult` JSON |
| `quick_similarity` | `reference_xml` (string), `target_xml` (string) | `{ "similarity_score": 0.87, "summary": {...} }` |
| `list_changes` | `reference_xml`, `target_xml`, optional `part` filter, optional `measure_range` | Filtered list of `NoteDiff` entries (for targeted queries) |
| `health_check` | — | `{ "status": "ok", "music21_version": "..."}` |
| `list_capabilities` | — | Server metadata per conventions |

### Options object

```json
{
  "expand_repeats": true,         // unfold repeats before comparing (default: true)
  "normalize_pitch": false,       // transpose to concert pitch (default: false)
  "ignore_articulations": false,  // skip articulation comparison (default: false)
  "part_filter": ["Soprano"],     // compare only named parts (default: all)
  "measure_range": [1, 32]        // compare only measures 1–32 (default: all)
}
```

### Engine reuse

`engine.py` contains all comparison logic with no MCP imports, so it can also be
imported directly by other servers or test scripts:

```python
from comparer_mcp.engine import compare, compare_files
result = compare_files("version_a.musicxml", "version_b.musicxml")
```

---

## 9. Dependencies

| Package | Purpose | License |
|---------|---------|---------|
| `mcp>=1.0.0` | MCP server framework | MIT |
| `music21` | MusicXML parsing, score object model, stream alignment | BSD-3 |
| `numpy` | Distance matrix in alignment (transitive via music21) | BSD-3 |

Dev dependencies: `pytest`, `pytest-asyncio` (per conventions).

---

## 10. Edge Cases & Design Decisions

| Edge case | Decision |
|-----------|----------|
| Different `<divisions>` values | music21 normalizes these on parse — no special handling needed |
| Enharmonic spelling (C# vs Db) | Compare by MIDI pitch number, flag spelling difference as informational |
| Pickup measures (anacrusis) | Match by measure number; measure 0 is pickup |
| Transposed scores | Compare as-written by default; option to normalize to concert pitch |
| Repeat signs expanded vs collapsed | Pre-process: use music21's `expandRepeats()` on both before comparing |
| Grace notes | Include in alignment with duration 0; flag as grace in `NoteInfo` |
| Chord notes | Hash all pitches sorted ascending; compare as sets |
| Missing voice numbers | Fall back to pitch-range matching between voices |
| Empty measures (multi-rest) | Treat as a single whole-rest; match structurally |
| Same piece, different arrangement | Works naturally — parts/voices added or removed show as missing/extra; note changes show as substitutions |
| Simplified vs full score | Part matcher handles unequal part counts; unmatched parts listed separately |
| Different editions / publishers | music21 normalizes formatting; comparison focuses on musical content not layout |

---

## 11. Implementation Phases

### Phase 1 — Core comparison (MVP)

- [ ] Parse two MusicXML files via music21
- [ ] Match parts by name
- [ ] Compare measure counts per part
- [ ] Align notes within matched measures (pitch + duration)
- [ ] Produce `ComparisonResult` with summary + similarity score
- [ ] Unit tests with simple SATB fixtures

### Phase 2 — Rich detail

- [ ] Key/time signature comparison
- [ ] Voice-aware alignment (multi-voice measures)
- [ ] Detailed `NoteDiff` with beat positions
- [ ] Articulation and tie comparison
- [ ] `to_dict()` / JSON export

### Phase 3 — MCP server & integration

- [ ] `server.py` with all 6 tools (compare, compare_files, quick_similarity, list_changes, health_check, list_capabilities)
- [ ] `test_server.py` — tool schemas, error propagation
- [ ] Integration tests with real MusicXML fixtures (`@pytest.mark.integration`)
- [ ] `install.sh`, `SETUP.md`, `TROUBLESHOOTING.md`, client config examples
- [ ] Integration with omr-mcp test suite (import engine directly)
- [ ] Batch comparison CLI for evaluating OMR across sample sets

### Phase 4 — Advanced features

- [ ] Visualization: side-by-side annotated score (via render-mcp)
- [ ] Version comparison report: human-readable summary ("Version B adds a descant in measures 17–24, transposes the tenor down a third in the coda")
- [ ] Diff export to MusicXML with colored annotations
