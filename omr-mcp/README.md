# omr-mcp

MCP server that converts sheet music images to MusicXML using optical music recognition (OMR).

## What it does

Takes a photo or scan of printed sheet music and returns a MusicXML document. Handles single pages or multi-page scores. Feeds directly into the rest of the choir-music-assistant pipeline.

## Tools

| Tool | Description |
|------|-------------|
| `recognize_sheet` | Convert a single image (file path or base64) to MusicXML string |
| `recognize_sheet_to_file` | Convert a single image and write MusicXML to a file |
| `recognize_sheets` | Process multiple pages and merge them into one MusicXML document |
| `list_capabilities` | Return server metadata: backend version, input/output formats, available tools |

## Installation

```bash
cd omr-mcp
uv sync
```

On first run, oemer downloads ~100 MB of model checkpoints. This happens once and is cached.

## Running

```bash
uv run omr-mcp
```

No environment variables required.

## Claude Desktop configuration

```json
{
  "mcpServers": {
    "omr": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/omr-mcp", "run", "omr-mcp"]
    }
  }
}
```

## Usage examples

```json
// Recognize a single image file
{"tool": "recognize_sheet", "arguments": {"image_path": "/path/to/scan.png"}}

// Recognize from base64-encoded image
{"tool": "recognize_sheet", "arguments": {"image_base64": "<base64 data>", "mime_type": "image/jpeg"}}

// Process multiple pages into one score
{"tool": "recognize_sheets", "arguments": {"image_paths": ["/path/page1.png", "/path/page2.png"]}}

// Save result directly to file
{"tool": "recognize_sheet_to_file", "arguments": {"image_path": "/path/scan.png", "output_path": "/tmp/score.mxl"}}
```

## Testing

```bash
# Unit tests (fast, no model required)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

# Integration tests (requires model download, ~10 min per page)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration
```

## Test samples

SATB a cappella samples are available in `test_samples/pdmx_satb_samples/`:

```
pdmx_satb_samples/
├── mxl/    # MusicXML ground truth
├── pdf/    # PDF scores
└── png/    # PNG images (OMR input)
```

Source: [PDMX dataset](https://zenodo.org/records/14648209) — 250K+ public domain scores.

## Dependencies

- [oemer](https://github.com/BreezeWhite/oemer) — deep learning OMR engine (UNet + SVM, ONNX Runtime)
- [Pillow](https://python-pillow.org/) — image loading and validation
- [defusedxml](https://github.com/tiran/defusedxml) — safe XML parsing
- [mcp](https://github.com/modelcontextprotocol/python-sdk) — MCP protocol

## Performance notes

- Processing time: 3–5 minutes per page on CPU
- oemer output may vary slightly between runs — do not assert on exact XML equality
- The generated MusicXML is functionally correct but may not pass strict schema validation

## System requirements

- Python 3.11+
- No system libraries required (ONNX Runtime is bundled via pip)
