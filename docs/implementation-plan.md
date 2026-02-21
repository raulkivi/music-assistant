# Implementation Plan

High-level roadmap for the Choir Music Assistant. Each MCP server has its own detailed `PLAN.md`
in its directory. See [Intro.md](Intro.md) for goals, phases, and data flow.
See [conventions.md](conventions.md) for coding standards all servers must follow.

---

## Build Order

```
1. omr-mcp            ✅ mostly complete — finish remaining items
2. synth-mcp          ❌ next priority
3. render-mcp         ❌
4. musicxml-abc-mcp   ❌
5. pitch-mcp          ❌ most complex — build last
```

---

## Server Summaries

| Server | Purpose | Goals | Detail |
|--------|---------|-------|--------|
| **omr-mcp** | Converts sheet music images to MusicXML using deep learning OCR | 1 | [omr-mcp/PLAN.md](../omr-mcp/PLAN.md) |
| **synth-mcp** | Synthesizes audio from MusicXML with selectable voice parts and tempo control | 3 | [synth-mcp/PLAN.md](../synth-mcp/PLAN.md) |
| **render-mcp** | Renders MusicXML to high-quality PDF or PNG for printing and display | 2 | [render-mcp/PLAN.md](../render-mcp/PLAN.md) |
| **musicxml-abc-mcp** | Converts between MusicXML and ABC notation so Claude can read and edit scores | LLM bridge | [musicxml-abc-mcp/PLAN.md](../musicxml-abc-mcp/PLAN.md) |
| **pitch-mcp** | Real-time pitch detection from microphone, compared against a reference score | 4, 5, 6 | [pitch-mcp/PLAN.md](../pitch-mcp/PLAN.md) |

---

## Dependencies Between Servers

```
omr-mcp  ──produces MusicXML──►  synth-mcp
                              ►  render-mcp
                              ►  musicxml-abc-mcp
                              ►  pitch-mcp

musicxml-abc-mcp  ──produces edited MusicXML──►  (any of the above)
```

All downstream servers accept MusicXML as a string. The calling client (Claude, web app, or
Android app) is responsible for passing MusicXML between servers. Servers are stateless with
respect to storage.

---

## Phase 2 — Web PoC

Once all five MCP servers are built and tested individually, build a minimal web application that
orchestrates them.

**Stack (provisional):**
- Backend: FastAPI (Python) — acts as MCP client, connects to MCP servers via stdio or SSE
- Frontend: React or plain HTML/JS — keep minimal for PoC
- Real-time: WebSockets for pitch monitoring updates from `pitch-mcp`

**Core screens:**
1. **Scan** — camera capture → omr-mcp → MusicXML stored in session
2. **Score view** — render-mcp → display PNG pages
3. **Practice** — synth-mcp → play selected voice at chosen tempo
4. **Sing** — pitch-mcp → real-time position indicator and pitch accuracy
5. **Export** — render-mcp → download PDF

---

## Phase 3 — Android App

Native Kotlin app targeting Android 10+. Reuses the Phase 2 FastAPI backend (running locally or
on a companion device).

- Camera → omr-mcp
- Microphone → pitch-mcp
- Score pages as images fetched from render-mcp
- Audio playback streamed from synth-mcp
