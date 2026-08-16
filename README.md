# Choir Music Assistant

Help choir singers digitize, practice with, and navigate sheet music using their phones.

## Goals

1. Digitize paper sheet music (photograph → digital score)
2. Export sheet music as a PDF
3. Play sheet music in individual voices (Soprano, Alto, Tenor, Bass) or combined
4. Show the current position in the score while singing (tempo tracking)
5. Show pitch accuracy in real time (too high / too low / on pitch)
6. Identify where in a score a singer currently is based on a hummed or sung melody
7. Compare two scores (editions, arrangements, OMR output vs. reference) and report structured diffs

## Delivery Phases

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1 — MCP Servers** | Six independent MCP servers, each covering one capability | 🔶 5 of 6 complete; omr-mcp's default (oemer) engine has a known SATB bug, fixed via opt-in `engine="audiveris"` |
| **Phase 2 — Web PoC** | Web app orchestrating the MCP servers for full UX validation | Planned |
| **Phase 3 — Android App** | Native Kotlin app for rehearsal use on phones | Planned |

---

## System Components

Six MCP servers, each independently deployable from its own directory:

| Server | Directory | Input → Output | Goals |
|--------|-----------|----------------|-------|
| **omr-mcp** | [omr-mcp/](omr-mcp/) | Sheet music image → MusicXML | 1 |
| **render-mcp** | [render-mcp/](render-mcp/) | MusicXML → PDF / PNG | 2 |
| **synth-mcp** | [synth-mcp/](synth-mcp/) | MusicXML + voice selection → Audio (WAV) | 3 |
| **musicxml-abc-mcp** | [musicxml-abc-mcp/](musicxml-abc-mcp/) | MusicXML ↔ ABC notation | LLM editing bridge |
| **pitch-mcp** | [pitch-mcp/](pitch-mcp/) | Microphone audio + loaded score → position + accuracy | 4, 5, 6 |
| **comparer-mcp** | [comparer-mcp/](comparer-mcp/) | Two MusicXML → structured diff | 7 |

### Why ABC notation?

ABC is a compact, text-based music notation format that LLMs can read and edit directly (unlike the
verbose XML of MusicXML). The `musicxml-abc-mcp` server enables AI-assisted score editing:
MusicXML → ABC → Claude edits → ABC → MusicXML.

---

## Data Flow

```
Paper score
    │  (photo)
    ▼
[omr-mcp]
    │  MusicXML
    ├──────────────────────────► [render-mcp] ──► PDF / PNG         (goal 2)
    │
    ├──────────────────────────► [synth-mcp]                        (goal 3)
    │                                │  voice selection + tempo
    │                                ▼
    │                            Audio file
    │
    ├──────────────────────────► [musicxml-abc-mcp]
    │                                │  ABC text
    │                                ▼
    │                            Claude (reads / edits)
    │                                │  ABC text (edited)
    │                                ▼
    │                            [musicxml-abc-mcp]
    │                                │  MusicXML (AI-edited)
    │                                ▼
    │                            (back into pipeline)
    │
    ├──────────────────────────► [pitch-mcp]
    │                                │  loads reference score
    │                                ▲  microphone audio stream
    │                                │
    │                            score position + pitch accuracy    (goals 4, 5, 6)
    │
    └──────────────────────────► [comparer-mcp]  (also compares against any MusicXML)
                                     │  reference score
                                     ▲  second MusicXML (edition / arrangement / OMR output)
                                     │
                                 structured diff                    (goal 7)
```

---

## Implementation Status

| Server | Status | Tests |
|--------|--------|-------|
| omr-mcp | ⚠️ Phase 1-4 complete; default (oemer) engine loses SATB voice structure — fixed via opt-in `engine="audiveris"`, not yet the default | 111 unit |
| synth-mcp | ✅ Phase 1 + UX complete | 60 unit + 7 integration |
| render-mcp | ✅ Phase 1 + UX complete | 68/68 incl. integration |
| musicxml-abc-mcp | ✅ Phase 1 + UX complete | 71/71 incl. integration |
| pitch-mcp | ✅ Phase A+B + UX complete (audio-driven position tracking, DTW via dtaidistance) | 112 unit + 4 integration |
| comparer-mcp | ✅ Phase 4 (advanced features) complete | 132/132 (125 unit + 7 integration) |

"UX complete" servers ship as installable PyPI packages with an `install.sh`, a non-technical
`SETUP.md`, ready-made client configs under `examples/`, a `health_check` tool, and a
`TROUBLESHOOTING.md` — see [docs/SETUP_UX_PLAN.md](docs/SETUP_UX_PLAN.md).

---

## Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Best library ecosystem for music, audio, and ML |
| Package manager | uv | Fast, reproducible builds |
| MCP framework | `mcp` Python SDK | Official SDK; stdio transport for local deployment |
| OMR | oemer / ONNXRuntime | Sheet music recognition |
| Rendering | Verovio + cairosvg + pypdf | No external CLI dependency |
| Synthesis | pyfluidsynth + music21 | In-process, no subprocess |
| Pitch detection | librosa pYIN + sounddevice | Pure Python, excellent for singing voice |
| Comparison | music21 | Structural / musical diffing of scores |
| Testing | pytest + pytest-asyncio | Standard async-capable testing |
| Phase 2 | Web app (TBD) | PoC to validate UX |
| Phase 3 | Kotlin (Android) | Native mobile for rehearsal |

---

## Getting Started

Each server has its own Python virtual environment managed by [uv](https://github.com/astral-sh/uv).

```bash
# Set up a server (example: synth-mcp)
cd synth-mcp
uv sync

# Run unit tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

# Run integration tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration
```

> **Never use `pip install`** — always use `uv sync` or `uv add`. Never share venvs between servers.

### System dependencies (pre-installed)

| Library | Used by |
|---------|---------|
| `libfluidsynth.so.3` | synth-mcp |
| `libcairo.so.2` | render-mcp |
| `libportaudio2` | pitch-mcp |

Soundfonts: `/usr/share/sounds/sf2/TimGM6mb.sf2`, `/usr/share/sounds/sf2/default-GM.sf2`

---

## Documentation

- [docs/conventions.md](docs/conventions.md) — coding and structural conventions shared across all servers
- [docs/sources.md](docs/sources.md) — references and sources
- [docs/SETUP_UX_PLAN.md](docs/SETUP_UX_PLAN.md) — end-user packaging plan (PyPI, installers, setup docs)
- Each server has its own `docs/` folder with `PLAN.md`, `HANDOVER.md`, `requirements.md`, and `architecture.md`
