# Copilot Instructions

## Project Overview

Choir Music Assistant — a collection of independent MCP (Model Context Protocol) servers that
together enable choir singers to digitize, practice with, and navigate sheet music.

See [docs/Intro.md](../docs/Intro.md) for goals, phases, and data flow.
See [docs/conventions.md](../docs/conventions.md) for coding standards all servers must follow.
See [docs/implementation-plan.md](../docs/implementation-plan.md) for the high-level build order.

---

## Working on an MCP Server

### Before you write any code

**Always read these two files for the server you are working on, in this order:**

1. **`<name>-mcp/HANDOVER.md`** — start here. Current status, what to build first, pre-flight
   checks, known gotchas, and the definition of done. Written specifically for someone picking up
   that server for the first time.

2. **`<name>-mcp/PLAN.md`** — architecture decisions, technology rationale, tool contracts, full
   phase breakdown, and risks. The reference document for why things are designed as they are.

3. **`docs/conventions.md`** — once, if you haven't already. Defines the project structure,
   required tools, error format, testing requirements, and naming rules that all servers must follow.

> Do not start implementing until you have run the pre-flight verification steps in HANDOVER.md.
> They exist to catch environment issues before they waste your time mid-implementation.

### When you finish work (or reach a milestone)

Update the documents so the next person (or session) starts with accurate information:

**In `<name>-mcp/HANDOVER.md`:**
- Check off completed items in the "Definition of Done" checklist
- Add any gotchas you discovered that weren't already documented
- Update the status table at the top to reflect current phase completion
- Remove or mark as resolved any pre-flight steps that are now always satisfied

**In `<name>-mcp/PLAN.md`:**
- Check off completed items in the Implementation Phases checklists (`- [x]`)
- Update the "Remaining Work" section (for omr-mcp) or phase status
- Note any technology decisions that changed from the original plan, with rationale

**In this file (`copilot-instructions.md`):**
- Update the server's status marker (❌ / ⚠️ / ✅) in the Repository Structure tree
- Update the server's tool list and backend in the MCP Servers Reference section if they changed

---

## Repository Structure

```
choir-music-assistant/
├── docs/
│   ├── Intro.md                # Vision, goals, phases, data flow
│   ├── conventions.md          # Shared conventions for all MCP servers
│   ├── implementation-plan.md  # High-level build order and server summaries
│   └── sources.md              # Reference links (ABC notation, etc.)
├── omr-mcp/                    # Image → MusicXML          ✅ mostly complete
│   ├── HANDOVER.md             # ← read first when working on this server
│   └── PLAN.md                 # ← architecture and decisions
├── synth-mcp/                  # MusicXML → Audio          ⚠️ Phase 1 complete, WAV integration test pending
│   ├── HANDOVER.md             # ← read first when working on this server
│   └── PLAN.md                 # ← architecture and decisions
├── render-mcp/                 # MusicXML → PDF/PNG        ❌ not started
│   ├── HANDOVER.md             # ← read first when working on this server
│   └── PLAN.md                 # ← architecture and decisions
├── musicxml-abc-mcp/           # MusicXML ↔ ABC            ❌ not started
│   ├── HANDOVER.md             # ← read first when working on this server
│   └── PLAN.md                 # ← architecture and decisions
└── pitch-mcp/                  # Mic audio → score pos/accuracy  ❌ not started
    ├── HANDOVER.md             # ← read first when working on this server
    └── PLAN.md                 # ← architecture and decisions
```

Each `*-mcp/` directory is a self-contained Python package deployable independently.

---

## Environment Setup

### Requirements

