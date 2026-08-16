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
| `list_supported_formats` | (Deprecated — use `list_capabilities`) List supported input and output formats |
| `health_check` | Check that all runtime dependencies are available and return a human-readable status summary; useful on first run |

## Installation

```bash
cd omr-mcp
uv sync
```

On first run, oemer downloads ~100 MB of model checkpoints. This happens once and is cached.

**Quick install:** `bash install.sh` sets up everything in one command and prints a ready-to-paste
client config — see [SETUP.md](SETUP.md). Ready-made configs for Claude Desktop, Cursor, Windsurf,
Continue, and Zed are in [`examples/`](examples/). Having trouble? Check
[TROUBLESHOOTING.md](TROUBLESHOOTING.md).

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

# Integration tests (~10 min one-time model-checkpoint download, then ~90-100s per page on CPU)
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
- `onnxruntime==1.18.1` — pinned; newer releases reject the ConvTranspose shapes baked into oemer's checkpoints (see `pyproject.toml` comments / `docs/HANDOVER.md` gotchas)
- `opencv-python-headless==4.10.0.84` — pinned; 5.x changed `cv2.HoughLinesP()`'s return shape, which crashes oemer's staffline extraction (see `pyproject.toml` comments / `docs/HANDOVER.md` gotchas)
- [Pillow](https://python-pillow.org/) — image loading and validation
- [defusedxml](https://github.com/tiran/defusedxml) — safe XML parsing
- [mcp](https://github.com/modelcontextprotocol/python-sdk) — MCP protocol

## Known limitations

- **SATB voice structure is currently lost.** oemer reads multi-staff choir systems sequentially
  rather than simultaneously, so a 4–5 voice SATB score comes out as a single merged `<part>` with
  the clef alternating back and forth, instead of one part per voice. This is real data loss, not
  a benign modeling difference (confirmed by inspecting generated MusicXML), and makes current
  output **unusable for anything that depends on multi-voice structure** — e.g. per-voice
  synthesis or score comparison. This is a known, currently open issue; see
  [docs/HANDOVER.md](docs/HANDOVER.md) for the full investigation.

## Performance notes

- Processing time: ~90–100s per page on CPU once the model checkpoints are cached
- oemer output may vary slightly between runs — do not assert on exact XML equality
- The generated MusicXML is functionally correct but may not pass strict schema validation

## System requirements

- Python 3.11+
- No system libraries required (ONNX Runtime is bundled via pip)
