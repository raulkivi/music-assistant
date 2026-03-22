# musicxml-abc-mcp

MCP server that converts between MusicXML and ABC notation.

## What it does

Bridges MusicXML (the standard but verbose XML format) and ABC notation (a compact, human-readable text format). The primary use case is enabling LLM-assisted score editing: MusicXML → ABC → Claude edits → ABC → MusicXML.

ABC is ideal for LLM editing because it is concise enough to fit in a context window and expressive enough to represent most choral music.

## Tools

| Tool | Description |
|------|-------------|
| `musicxml_to_abc` | Convert MusicXML to ABC notation; optionally filter to a single part |
| `abc_to_musicxml` | Convert ABC notation back to MusicXML |
| `validate_abc` | Parse an ABC string and return errors or warnings |
| `list_capabilities` | Return server metadata: backend version, ABC standard |

## Installation

```bash
cd musicxml-abc-mcp
uv sync --extra dev
```

Note: use `--extra dev` (not `--group dev`) to install pytest.

## Running

```bash
uv run musicxml-abc-mcp
```

No environment variables required.

## Usage examples

```json
// Convert full score to ABC
{
  "tool": "musicxml_to_abc",
  "arguments": {"musicxml_path": "/path/to/score.mxl"}
}

// Extract just the Soprano part
{
  "tool": "musicxml_to_abc",
  "arguments": {"musicxml_path": "/path/to/score.mxl", "part_name": "Soprano"}
}

// Convert edited ABC back to MusicXML
{
  "tool": "abc_to_musicxml",
  "arguments": {"abc_text": "X:1\nT:My Song\n...", "output_path": "/tmp/edited.mxl"}
}

// Validate ABC before converting
{
  "tool": "validate_abc",
  "arguments": {"abc_text": "X:1\nT:My Song\n..."}
}
```

## ABC notation basics

This server uses ABC standard v2.1:

- `c` (lowercase) = C4 (middle C)
- `C` (uppercase) = C3 (one octave below middle C)
- Apostrophe raises an octave: `c'` = C5
- Comma lowers an octave: `C,` = C2

Round-trips preserve notes within ±2%. Dynamics and complex articulations are not preserved.

## Testing

```bash
# All tests including integration (round-trip SATB conversion)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v
```

## Dependencies

- [music21](https://web.mit.edu/music21/) — score parsing; ABC output uses a custom serializer (music21 9.x has no ABC writer)
- [mcp](https://github.com/modelcontextprotocol/python-sdk) — MCP protocol

## System requirements

- Python 3.11+
- No system libraries required
