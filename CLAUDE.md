# CLAUDE.md — Choir Music Assistant

Project-level instructions for Claude Code. Read this before doing any work in this repository.

---

## What this project is

Five independent MCP servers for choir practice. Each server lives in its own directory, has its own Python venv, and can be deployed standalone.

| Server | Directory | Input → Output | Goal |
|--------|-----------|----------------|------|
| omr-mcp | `omr-mcp/` | Sheet music image → MusicXML | Digitize scores |
| render-mcp | `render-mcp/` | MusicXML → PDF / PNG | Print / display |
| synth-mcp | `synth-mcp/` | MusicXML + voice → WAV | Practice audio |
| musicxml-abc-mcp | `musicxml-abc-mcp/` | MusicXML ↔ ABC | LLM editing bridge |
| pitch-mcp | `pitch-mcp/` | Mic audio + score → position + accuracy | Sing-along feedback |

See [docs/Intro.md](docs/Intro.md) for the full vision and data flow.

---

## Documentation map

Each MCP server has four documents:

| File | Purpose |
|------|---------|
| `README.md` | User-facing: install, run, tools, examples |
| `HANDOVER.md` | Developer onboarding: status, gotchas, definition of done |
| `PLAN.md` | Architecture decisions and phase breakdown |
| `docs/requirements.md` | Functional/non-functional requirements and interface contracts |
| `docs/architecture.md` | Component diagram, data-flow traces, key algorithms |

**Before touching any server, read its HANDOVER.md, then docs/architecture.md.**

---

## Running tests

From inside each `*-mcp/` directory:

```bash
# Unit tests (fast, no external dependencies)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

# Integration tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration

# synth-mcp integration (needs soundfont)
VIRTUAL_ENV= SYNTH_SOUNDFONT_PATH=/usr/share/sounds/sf2/TimGM6mb.sf2 \
  .venv/bin/pytest tests/ -v -m integration

# pitch-mcp manual tests (real microphone, skip in CI)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m manual
```

Install dev dependencies: `uv sync` (or `uv sync --extra dev` for musicxml-abc-mcp).

---

## Server status

| Server | Status | Tests |
|--------|--------|-------|
| omr-mcp | ✅ mostly complete (integration tests pending) | 36 unit |
| synth-mcp | ✅ Phase 1 complete | 60 unit + 7 integration |
| render-mcp | ✅ Phase 1 complete | 68/68 incl. integration |
| musicxml-abc-mcp | ✅ Phase 1 complete | 71/71 incl. integration |
| pitch-mcp | ✅ Phase A+B complete | 93/93 |

---

## Hard rules

- **Never use `pip install`** — always `uv sync` or `uv add`
- **Never share venvs** between servers; each has its own `.venv`
- **`engine.py` must not import from `mcp`** — keeps it unit-testable without the MCP stack
- **All tool handlers must be `async def`**
- **All error responses** must use `{"error": "...", "error_code": "..."}` — see [docs/conventions.md](docs/conventions.md) for the full code list
- **Integration tests** must be marked `@pytest.mark.integration` and must not run in the default `pytest` invocation

---

## MCP stdio pattern

Use `mcp.server.stdio.stdio_server()` — `run_server()` does not exist in the current SDK:

```python
async def _run():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

asyncio.run(_run())
```

---

## Known gotchas (non-obvious, apply across sessions)

| Server | Gotcha |
|--------|--------|
| synth-mcp | music21 9.x: `part.id` is the part *name* (e.g. "Soprano"), not the XML `<part id>` attribute ("P1") |
| synth-mcp | FluidSynth: use `audio.driver=file` + `fluid_player_join()` — no subprocess, no CLI |
| synth-mcp | Synthesis tests skip automatically when `SYNTH_SOUNDFONT_PATH` is unset |
| render-mcp | Verovio SVGs have fixed pixel dims — use `scale=dpi/96.0` with cairosvg, not `dpi=` |
| render-mcp | MuseScore CLI is not installed; Verovio is the active backend |
| musicxml-abc-mcp | music21 9.x has no ABC write support — custom serializer in `engine.py` handles it |
| musicxml-abc-mcp | ABC v2.1: lowercase `c` = C4 (middle C); uppercase `C` = C3 |
| musicxml-abc-mcp | Use `uv sync --extra dev` (not `--group dev`) to install pytest |
| pitch-mcp | `crepe` fails to build under uv (missing `pkg_resources`) — keep as manual opt-in only |
| pitch-mcp | `aubio` has no Python 3.13 wheel — use librosa instead |
| pitch-mcp | sounddevice streams fail at runtime if `libportaudio2` is absent |
| pitch-mcp | Audio callback must never do I/O or locking — queue chunks only |
| omr-mcp | oemer downloads ~100 MB of model checkpoints on first run (~10 min) |
| omr-mcp | oemer output varies slightly between runs — do not assert byte-identical XML |

---

## System libraries (already installed on this machine)

| Library | Path | Used by |
|---------|------|---------|
| `libfluidsynth.so.3` | `/usr/lib/x86_64-linux-gnu/` | synth-mcp |
| `libcairo.so.2` | system-wide | render-mcp |
| `libportaudio2` | system-wide | pitch-mcp (real-time) |

Soundfonts available at `/usr/share/sounds/sf2/` — `TimGM6mb.sf2` and `default-GM.sf2`.

---

## Document update policy

When you finish work or reach a milestone, update:

1. `<server>/HANDOVER.md` — check off done items, add new gotchas
2. `<server>/PLAN.md` — check off phase items, note any changed decisions
3. `<server>/docs/requirements.md` — update if behaviour or interfaces changed
4. `<server>/docs/architecture.md` — update diagrams/algorithms if implementation changed
5. `.github/copilot-instructions.md` — update status markers and tool lists
6. This file (`CLAUDE.md`) — update status table and gotchas if needed
