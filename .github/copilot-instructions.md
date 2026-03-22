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

**Always read these files for the server you are working on, in this order:**

1. **`<name>-mcp/HANDOVER.md`** — start here. Current status, what to build first, pre-flight
   checks, known gotchas, and the definition of done. Written specifically for someone picking up
   that server for the first time.

2. **`<name>-mcp/PLAN.md`** — architecture decisions, technology rationale, tool contracts, full
   phase breakdown, and risks. The reference document for why things are designed as they are.

3. **`<name>-mcp/docs/requirements.md`** — functional and non-functional requirements, interface
   contracts, error codes, and testing obligations for that server.

4. **`<name>-mcp/docs/architecture.md`** — component diagram, module responsibilities, data-flow
   traces, key algorithms, and dependency notes for that server.

5. **`docs/conventions.md`** — once, if you haven't already. Defines the project structure,
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

**In `<name>-mcp/docs/requirements.md`:**
- Update any FR/NFR/IR entries whose behaviour changed
- Add new requirements if new tools or constraints were introduced

**In `<name>-mcp/docs/architecture.md`:**
- Update component diagrams, data-flow traces, or algorithm descriptions if the implementation changed
- Keep module responsibility tables and function lists in sync with the actual source

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
│   ├── README.md               # User-facing: tools, install, run, test
│   ├── HANDOVER.md             # ← read first when working on this server
│   ├── PLAN.md                 # ← architecture and decisions
│   └── docs/
│       ├── requirements.md     # Functional/non-functional requirements, error codes
│       └── architecture.md     # Component diagram, data flow, algorithms
├── synth-mcp/                  # MusicXML → Audio          ✅ Phase 1 COMPLETE
│   ├── README.md
│   ├── HANDOVER.md
│   ├── PLAN.md
│   └── docs/
│       ├── requirements.md
│       └── architecture.md
├── render-mcp/                 # MusicXML → PDF/PNG        ✅ Phase 1 COMPLETE
│   ├── README.md
│   ├── HANDOVER.md
│   ├── PLAN.md
│   └── docs/
│       ├── requirements.md
│       └── architecture.md
├── musicxml-abc-mcp/           # MusicXML ↔ ABC            ✅ Phase 1 COMPLETE
│   ├── README.md
│   ├── HANDOVER.md
│   ├── PLAN.md
│   └── docs/
│       ├── requirements.md
│       └── architecture.md
└── pitch-mcp/                  # Mic audio → score pos/accuracy  ✅ Phase A+B COMPLETE
    ├── README.md
    ├── HANDOVER.md
    ├── PLAN.md
    └── docs/
        ├── requirements.md
        └── architecture.md
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

**Read before working:** [omr-mcp/HANDOVER.md](../omr-mcp/HANDOVER.md) · [omr-mcp/PLAN.md](../omr-mcp/PLAN.md) · [omr-mcp/docs/requirements.md](../omr-mcp/docs/requirements.md) · [omr-mcp/docs/architecture.md](../omr-mcp/docs/architecture.md)

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

### synth-mcp ✅ Phase 1 COMPLETE — 60 unit + 7 integration tests pass

**Purpose:** Synthesizes audio from MusicXML with selectable voice parts and tempo control.

**Read before working:** [synth-mcp/HANDOVER.md](../synth-mcp/HANDOVER.md) · [synth-mcp/PLAN.md](../synth-mcp/PLAN.md) · [synth-mcp/docs/requirements.md](../synth-mcp/docs/requirements.md) · [synth-mcp/docs/architecture.md](../synth-mcp/docs/architecture.md)

**Implemented tools:** `get_parts`, `synthesize`, `list_capabilities`

**Backend:** music21 (MusicXML → MIDI) + pyfluidsynth library (MIDI → WAV, no subprocess)

**System dependency:** `libfluidsynth.so.3` (installed at `/usr/lib/x86_64-linux-gnu/` on Ubuntu)
and an SF2 soundfont (path via `SYNTH_SOUNDFONT_PATH` env var).
System soundfonts: `/usr/share/sounds/sf2/TimGM6mb.sf2` or `default-GM.sf2`.
Synthesis tests skip automatically when `SYNTH_SOUNDFONT_PATH` is unset.

**Key files:**
- `src/synth_mcp/server.py` — MCP tool definitions
- `src/synth_mcp/engine.py` — music21 + pyfluidsynth synthesis pipeline
- `src/synth_mcp/utils.py` — MusicXML validation, tempo validation, path helpers

**Gotcha:** music21 9.x sets `part.id` to the part name (e.g. "Soprano"), not the XML `id`
attribute (e.g. "P1"). Callers must use part names when specifying `part_ids`.