- **Python**: 3.11 or higher (each server pins its version in `.python-version`)
- **Package manager**: [uv](https://github.com/astral-sh/uv) — always prefer over pip
- **Environment manager**: pyenv (`.python-version` files use pyenv version names)

### Per-server setup

```bash
cd <name>-mcp

# Install all dependencies (including dev)
uv sync

# Run unit tests
uv run pytest tests/ -v

# Run integration tests (slower, require real backends)
uv run pytest tests/ -v -m integration

# Start the MCP server
uv run <name>-mcp
```

---

## MCP Servers Reference

Keep this section up to date as servers are implemented. When a server's tools, backend, or
status changes, update the relevant entry here.

---

### omr-mcp ✅ mostly complete

**Purpose:** Optical Music Recognition — converts sheet music images to MusicXML.

**Read before working:** [omr-mcp/HANDOVER.md](../omr-mcp/HANDOVER.md) · [omr-mcp/PLAN.md](../omr-mcp/PLAN.md)

**Implemented tools:**
- `recognize_sheet` — image path or base64 → MusicXML string
- `recognize_sheet_to_file` — image path → saves MusicXML, returns path
- `recognize_sheets` — ordered list of image paths/base64 → single merged MusicXML (multi-page)
- `list_capabilities` — returns server capabilities per conventions.md
- `list_supported_formats` — deprecated alias for `list_capabilities`

**Backend:** [oemer](https://github.com/BreezeWhite/oemer) (deep learning, ONNX Runtime, CPU-friendly)

**Remaining work:** run integration tests against real oemer to verify end-to-end — see HANDOVER.md

**Key files:**
- `src/omr_mcp/server.py` — MCP tool definitions
- `src/omr_mcp/omr_engine.py` — oemer wrapper
- `src/omr_mcp/utils.py` — image validation and base64 helpers
- `test_samples/pdmx_satb_samples/` — 10 SATB a cappella pieces (PNG + ground-truth MXL)

---

### synth-mcp ⚠️ Phase 1 complete — WAV integration test pending

**Purpose:** Synthesizes audio from MusicXML with selectable voice parts and tempo control.

**Read before working:** [synth-mcp/HANDOVER.md](../synth-mcp/HANDOVER.md) · [synth-mcp/PLAN.md](../synth-mcp/PLAN.md)

**Implemented tools:** `get_parts`, `synthesize`, `list_capabilities`

**Backend:** music21 (MusicXML → MIDI) + FluidSynth CLI (MIDI → WAV)

**System dependency:** FluidSynth (`apt install fluidsynth libfluidsynth-dev` / `brew install fluid-synth`)
and an SF2 soundfont (path via `SYNTH_SOUNDFONT_PATH` env var)

**Key files:**
- `src/synth_mcp/server.py` — MCP tool definitions
- `src/synth_mcp/engine.py` — music21 + FluidSynth synthesis pipeline
- `src/synth_mcp/utils.py` — MusicXML validation, tempo validation, path helpers

**Remaining work:** run end-to-end WAV integration test once FluidSynth + soundfont are available

**Gotcha:** music21 9.x sets `part.id` to the part name (e.g. "Soprano"), not the XML `id`
attribute (e.g. "P1"). Callers must use part names when specifying `part_ids`.

---

### render-mcp ❌ not started

**Purpose:** Renders MusicXML to PDF or PNG for printing and display.

**Read before working:** [render-mcp/HANDOVER.md](../render-mcp/HANDOVER.md) · [render-mcp/PLAN.md](../render-mcp/PLAN.md)

**Planned tools:** `render_to_pdf`, `render_to_image`, `list_capabilities`

**Planned backend:** MuseScore 4 CLI (primary), Verovio (fallback, pure Python)

**System dependency:** MuseScore 4 for primary backend (optional — Verovio works without it)

---

### musicxml-abc-mcp ❌ not started

**Purpose:** Converts between MusicXML and ABC notation so Claude can read and edit scores.

**Read before working:** [musicxml-abc-mcp/HANDOVER.md](../musicxml-abc-mcp/HANDOVER.md) · [musicxml-abc-mcp/PLAN.md](../musicxml-abc-mcp/PLAN.md)

**Planned tools:** `musicxml_to_abc`, `abc_to_musicxml`, `validate_abc`, `list_capabilities`

**Planned backend:** music21 (handles both formats natively)

**Note:** No system dependencies — pure Python. Simplest server to implement.

---

### pitch-mcp ❌ not started

**Purpose:** Real-time pitch detection from microphone, compared against a reference score, to
show current position and pitch accuracy while singing.

**Read before working:** [pitch-mcp/HANDOVER.md](../pitch-mcp/HANDOVER.md) · [pitch-mcp/PLAN.md](../pitch-mcp/PLAN.md)

**Planned tools:** `analyze_recording` (Phase A), `load_score`, `start_monitoring`,
`get_current_position`, `stop_monitoring`, `list_capabilities` (Phase B)

**Planned backends:** crepe (pitch detection, requires TensorFlow), sounddevice (audio input),
dtaidistance (DTW score alignment)

**System dependency:** PortAudio (`apt install libportaudio2` / `brew install portaudio`)

**Build strategy:** Implement offline `analyze_recording` first. Add real-time tools only after
offline analysis is verified. See HANDOVER.md for details.

**Note:** Most complex server — build last.

---

## Notes for AI Assistants

- **Always read HANDOVER.md first** for the server you are working on — it tells you what is done,
  what to do next, and what will trip you up.
- **Update HANDOVER.md and PLAN.md** when you complete work or reach a milestone.
- Always use `uv` — never `pip install` directly.
- Each MCP server has its own `uv` venv — never share environments between servers.
- The `engine.py` in each server must not import from the `mcp` SDK (keeps it unit-testable).
- All tool handlers must be `async def`.
- All error responses must use the standard format: `{"error": "...", "error_code": "..."}`.
- Integration tests must be marked `@pytest.mark.integration` and must not run in the default
  `pytest` invocation.
- See [docs/conventions.md](../docs/conventions.md) for the full error code list, required tools,
  testing requirements, and project structure template.
