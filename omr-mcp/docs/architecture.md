# omr-mcp — Technical Architecture

## Overview

omr-mcp is a stateless MCP server that converts sheet music images to MusicXML using the oemer deep-learning OMR engine. Every tool call is independent; no state is retained between calls.

---

## Component Diagram

```
┌───────────────────────────────────────────────────────────┐
│                      MCP Client                           │
│              (Claude Desktop / web app)                   │
└──────────────────────────┬────────────────────────────────┘
                           │  stdio (JSON-RPC)
┌──────────────────────────▼────────────────────────────────┐
│                       server.py                           │
│                                                           │
│  list_tools()          → Tool definitions (5 tools)       │
│  call_tool(name, args) → dispatches to engine functions   │
│  _detect_input_format  → "path" | "base64"                │
│  main()                → stdio_server() entry point       │
└────────────┬──────────────────────────┬───────────────────┘
             │                          │
┌────────────▼────────────┐  ┌──────────▼───────────────────┐
│      omr_engine.py      │  │         utils.py             │
│                         │  │                              │
│  recognize_image()      │  │  validate_image_path()       │
│  recognize_image_to_    │  │  decode_base64_image()       │
│    file()               │  │  get_image_info()            │
│  recognize_images()     │  │  format_file_size()          │
│  _merge_musicxml_pages()│  └──────────────────────────────┘
│  _run_oemer()           │
│  _extract_musicxml_     │
│    metadata()           │
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│       oemer library     │
│  oemer.generate(path)   │
│  UNet + SVM models      │
│  ONNX Runtime inference │
└─────────────────────────┘
```

---

## Module Responsibilities

### `server.py`

Entry point and MCP protocol layer. Contains no business logic.

- Registers five tools with their JSON schemas
- Dispatches `call_tool` to the appropriate engine function
- Handles format detection: determines whether an input is a file path or base64 string via `_detect_input_format`
- Decodes base64 input to a temporary file before passing to the engine
- Converts engine results and exceptions into `TextContent` JSON responses
- Starts the server with `mcp.server.stdio.stdio_server()`

**Format detection heuristic in `_detect_input_format`:**
- If the string starts with `data:` → `"base64"`
- If the string is longer than 500 chars and contains no `/` or `\` path separators → `"base64"`
- Otherwise → `"path"`

### `omr_engine.py`

Core processing logic. No MCP imports.

| Function | Description |
|----------|-------------|
| `recognize_image(image_path)` | Run oemer on a single image; return MusicXML string + metadata |
| `recognize_image_to_file(input_path, output_path)` | Same as above but write MusicXML to disk |
| `recognize_images(image_paths)` | Process multiple pages; merge into one MusicXML document |
| `_run_oemer(image_path)` | Call `oemer.generate(image_path)`; return path to output MusicXML file |
| `_merge_musicxml_pages(pages)` | Stitch per-page MusicXML documents into one |
| `_extract_musicxml_metadata(xml)` | Regex-based extraction of stave count and measure count |

### `utils.py`

Input validation and helper utilities. No engine logic.

| Function | Description |
|----------|-------------|
| `validate_image_path(path)` | Check file exists, extension is PNG/JPG/JPEG, size ≤ 50 MB |
| `decode_base64_image(data, output_path)` | Decode base64 (strips `data:` prefix), write to temp file, verify with Pillow |
| `get_image_info(path)` | Return width, height, format, mode, file size via Pillow |
| `format_file_size(bytes)` | Human-readable string (KB / MB) |

---

## Data Flow

### Single image recognition

```
call_tool("recognize_sheet", {image_path: "/path/scan.png"})
  │
  ├─ server.py: _detect_input_format → "path"
  ├─ utils.py: validate_image_path ──→ error if invalid
  ├─ omr_engine.py: recognize_image
  │     ├─ _run_oemer(image_path) → oemer.generate → "/tmp/oemer_out/score.xml"
  │     ├─ read MusicXML from output file
  │     └─ _extract_musicxml_metadata → {staves_detected, measures}
  └─ return {"musicxml": "...", "metadata": {...}}