---

### render-mcp ✅ Phase 1 COMPLETE — 68/68 tests pass (includes integration)

**Purpose:** Renders MusicXML to PDF or PNG for printing and display.

**Read before working:** [render-mcp/HANDOVER.md](../render-mcp/HANDOVER.md) · [render-mcp/PLAN.md](../render-mcp/PLAN.md) · [render-mcp/docs/requirements.md](../render-mcp/docs/requirements.md) · [render-mcp/docs/architecture.md](../render-mcp/docs/architecture.md)

**Implemented tools:** `render_to_pdf`, `render_to_image`, `list_capabilities`

**Backend:** Verovio (MusicXML → SVG, in-process) + cairosvg (SVG → PNG/PDF per page) + pypdf (merge pages)

**System dependency:** `libcairo.so.2` (system-wide on Ubuntu — no sudo needed). No MuseScore required.

**Key files:**
- `src/render_mcp/server.py` — MCP tool definitions
- `src/render_mcp/engine.py` — Verovio + cairosvg rendering pipeline
- `src/render_mcp/utils.py` — MusicXML validation, path helpers

**Gotcha:** Verovio SVGs have fixed pixel dimensions — use `scale=dpi/96.0` with cairosvg, not `dpi=`.

---

### musicxml-abc-mcp ✅ Phase 1 COMPLETE — 71/71 tests pass (includes integration)

**Purpose:** Converts between MusicXML and ABC notation so Claude can read and edit scores.

**Read before working:** [musicxml-abc-mcp/HANDOVER.md](../musicxml-abc-mcp/HANDOVER.md) · [musicxml-abc-mcp/PLAN.md](../musicxml-abc-mcp/PLAN.md) · [musicxml-abc-mcp/docs/requirements.md](../musicxml-abc-mcp/docs/requirements.md) · [musicxml-abc-mcp/docs/architecture.md](../musicxml-abc-mcp/docs/architecture.md)

**Implemented tools:** `musicxml_to_abc`, `abc_to_musicxml`, `validate_abc`, `list_capabilities`

**Backend:** music21 (MusicXML parsing + abc_to_musicxml) + custom ABC serializer (MusicXML → ABC)

**Note:** No system dependencies — pure Python.

**Key files:**
- `src/musicxml_abc_mcp/server.py` — MCP tool definitions
- `src/musicxml_abc_mcp/engine.py` — conversion pipeline + custom ABC serializer (no separate file)
- `src/musicxml_abc_mcp/utils.py` — input validation

**Gotcha:** music21 9.x has **no ABC write support** (`ConverterABC.registerOutputExtensions = ()`).
A custom serializer walks the music21 note model directly.
ABC octave convention (v2.1): lowercase `c` = C4 (middle C); uppercase `C` = C3.

---

### pitch-mcp ✅ Phase A+B COMPLETE — 93/93 tests pass

**Purpose:** Real-time pitch detection from microphone, compared against a reference score, to
show current position and pitch accuracy while singing.

**Read before working:** [pitch-mcp/HANDOVER.md](../pitch-mcp/HANDOVER.md) · [pitch-mcp/PLAN.md](../pitch-mcp/PLAN.md) · [pitch-mcp/docs/requirements.md](../pitch-mcp/docs/requirements.md) · [pitch-mcp/docs/architecture.md](../pitch-mcp/docs/architecture.md)

**Implemented tools:** `analyze_recording` (Phase A), `load_score`, `start_monitoring`,
`get_current_position`, `stop_monitoring`, `list_capabilities` (Phase B)

**Backend:** librosa pYIN (`librosa.pyin`) — pure Python, no system deps, excellent for singing voice.
Real-time Phase B uses sounddevice + YIN autocorrelation in a worker thread.

**System dependency:** `libportaudio2` required at runtime for real-time streams (Phase B).
Offline analysis (Phase A) has no system dependencies.

**Key files:**
- `src/pitch_mcp/server.py` — MCP tool definitions
- `src/pitch_mcp/engine.py` — session management + offline/real-time orchestration
- `src/pitch_mcp/pitch_detector.py` — librosa pYIN + optional crepe backend
- `src/pitch_mcp/aligner.py` — time-domain alignment, accuracy classification
- `src/pitch_mcp/utils.py` — note sequence extraction, metronome map, Hz↔note conversion

**Gotcha:** `crepe` fails to build under uv (missing `pkg_resources`) — keep as manual opt-in only.
`aubio` has no Python 3.13 wheel and requires system libs — use librosa instead.

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
