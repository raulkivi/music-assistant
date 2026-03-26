# comparer-mcp — Requirements

## Functional requirements

### FR-1: Full comparison

Compare two MusicXML inputs (string or file path) and return a structured `ComparisonResult` containing:
- Global similarity score (0.0–1.0)
- Summary statistics (parts matched/missing, notes identical/changed/missing)
- Per-part diffs with per-measure and per-note detail

### FR-2: Part matching

Match parts between two scores using a priority cascade:
1. Exact part name (case-insensitive)
2. MIDI program / instrument
3. Positional order
4. Pitch range heuristic

Report unmatched parts as missing (in reference only) or extra (in target only).

### FR-3: Note-level alignment

Within matched measures, align note sequences using edit-distance. Classify each difference as:
`MATCH`, `PITCH_CHANGE`, `DURATION_CHANGE`, `SUBSTITUTION`, `INSERTION`, `DELETION`.

### FR-4: Similarity scoring

Weighted aggregate: 30% structure (parts + measures matched) + 70% note accuracy.

### FR-5: Filtering

Support filtering comparison by:
- Part name(s)
- Measure range
- Options: expand repeats, normalize pitch, ignore articulations

### FR-6: Quick similarity

Return only the similarity score and summary statistics (no note-level detail) for fast queries.

### FR-7: MCP tools

Expose as MCP server with tools: `compare_musicxml`, `compare_musicxml_files`, `quick_similarity`, `list_changes`, `health_check`, `list_capabilities`.

---

## Non-functional requirements

### NFR-1: No MCP dependency in engine

`engine.py` must not import from `mcp` — keeps comparison logic independently testable and reusable by other servers.

### NFR-2: Error format

All tool errors return `{"error": "human description", "error_code": "SCREAMING_SNAKE"}`.

Standard error codes: `FILE_NOT_FOUND`, `INVALID_INPUT`, `UNSUPPORTED_FORMAT`, `PROCESSING_FAILED`, `INVALID_PARAMETER`.

### NFR-3: Performance

- Simple SATB comparison (4 parts, 30 measures): < 5 seconds
- Large orchestral score: best-effort, no hard timeout

### NFR-4: Test coverage

- Unit tests for all modules (target: 30+ for Phase 1)
- Integration tests marked `@pytest.mark.integration`
- Integration tests must not run in default `pytest` invocation

---

## Interfaces

### Input formats

- MusicXML string (`<score-partwise>` or `<score-timewise>`)
- MusicXML file path (`.musicxml`, `.xml`, `.mxl`)

### Output format

JSON-serializable `ComparisonResult` — see `docs/architecture.md` §4 for full data model.
