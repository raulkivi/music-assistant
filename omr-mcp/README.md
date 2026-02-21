# OMR MCP Server

A Model Context Protocol (MCP) server for Optical Music Recognition (OMR) that converts sheet music images into MusicXML format.

## Features

- 🎼 Convert PNG/JPEG sheet music images to MusicXML
- 🤖 Powered by [oemer](https://github.com/BreezeWhite/oemer) deep learning engine
- 🔌 MCP server compatible with Claude Desktop and other MCP clients
- 🖥️ Runs locally - no cloud APIs required
- 📝 Returns structured MusicXML that works with MuseScore, Finale, etc.

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /home/luarvik/src/choir-music-assistant/omr-mcp
   ```

2. **Install dependencies:**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Test oemer installation:**
   ```bash
   python -c "from oemer import generate; print('oemer installed successfully')"
   ```
   
   **Note:** On first run, oemer will download model checkpoints (~10 minutes). This is a one-time setup.

### Usage with Claude Desktop

1. **Add to your Claude Desktop configuration** (`~/.config/claude/claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "omr": {
         "command": "uv",
         "args": ["--directory", "/home/luarvik/src/choir-music-assistant/omr-mcp", "run", "omr-mcp"]
       }
     }
   }
   ```

2. **Restart Claude Desktop**

3. **Use the OMR tool in Claude:**
   - Upload or reference a sheet music image (PNG/JPEG)
   - Ask Claude to "recognize the sheet music" or "convert this to MusicXML"
   - Claude will use the `recognize_sheet` tool automatically

### Standalone Testing

Test the server directly:

```bash
# Run the server
uv run omr-mcp

# In another terminal, test with sample input
echo '{"method": "tools/call", "params": {"name": "recognize_sheet", "arguments": {"image_path": "/path/to/your/sheet.png"}}}' | uv run omr-mcp
```

## Available Tools

### `recognize_sheet`

Converts sheet music images to MusicXML format.

**Input:**
- `image_path` (string): Path to PNG or JPEG sheet music image

**Output:**
```json
{
  "musicxml": "<score-partwise>...</score-partwise>",
  "metadata": {
    "source": "/path/to/input.png",
    "processing_time_ms": 15000,
    "output_path": "/path/to/generated.musicxml",
    "engine": "oemer"
  }
}
```

**Error handling:**
```json
{
  "error": "File not found: /path/to/missing.png"
}
```

## How It Works

1. **Input Validation:** Checks file format and existence
2. **OMR Processing:** Uses oemer's deep learning models to:
   - Detect staff lines and musical symbols
   - Classify notes, rests, clefs, time signatures
   - Extract musical semantics
3. **MusicXML Generation:** Converts recognized elements to standard MusicXML format
4. **Return Results:** Provides both the MusicXML content and processing metadata

## Technical Details

### OMR Engine: oemer

- **Architecture:** UNet segmentation + SVM classification
- **Models:** 
  - Staff line detection
  - Symbol segmentation (notes, clefs, accidentals)
  - Classification refinement
- **Runtime:** ONNX Runtime (CPU-optimized)
- **Processing Time:** 3-5 minutes per page (varies by complexity)

### Supported Formats

- **Input:** PNG, JPEG images
- **Output:** MusicXML (compatible with MuseScore, Finale, Sibelius, etc.)

### Performance Notes

- First run downloads models (~10 min setup)
- Processing time depends on image complexity and hardware
- GPU acceleration available but not required
- Works entirely offline

## Troubleshooting

### Common Issues

**Models not downloading:**
```bash
# Manual model download
pip install oemer[tf]  # If you prefer TensorFlow backend
```

**Import errors:**
```bash
# Verify installation
uv run python -c "import oemer; print('OK')"
```

**Claude Desktop not finding server:**
- Check config file path: `~/.config/claude/claude_desktop_config.json`
- Verify absolute paths in configuration
- Restart Claude Desktop after config changes

**Poor recognition quality:**
- Ensure high-resolution, clear images
- Try scanning at 300+ DPI
- Avoid handwritten scores for best results

### Logging

Enable detailed logging:
```bash
export OMR_LOG_LEVEL=DEBUG
uv run omr-mcp
```

## Development

### Project Structure

```
omr-mcp/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── HANDOVER.md             # Testing handover notes
├── src/
│   └── omr_mcp/
│       ├── __init__.py
│       ├── server.py       # MCP server implementation
│       ├── omr_engine.py   # oemer integration
│       └── utils.py        # Helper functions
├── tests/                  # Unit tests (26 passing)
│   ├── test_server.py
│   ├── test_omr.py
│   └── test_utils.py
└── test_samples/           # SATB a cappella test data
    ├── pdmx_satb_samples/  # PNG + MusicXML pairs
    └── pdmx_full/          # Full PDMX dataset (14GB)
```

### Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run unit tests (26 passing)
uv run pytest tests/ -v
```

### Test Samples

SATB a cappella test samples are available in `test_samples/pdmx_satb_samples/`:

```
pdmx_satb_samples/
├── mxl/    # 10 MusicXML files (ground truth)
├── pdf/    # 10 PDF scores  
└── png/    # 42 PNG images (OMR input)
```

**To extract more samples** (1684 available):
```bash
# Edit max_samples in the script, then run:
python test_samples/download_pdmx_satb.py
```

Source: [PDMX dataset](https://zenodo.org/records/14648209) - 250K+ public domain MusicXML scores.

## Roadmap

- [x] Phase 1: Basic OMR functionality
- [x] Phase 2: Enhanced input handling (base64 support)
- [x] Phase 3: Quality improvements and testing (unit tests + SATB fixtures)
- [ ] Phase 4: Advanced features (Audiveris backend, confidence scores)

## License

This project is open source. See individual dependencies for their licenses:
- [oemer](https://github.com/BreezeWhite/oemer) - OMR engine
- [MCP](https://github.com/modelcontextprotocol/python-sdk) - Protocol implementation

## Contributing

Issues and pull requests welcome! Please ensure compatibility with the MCP specification and test with real sheet music examples.