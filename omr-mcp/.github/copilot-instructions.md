# omr-mcp — Copilot Instructions

## What This Server Does

Converts sheet music images (PNG/JPEG) to MusicXML using the `oemer` deep-learning OCR engine.
This is the entry point of the choir music pipeline — all other servers consume MusicXML produced here.

**Status:** Phases 1–4 substantially complete. 36 unit tests pass.
Integration tests written but not yet verified against real oemer.

---

## Before You Write Any Code

Read these documents in order:
1. **`docs/HANDOVER.md`** — current status, remaining work, pre-flight checks, known gotchas, definition of done
2. **`docs/PLAN.md`** — architecture decisions and technology rationale
3. **`docs/requirements.md`** — functional and non-functional requirements, error codes
4. **`docs/architecture.md`** — component diagram, data-flow, module responsibilities

---

## Project Structure

```
omr-mcp/
├── pyproject.toml
├── .python-version          # "llm311"
├── src/omr_mcp/
│   ├── server.py            # MCP tool definitions and async handlers
│   ├── omr_engine.py        # oemer wrapper — NO mcp imports
│   └── utils.py             # image validation, base64 helpers
├── tests/
│   ├── test_omr.py          # unit + integration tests
│   └── fixtures/
├── test_samples/
│   └── pdmx_satb_samples/   # 10 SATB PNG + MXL fixtures — use these in tests
│       ├── png/
│       └── mxl/
└── docs/
    ├── requirements.md
    └── architecture.md
```

---

## Implemented Tools

| Tool | Input | Output |
|------|-------|--------|
| `recognize_sheet` | Image path or base64 | MusicXML string + metadata |
| `recognize_sheet_to_file` | Image path | MusicXML file path + metadata |
| `recognize_sheets` | List of image paths/base64 | Single merged MusicXML (multi-page) |
| `list_capabilities` | — | Server capabilities |
| `list_supported_formats` | — | Deprecated alias for `list_capabilities` |

---

## Coding Standards

- **Package manager:** `uv` only — never `pip install`
- **`omr_engine.py` must not import from `mcp`** — keeps it independently unit-testable
- **All tool handlers must be `async def`**
- **All error responses:** `{"error": "human description", "error_code": "SCREAMING_SNAKE"}`
- **Standard error codes:** `FILE_NOT_FOUND`, `UNSUPPORTED_FORMAT`, `FILE_TOO_LARGE`, `INVALID_INPUT`, `PROCESSING_FAILED`, `INVALID_PARAMETER`
- **Integration tests** must be `@pytest.mark.integration` — not run in the default `pytest` invocation
- **Python 3.11+**; `asyncio_mode = "auto"` in pytest config

---

## Running Tests

```bash
# Unit tests (fast, default)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

# Integration tests (invokes real oemer — slow, first run downloads ~100 MB)
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

---

## Known Gotchas

- **oemer downloads ~100 MB on first run** — expect ~10 min. Uses cache after that.
- **oemer output varies slightly between runs** — compare structure, not byte-identical XML.
- **MusicXML from oemer may not pass strict schema validation** — test for parseable content with
  parts and measures present.
- **Never load or iterate `test_samples/pdmx_full/`** (14 GB dataset) in tests — use
  `pdmx_satb_samples/` only.

---

## When You Finish Work

Update these documents so the next session starts with accurate information:
- **`docs/HANDOVER.md`** — check off done items, add new gotchas, update status
- **`docs/PLAN.md`** — check off completed phase items, note changed decisions
- **`docs/requirements.md`** — update if behaviour or interfaces changed
- **`docs/architecture.md`** — update if implementation structure changed
