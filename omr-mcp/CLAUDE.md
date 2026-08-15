# omr-mcp — Claude Code Instructions

## What This Server Does

Converts sheet music images (PNG/JPEG) to MusicXML using the `oemer` deep-learning OCR engine.
Entry point of the choir pipeline — all other servers consume MusicXML produced here.

**Status:** Phases 1–4 code complete. 91 unit tests pass. Integration tests run against real oemer
for the first time (2026-08-15): fixing a 100%-blocking API bug plus pinning `onnxruntime` and
`opencv-python-headless` took the suite from 0/41 to 20/41 passing. **Output quality not yet
usable for SATB scores** — oemer reads multi-staff systems sequentially instead of simultaneously,
so a 4-voice choir score comes out as one part with the clef alternating back and forth instead of
4 parts sounding together; the harmonic structure is lost, confirmed by inspecting generated XML.
2/4 CPDL images also hit further oemer-internal crashes on this specific input data. See
`docs/HANDOVER.md` for the full writeup.

---

## Running Tests

```bash
# From this directory
VIRTUAL_ENV= .venv/bin/pytest tests/ -v                # 36 unit tests (fast)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration # invokes real oemer (~3–5 min/page)
```

Install dependencies: `uv sync`

---

## Key Files

| File | Purpose |
|------|---------|
| `src/omr_mcp/server.py` | MCP tool definitions and handlers |
| `src/omr_mcp/omr_engine.py` | oemer wrapper (no MCP imports) |
| `src/omr_mcp/utils.py` | Image validation, base64 helpers |
| `tests/test_omr.py` | Unit + integration tests |
| `test_samples/pdmx_satb_samples/` | 10 SATB PNG + MXL ground-truth fixtures |
| `docs/HANDOVER.md` | Status, remaining work, definition of done |
| `docs/PLAN.md` | Architecture decisions and rationale |
| `docs/requirements.md` | Functional/non-functional requirements |
| `docs/architecture.md` | Component diagram and data-flow |

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

## Hard Rules

- **Never `pip install`** — use `uv sync` or `uv add`
- **`omr_engine.py` must not import from `mcp`** — keeps it unit-testable
- **All tool handlers must be `async def`**
- **All errors** → `{"error": "...", "error_code": "..."}` (codes: `FILE_NOT_FOUND`, `UNSUPPORTED_FORMAT`, `FILE_TOO_LARGE`, `INVALID_INPUT`, `PROCESSING_FAILED`, `INVALID_PARAMETER`)
- **Integration tests** must be `@pytest.mark.integration` and skipped in the default run

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

---

## Known Gotchas

- **oemer downloads ~100 MB on first run** and takes ~10 min. Subsequent runs use cache.
- **oemer output varies slightly between runs** — never assert byte-identical XML; parse and
  compare structure instead.
- **MusicXML from oemer may not validate against strict schema** — check for parseable content
  and presence of parts/measures.
- **The full PDMX dataset (14 GB) lives in `test_samples/pdmx_full/`** — never load or iterate
  it in tests; use `pdmx_satb_samples/` only.
- **`.python-version` (`llm311`) is a pyenv-virtualenv name `uv` doesn't understand** — `uv sync`
  silently falls back to whatever `python3` is on `PATH` instead of erroring. Always check
  `.venv/bin/python --version` after `uv venv`/`uv sync`; use `uv venv --python 3.11` if it's wrong.
- **`omr_engine.py` forces `CUDA_VISIBLE_DEVICES=""` at import time.** On this dev host,
  onnxruntime's CUDA execution provider hard-aborts the process instead of raising a catchable
  Python exception. Real GPU inference would need a matched onnxruntime-gpu/CUDA driver pair.
- **`onnxruntime` and `opencv-python-headless` are pinned** in `pyproject.toml`, and
  `onnxruntime-gpu` is excluded via `[tool.uv] override-dependencies` — oemer's own packaging
  leaves both unpinned, and their latest releases each broke oemer's bundled ONNX models in
  different ways (ConvTranspose shape validation; `cv2.HoughLinesP` return-shape change). Full
  details in `docs/HANDOVER.md`.

---

## Claude Desktop Config

```json
{
  "mcpServers": {
    "omr": {
      "command": "uv",
      "args": ["--directory", "/path/to/omr-mcp", "run", "omr-mcp"]
    }
  }
}
```

---

## Document Update Policy

When you finish work or reach a milestone, update:
1. `docs/HANDOVER.md` — check off done items, add new gotchas
2. `docs/PLAN.md` — check off phase items, note changed decisions
3. `docs/requirements.md` — update if behaviour changed
4. `docs/architecture.md` — update if implementation changed
