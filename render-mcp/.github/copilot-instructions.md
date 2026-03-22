# render-mcp — Copilot Instructions

## What This Server Does

Renders MusicXML scores to PDF (for printing) or PNG (for display in web/mobile apps).
Backend: Verovio (in-process Python) + cairosvg + pypdf. No MuseScore CLI required.

**Status:** Phase 1 complete. 68/68 tests pass including integration tests.

---

## Before You Write Any Code

Read these documents in order:
1. **`HANDOVER.md`** — current status, remaining work, pre-flight checks, known gotchas, definition of done
2. **`PLAN.md`** — architecture decisions and technology rationale
3. **`docs/requirements.md`** — functional and non-functional requirements, error codes
4. **`docs/architecture.md`** — component diagram, data-flow, module responsibilities

---

## Project Structure

```
render-mcp/
├── pyproject.toml
├── .python-version          # "llm311"
├── src/render_mcp/
│   ├── server.py            # MCP tool definitions and async handlers
│   ├── engine.py            # Verovio + cairosvg rendering — NO mcp imports
│   └── utils.py             # MusicXML validation, path helpers
├── tests/
│   ├── test_server.py       # protocol tests
│   ├── test_engine.py       # unit + integration tests
│   ├── test_utils.py        # unit tests
│   └── fixtures/
└── docs/
    ├── requirements.md
    └── architecture.md
```

MXL test fixtures are in `../omr-mcp/test_samples/pdmx_satb_samples/mxl/` — 10 SATB files.

---

## Implemented Tools

| Tool | Description |
|------|-------------|
| `render_to_pdf` | MusicXML → multi-page PDF at caller-specified or auto-generated path |
| `render_to_image` | MusicXML → PNG or SVG, single page, configurable DPI (72–600) |
| `list_capabilities` | Server metadata, active backend, format support |

---

## Environment

- **Backend:** Verovio (MusicXML → SVG, pure Python) + cairosvg (SVG → PNG/PDF) + pypdf (merge)
- **System dep:** `libcairo.so.2` — installed system-wide on Ubuntu; no sudo needed
- **No MuseScore CLI** — do not check for or call `mscore4`/`musescore4`
- Integration tests run in-process (Verovio requires no external tools) — no special setup needed

---

## Coding Standards

- **Package manager:** `uv` only — never `pip install`
- **`engine.py` must not import from `mcp`** — keeps it independently unit-testable
- **All tool handlers must be `async def`**
- **All error responses:** `{"error": "human description", "error_code": "SCREAMING_SNAKE"}`
- **Standard error codes:** `INVALID_INPUT`, `PROCESSING_FAILED`, `INVALID_PARAMETER`, `FILE_NOT_FOUND`
- **Integration tests** must be `@pytest.mark.integration` — not run in the default `pytest` invocation
- **Python 3.11+**; `asyncio_mode = "auto"` in pytest config

---

## Running Tests

```bash
# All tests including integration (Verovio is in-process, no external deps)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

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

---

## Known Gotchas

- **cairosvg DPI with Verovio SVGs.** Verovio emits SVGs with fixed pixel dimensions — the `dpi`
  kwarg in `cairosvg.svg2png(dpi=...)` has no effect. Use `scale=dpi/96.0` instead.
- **Multi-page PDF pipeline:** each SVG page → single-page PDF via cairosvg → merge with pypdf.
  Single-page scores skip the merge step.
- **MuseScore is not installed.** Don't attempt to call any MuseScore CLI command.

---

## When You Finish Work

Update these documents so the next session starts with accurate information:
- **`HANDOVER.md`** — check off done items, add new gotchas, update status
- **`PLAN.md`** — check off completed phase items, note changed decisions
- **`docs/requirements.md`** — update if behaviour or interfaces changed
- **`docs/architecture.md`** — update if implementation structure changed
