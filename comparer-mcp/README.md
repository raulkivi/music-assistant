# comparer-mcp

MCP server for music-aware comparison of MusicXML files. Provides structured, multi-level diffs that report what changed between two scores — from global similarity down to individual notes.

## What it does

- **Version / arrangement comparison** — Compare different editions, arrangements, or simplifications of the same piece
- **OMR quality evaluation** — Compare `omr-mcp` output against a known-good reference
- **Round-trip fidelity** — Verify MusicXML → ABC → MusicXML through `musicxml-abc-mcp`
- **Regression testing** — Detect regressions when OMR models or conversion logic change
- **Score editing validation** — Confirm LLM-driven edits only changed intended elements

## Tools

| Tool | Description |
|------|-------------|
| `compare_musicxml` | Full diff of two MusicXML strings → structured `ComparisonResult` JSON |
| `compare_musicxml_files` | Full diff of two MusicXML file paths → structured `ComparisonResult` JSON |
| `quick_similarity` | Similarity score (0.0–1.0) + summary statistics |
| `list_changes` | Filtered note-level diffs (by part name, measure range) |
| `health_check` | Server status and music21 version |
| `list_capabilities` | Server metadata per conventions |

## Installation

```bash
cd comparer-mcp
uv sync
```

## Running

```bash
uv run comparer-mcp
```

## Configuration

No environment variables required. All configuration is passed via the `options` parameter on comparison tools.

### Options object

```json
{
  "expand_repeats": true,
  "normalize_pitch": false,
  "ignore_articulations": false,
  "part_filter": ["Soprano"],
  "measure_range": [1, 32]
}
```

## Usage examples

```json
// Compare two MusicXML strings
{
  "tool": "compare_musicxml",
  "arguments": {
    "reference_xml": "<score-partwise>...</score-partwise>",
    "target_xml": "<score-partwise>...</score-partwise>"
  }
}

// Compare two files
{
  "tool": "compare_musicxml_files",
  "arguments": {
    "reference_path": "/path/to/reference.musicxml",
    "target_path": "/path/to/omr_output.musicxml"
  }
}

// Quick similarity check
{
  "tool": "quick_similarity",
  "arguments": {
    "reference_xml": "<score-partwise>...</score-partwise>",
    "target_xml": "<score-partwise>...</score-partwise>"
  }
}
// → {"similarity_score": 0.87, "summary": {...}}

// Filtered changes (e.g. "what changed in the Alto, measures 17–24?")
{
  "tool": "list_changes",
  "arguments": {
    "reference_xml": "<score-partwise>...</score-partwise>",
    "target_xml": "<score-partwise>...</score-partwise>",
    "part": "Alto",
    "measure_range": [17, 24]
  }
}
```

## Testing

```bash
# Unit tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

# Integration tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration

# Install dependencies
uv sync
```

## Dependencies

- [music21](https://web.mit.edu/music21/) — MusicXML parsing, score object model, stream alignment
- [numpy](https://numpy.org/) — distance matrix for note alignment (transitive via music21)
- [mcp](https://github.com/modelcontextprotocol/python-sdk) — MCP protocol

## System requirements

- Python 3.11+
- No system libraries required

## Phase status

| Phase | Status |
|-------|--------|
| Phase 1 — Core comparison (MVP) | Not started |
| Phase 2 — Rich detail | Not started |
| Phase 3 — MCP server & integration | Not started |
| Phase 4 — Advanced features | Not started |