```

### Base64 image input

```
call_tool("recognize_sheet", {image_base64: "<data>", mime_type: "image/jpeg"})
  │
  ├─ server.py: _detect_input_format → "base64"
  ├─ utils.py: decode_base64_image → /tmp/omr_XXXXX.jpg
  └─ (same as above from validate_image_path onwards)
```

### Multi-page recognition

```
call_tool("recognize_sheets", {image_paths: ["/p1.png", "/p2.png"]})
  │
  ├─ omr_engine.py: recognize_images
  │     ├─ recognize_image("/p1.png") → musicxml_1
  │     ├─ recognize_image("/p2.png") → musicxml_2
  │     └─ _merge_musicxml_pages([musicxml_1, musicxml_2])
  │           ├─ Parse each page with defusedxml.ElementTree
  │           ├─ For each subsequent page:
  │           │     find max measure number in base document
  │           │     append page's measures, renumbering from (max + 1)
  │           └─ Return merged XML string
  └─ return {"musicxml": "...", "page_count": 2, "metadata": {...}}
```

---

## Multi-Page Merge Algorithm

Pages are merged by appending measures from each successive page to the corresponding part in the base document.

```
base_doc = parse(page_1_xml)
for page in pages[1:]:
    page_doc = parse(page_xml)
    for part_index, part in enumerate(page_doc.parts):
        base_part = base_doc.parts[part_index]   # matched by index
        last_num = max(m.number for m in base_part.measures)
        for measure in part.measures:
            measure.number += last_num            # renumber sequentially
            base_part.append(measure)
return serialize(base_doc)
```

Parts are matched by index (not by name), so the number of parts must be consistent across pages.

---

## oemer Integration

`_run_oemer(image_path)` calls `oemer.generate(image_path)` directly as a library function (not a subprocess). oemer:

1. Runs staffline detection (UNet segmentation model)
2. Runs symbol segmentation (UNet model)
3. Classifies symbols (SVM)
4. Writes a MusicXML file to a subdirectory near the input image
5. Returns the path to that file

Model checkpoints are downloaded on first call (~100 MB) and cached in `~/.cache/oemer/` (or the oemer package directory). Subsequent calls use the cached models.

Metadata (stave count, measure count) is extracted by scanning the returned MusicXML with regexes rather than a full parse, for speed.

---

## Error Handling

All errors are returned as JSON text content rather than raising MCP protocol errors.

```json
{"error": "File not found: /path/scan.png", "error_code": "FILE_NOT_FOUND"}
```

| Scenario | Code |
|----------|------|
| File not found | `FILE_NOT_FOUND` |
| Unsupported image format | `INVALID_FORMAT` |
| Image too large (> 50 MB) | `INVALID_INPUT` |
| Base64 decode failure | `INVALID_INPUT` |
| Pillow cannot open image | `INVALID_INPUT` |
| oemer processing error | `PROCESSING_FAILED` |

---

## Key Dependencies

| Package | Role |
|---------|------|
| `oemer` | OMR engine — UNet + SVM, ONNX Runtime |
| `Pillow` | Image validation and info extraction |
| `defusedxml` | Safe XML parsing (prevents XXE attacks) |
| `mcp` | MCP protocol SDK |

No system libraries are required. ONNX Runtime is bundled with the oemer pip package.

---

## Server Startup

```python
# server.py main()
async def _run():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

asyncio.run(_run())
```

The server process is single-threaded. Each tool call is handled sequentially. oemer processing blocks the event loop for the duration (3–5 min per page on CPU); this is acceptable for Phase 1 as MCP clients handle timeouts.

---

## File Layout

```
omr-mcp/
├── pyproject.toml
├── src/
│   └── omr_mcp/
│       ├── __init__.py
│       ├── server.py        ← MCP layer (tool registration, dispatch)
│       ├── omr_engine.py    ← Business logic (oemer, merge)
│       └── utils.py         ← Input validation, base64, image info
└── tests/
    ├── test_server.py
    ├── test_omr.py
    ├── test_utils.py
    └── test_samples/
        └── pdmx_satb_samples/  ← PNG + MXL fixture pairs
```
