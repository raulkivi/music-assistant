# Choir Music Assistant

## Vision

Help choir singers digitize, practice with, and navigate sheet music using their phones.

## Goals

1. Digitize paper sheet music (photograph → digital score)
2. Export sheet music as a PDF file
3. Play sheet music in individual voices (Soprano, Alto, Tenor, Bass) or combined
4. Show the current position in the score while singing (tempo tracking)
5. Show pitch accuracy in real time (too high / too low / on pitch)
6. Identify where in a score a singer currently is based on a hummed or sung melody

## Delivery Phases

### Phase 1 — MCP Servers *(current)*

Build and test each capability as an independent MCP server. Each server is self-contained and deployable on its own. Claude Desktop (or any MCP client) can use them individually or together.

### Phase 2 — Web PoC

A web application that orchestrates the MCP servers to deliver the full user experience described in Goals 1–6. This is a proof-of-concept to validate the UX before investing in mobile development.

### Phase 3 — Android App

Native Android application (Kotlin) for use on phones during rehearsal.

---

## System Components

Five MCP servers, each independently deployable from its own directory:

| Server | Directory | Input → Output | Goals covered |
|--------|-----------|----------------|---------------|
| **omr-mcp** | `omr-mcp/` | Sheet music image → MusicXML | 1 |
| **render-mcp** | `render-mcp/` | MusicXML → PDF / PNG | 2 |
| **synth-mcp** | `synth-mcp/` | MusicXML + voice selection → Audio | 3 |
| **musicxml-abc-mcp** | `musicxml-abc-mcp/` | MusicXML ↔ ABC notation | LLM editing bridge |
| **pitch-mcp** | `pitch-mcp/` | Microphone audio + loaded score → position + accuracy | 4, 5, 6 |

### Why ABC notation?

ABC is a compact, text-based music notation format that large language models can read and edit
directly (unlike the verbose XML of MusicXML). The `musicxml-abc-mcp` enables AI-assisted score
editing: MusicXML → ABC → Claude edits → ABC → MusicXML.

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
    └──────────────────────────► [pitch-mcp]
                                     │  loads reference score
                                     ▲  microphone audio stream
                                     │
                                 score position + pitch accuracy    (goals 4, 5, 6)
```

---

## Implementation Status

| Server | Status | Notes |
|--------|--------|-------|
| omr-mcp | ✅ Mostly complete | Integration tests and batch processing pending |
| synth-mcp | ❌ Not started | Next priority |
| render-mcp | ❌ Not started | |
| musicxml-abc-mcp | ❌ Not started | |
| pitch-mcp | ❌ Not started | Most complex component |

---

## Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Best library ecosystem for music, audio, and ML |
| Package manager | uv | Fast, reproducible builds; preferred over pip |
| MCP framework | `mcp` Python SDK | Official SDK; stdio transport for local deployment |
| Testing | pytest + pytest-asyncio | Standard async-capable testing |
| Phase 2 | Web app (TBD) | PoC to validate UX before mobile investment |
| Phase 3 | Kotlin (Android) | Native mobile for rehearsal use |

See [conventions.md](conventions.md) for coding and structural conventions shared across all MCP servers.
See [implementation-plan.md](implementation-plan.md) for the detailed build plan for each component.
