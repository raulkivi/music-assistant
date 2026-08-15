# comparer-mcp — Copilot Instructions

## What This Server Does

Music-aware comparison of two MusicXML files. Provides structured, multi-level diffs
from global similarity score down to individual note differences. Primary use cases:
version/arrangement comparison, OMR quality evaluation, round-trip fidelity testing.

**Status:** Phase 1 (core comparison MVP) complete. 45/45 tests pass (43 unit + 2 integration).
`server.py` (Phase 3, MCP tools) not yet built.

---

## Before You Write Any Code

Read these documents in order:
1. **`docs/HANDOVER.md`** — current status, remaining work, definition of done
2. **`docs/PLAN.md`** — implementation plan and technology decisions
3. **`docs/requirements.md`** — functional and non-functional requirements
4. **`docs/architecture.md`** — full vision, 5-layer comparison pipeline, data model, similarity scoring

---

## Project Structure

```
comparer-mcp/
├── pyproject.toml
├── .python-version          # 3.11
├── src/comparer_mcp/
│   ├── server.py            # MCP tool definitions, dispatches to engine
│   ├── engine.py            # Comparison orchestration — NO mcp imports
│   ├── models.py            # Dataclasses: ComparisonResult, NoteDiff, etc.
│   ├── part_matcher.py      # Part matching (name, instrument, range)
│   ├── measure_comparator.py # Measure-level structural comparison
│   ├── note_aligner.py      # Edit-distance note alignment
│   └── utils.py             # Validation, pitch names, duration formatting
├── tests/
│   ├── test_engine.py       # End-to-end comparison tests
│   ├── test_server.py       # Tool schemas, error propagation
│   ├── test_part_matcher.py # Part matching edge cases
│   ├── test_note_aligner.py # Alignment algorithm tests
│   ├── test_utils.py
│   └── fixtures/            # MusicXML test files
└── docs/
    ├── HANDOVER.md
    ├── PLAN.md
    ├── requirements.md
    └── architecture.md
```

---

## Planned Tools

| Tool | Description |
|------|-------------|
| `compare_musicxml` | Full diff of two MusicXML strings → structured `ComparisonResult` JSON |
| `compare_musicxml_files` | Full diff of two MusicXML file paths → structured `ComparisonResult` JSON |
| `quick_similarity` | Similarity score (0.0–1.0) + summary statistics |
| `list_changes` | Filtered note-level diffs (by part, measure range) |
| `health_check` | Server status and music21 version |
| `list_capabilities` | Server metadata per conventions |

---

## Coding Standards

- **Package manager:** `uv` only — never `pip install`
- **`engine.py` must not import from `mcp`** — keeps it independently unit-testable
- **All tool handlers must be `async def`**
- **All error responses:** `{"error": "human description", "error_code": "SCREAMING_SNAKE"}`
- **Standard error codes:** `FILE_NOT_FOUND`, `INVALID_INPUT`, `UNSUPPORTED_FORMAT`, `PROCESSING_FAILED`, `INVALID_PARAMETER`
- **Integration tests** → `@pytest.mark.integration`
- **Python 3.11+**; `asyncio_mode = "auto"` in pytest config

---

## Running Tests

```bash
# Unit tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

# Integration tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration

# Install dependencies
uv sync
```

---

## MCP Server Startup Pattern

```python
import asyncio
import mcp.server.stdio

async def _run():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

asyncio.run(_run())
```

`mcp.server.stdio.run_server()` does not exist — always use the context manager above.
