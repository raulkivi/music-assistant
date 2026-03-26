# comparer-mcp — Claude Code Instructions

## What This Server Does

Music-aware comparison of two MusicXML files. Provides structured, multi-level diffs
from global similarity score down to individual note differences. Primary use cases:
version/arrangement comparison, OMR quality evaluation, round-trip fidelity testing.

**Status:** Pre-implementation (design complete, no source code yet).

---

## Running Tests

```bash
# From this directory
VIRTUAL_ENV= .venv/bin/pytest tests/ -v              # unit tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration  # integration tests
```

Install dependencies: `uv sync`

---

## Key Files

| File | Purpose |
|------|---------|
| `src/comparer_mcp/server.py` | MCP tool definitions and handlers |
| `src/comparer_mcp/engine.py` | Comparison orchestration (no MCP imports) |
| `src/comparer_mcp/models.py` | Dataclasses: ComparisonResult, NoteDiff, etc. |
| `src/comparer_mcp/part_matcher.py` | Part matching logic (name, instrument, range) |
| `src/comparer_mcp/note_aligner.py` | Edit-distance note alignment |
| `src/comparer_mcp/measure_comparator.py` | Measure-level structural comparison |
| `src/comparer_mcp/utils.py` | Validation, pitch names, duration formatting |
| `docs/HANDOVER.md` | Status, remaining work, definition of done |
| `docs/PLAN.md` | Implementation plan and technology decisions |
| `docs/requirements.md` | Functional/non-functional requirements |
| `docs/architecture.md` | Full vision, pipeline design, data model |

---

## Planned Tools

| Tool | Description |
|------|-------------|
| `compare_musicxml` | Full diff of two MusicXML strings |
| `compare_musicxml_files` | Full diff of two MusicXML file paths |
| `quick_similarity` | Similarity score (0.0–1.0) + summary |
| `list_changes` | Filtered note-level diffs |
| `health_check` | Server status and music21 version |
| `list_capabilities` | Server metadata per conventions |

---

## Environment

- **Core library:** `music21` — MusicXML parsing, score model, stream alignment
- **No system dependencies** required
- **music21 import is slow** (~2s first time) — this is expected

---

## Hard Rules

- **Never `pip install`** — use `uv sync` or `uv add`
- **`engine.py` must not import from `mcp`** — keeps it unit-testable
- **All tool handlers must be `async def`**
- **All errors** → `{"error": "...", "error_code": "..."}` (codes: `FILE_NOT_FOUND`, `INVALID_INPUT`, `UNSUPPORTED_FORMAT`, `PROCESSING_FAILED`, `INVALID_PARAMETER`)
- **Integration tests** must be `@pytest.mark.integration`

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

`run_server()` does not exist in the installed MCP SDK — use the context manager above.
