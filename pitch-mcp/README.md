# pitch-mcp

MCP server for real-time pitch detection and score alignment. Listens to a singer via microphone and reports their current position in a score and whether they are singing in tune.

## What it does

Covers three goals:
- **Goal 4** — Show the current measure/beat position while singing
- **Goal 5** — Report pitch accuracy (too high / too low / on pitch)
- **Goal 6** — Identify where in the score a singer is based on a hummed or sung phrase

Supports both offline analysis of pre-recorded audio and real-time microphone input.

## Tools

| Tool | Description |
|------|-------------|
| `analyze_recording` | Offline: analyse a WAV file against a reference MusicXML score |
| `load_score` | Load a MusicXML score into a named session; returns a `session_id` |
| `start_monitoring` | Open the microphone and begin real-time pitch detection |
| `get_current_position` | Poll the current score position and pitch accuracy |
| `stop_monitoring` | Stop the microphone and return a session summary |
| `list_capabilities` | Return server metadata: pitch backend, microphone availability |

## Installation

```bash
cd pitch-mcp
uv sync
```

For real-time monitoring (`start_monitoring`), PortAudio is required:

```bash
# Ubuntu / Debian
sudo apt install libportaudio2
```

## Running

```bash
uv run pitch-mcp
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PITCH_BACKEND` | `librosa` | Pitch detection algorithm: `librosa` or `crepe` |

`crepe` requires a manual TensorFlow install (~500 MB) and downloads ~50 MB of model weights on first use. The default `librosa` backend (pYIN algorithm) works well for singing voice with no extra setup.

## Usage examples

```json
// Offline analysis of a recording
{
  "tool": "analyze_recording",
  "arguments": {
    "wav_path": "/path/to/recording.wav",
    "musicxml_path": "/path/to/score.mxl",
    "part_name": "Soprano"
  }
}

// Real-time session
{"tool": "load_score", "arguments": {"musicxml_path": "/path/to/score.mxl", "part_name": "Alto"}}
// → returns {"session_id": "abc123"}

{"tool": "start_monitoring", "arguments": {"session_id": "abc123"}}
{"tool": "get_current_position", "arguments": {"session_id": "abc123"}}
// → returns measure, beat, expected pitch, detected pitch, accuracy

{"tool": "stop_monitoring", "arguments": {"session_id": "abc123"}}
```

Audio must be 16-bit PCM WAV. MP3 and FLAC are not supported.

## Testing

```bash
# Unit tests (no microphone or audio required)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

# Integration tests (uses pre-recorded WAV files)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration

# Manual tests (requires a real microphone — skip in CI)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m manual
```

## Dependencies

- [librosa](https://librosa.org/) — pYIN pitch detection (primary backend, pure Python)
- [music21](https://web.mit.edu/music21/) — score parsing and pitch calculations
- [sounddevice](https://python-sounddevice.readthedocs.io/) — real-time microphone input
- [numpy](https://numpy.org/), [scipy](https://scipy.org/) — numerics
- [mcp](https://github.com/modelcontextprotocol/python-sdk) — MCP protocol

## System requirements

- Python 3.12+
- `libportaudio2` — required for real-time microphone input (`start_monitoring`)
- No system libraries required for offline analysis

## Phase status

| Phase | Status |
|-------|--------|
| Phase A — offline analysis | Complete (93/93 tests pass) |
| Phase B — real-time monitoring | Session framework in place; microphone integration ready |
