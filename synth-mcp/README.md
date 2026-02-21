# synth-mcp

MCP server that synthesizes audio from a MusicXML score. Callers can select which voice parts to
include (Soprano, Alto, Tenor, Bass, or any combination) and optionally adjust the tempo.

**Output:** WAV file written to disk; path returned in the tool response.

---

## Installation

### 1. Install system dependencies

**Linux**
```bash
apt install fluidsynth libfluidsynth-dev
```

**macOS**
```bash
brew install fluid-synth
```

Verify:
```bash
fluidsynth --version
```

### 2. Download a soundfont

The server requires an SF2 soundfont file. Both options below are free:

| Soundfont | Size | Download |
|-----------|------|----------|
| MuseScore General (recommended) | ~200 MB | https://musescore.org/en/handbook/soundfonts-and-sfz-files |
| GeneralUser GS | ~30 MB | https://schristiancollins.com/generaluser.php |

Save the file somewhere permanent and note the path — you'll need it as `SYNTH_SOUNDFONT_PATH`.

### 3. Install Python dependencies

```bash
cd synth-mcp
uv sync
```

### 4. Verify the setup

```bash
SYNTH_SOUNDFONT_PATH=/path/to/soundfont.sf2 uv run synth-mcp
```

You should see log output confirming the soundfont is found and the server has started.

---

## Claude Desktop configuration

Merge the following into `~/.config/claude/claude_desktop_config.json`
(see `examples/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "synth": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/synth-mcp", "run", "synth-mcp"],
      "env": {
        "SYNTH_SOUNDFONT_PATH": "/absolute/path/to/soundfont.sf2"
      }
    }
  }
}
```

---

## Tools

### `get_parts`

Lists all voice parts in a MusicXML score.

**Input**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `musicxml` | string | Yes | MusicXML document as a string |

**Output**
```json
{
  "parts": [
    {"id": "P1", "name": "Soprano", "measure_count": 32},
    {"id": "P2", "name": "Alto",    "measure_count": 32},
    {"id": "P3", "name": "Tenor",   "measure_count": 32},
    {"id": "P4", "name": "Bass",    "measure_count": 32}
  ]
}
```

---

### `synthesize`

Synthesizes a WAV file from a MusicXML score.

**Input**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `musicxml` | string | Yes | MusicXML document as a string |
| `part_ids` | list[string] | No | Part IDs to include (default: all parts) |
| `tempo_factor` | float | No | Tempo multiplier 0.25–4.0 (default: 1.0) |
| `output_path` | string | No | WAV output path (auto-generated if omitted) |

**Output**
```json
{
  "audio_path": "/tmp/synth-mcp/output_20260221_143012.wav",
  "format": "wav",
  "duration_seconds": 142.5,
  "parts_included": ["P1"],
  "tempo_factor": 0.75
}
```

---

### `list_capabilities`

Returns server metadata and runtime status.

**Output**
```json
{
  "server": "synth-mcp",
  "version": "0.1.0",
  "input_formats": ["musicxml"],
  "output_formats": ["wav"],
  "tools": ["get_parts", "synthesize", "list_capabilities"],
  "backend": "fluidsynth",
  "backend_version": "2.3.4",
  "soundfont_loaded": true,
  "soundfont_path": "/path/to/soundfont.sf2",
  "fluidsynth_available": true
}
```

---

## Running tests

```bash
# Unit tests only (fast, no system dependencies needed beyond music21)
uv run pytest tests/ -v

# Include integration tests (requires MXL fixtures from omr-mcp)
uv run pytest tests/ -v -m integration
```

---

## Known limitations

- music21's MIDI export may drop some articulations and dynamics. Acceptable for practice playback.
- Audio output is always WAV. Convert to MP3 with `ffmpeg -i out.wav out.mp3` if needed.
- Large scores (100+ measures) may take several seconds to synthesize.
