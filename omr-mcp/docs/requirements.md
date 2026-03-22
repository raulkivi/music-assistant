# omr-mcp Requirements

## Purpose

Convert photographs or scans of printed sheet music into MusicXML documents. This is the entry point of the choir-music-assistant pipeline — its output feeds every other server.

Covers **Goal 1**: Digitize paper sheet music (photograph → digital score).

---

## Functional Requirements

### FR-1 — Single image recognition

The server MUST accept a single sheet music image and return a valid MusicXML string.

- Accepted input forms: absolute file path to a PNG or JPEG file; base64-encoded image data with MIME type
- The returned MusicXML MUST be a complete `<score-partwise>` document
- Processing time MUST be under 30 seconds for a typical single-page score on CPU hardware

### FR-2 — Save result to file

The server MUST accept an output file path and write the MusicXML to disk, returning the written path.

### FR-3 — Multi-page recognition

The server MUST accept a list of image paths (one per page) and merge the results into a single MusicXML document.

- Pages MUST be merged in the order supplied
- The merged document MUST be a single `<score-partwise>` with all pages' measures appended

### FR-4 — Capability reporting

The server MUST expose a tool that returns:

- Server name and version
- Supported input formats (PNG, JPEG)
- Output format (MusicXML)
- OMR engine name and version
- List of available tools

### FR-5 — Input validation

The server MUST reject input that fails the following checks and return a descriptive error:

| Check | Condition |
|-------|-----------|
| File existence | File path must point to an existing file |
| File format | File extension and MIME type must be PNG or JPEG |
| Base64 validity | Base64 string must decode without error |
| Image readability | Pillow must be able to open the decoded image |

---

## Non-Functional Requirements

### NFR-1 — Accuracy

The OMR engine MUST correctly recognize standard Western staff notation including: noteheads, stems, beams, rests, clefs, key signatures, time signatures, bar lines, and accidentals.

Accuracy on clean, printed scores (300+ DPI) MUST be sufficient for practical choir practice use. Handwritten scores and low-quality scans may produce degraded output; this is acceptable but SHOULD be documented.

### NFR-2 — Offline operation

All processing MUST run locally. No network requests to external APIs or cloud services are permitted during recognition.

### NFR-3 — Model bootstrapping

On first run, the server MAY download model checkpoints (~100 MB). Subsequent runs MUST use the cached models. Download MUST be automatic and require no manual intervention beyond internet access.

### NFR-4 — Output correctness

The returned MusicXML MAY not pass strict schema validation, but MUST be functionally correct and parseable by music21, MuseScore, and Finale.

### NFR-5 — Determinism tolerance

oemer output may vary slightly between runs on the same image. Callers MUST NOT assert byte-identical output across runs.

### NFR-6 — Transport

The server MUST communicate via MCP stdio transport. It MUST NOT require any network port or GUI.

---

## Interface Requirements

### IR-1 — MCP protocol

The server MUST implement the Model Context Protocol using `mcp.server.stdio.stdio_server()`. Tools MUST be registered with correct input schemas.

### IR-2 — Tool: `recognize_sheet`

```
Input:
  image_path   string  (optional) absolute path to PNG/JPEG
  image_base64 string  (optional) base64-encoded image data
  mime_type    string  (optional) "image/png" or "image/jpeg"; required when image_base64 is provided
  output_path  string  (optional) path to write MusicXML; if omitted, MusicXML is returned inline

At least one of image_path or image_base64 must be provided.

Output:
  musicxml     string  MusicXML document
  metadata     object
    source              string   original image path or "base64"
    processing_time_ms  integer
    engine              string   "oemer"
```

### IR-3 — Tool: `recognize_sheet_to_file`

```
Input:
  image_path   string  required  absolute path to PNG/JPEG
  output_path  string  optional  path to write MusicXML (auto-generated if omitted)

Output:
  output_path  string  path of written file
  metadata     object  same structure as recognize_sheet
```

### IR-4 — Tool: `recognize_sheets`

```
Input:
  image_paths  list[string]  required  ordered list of image paths

Output:
  musicxml     string  merged MusicXML document
  page_count   integer
  metadata     object
```

### IR-5 — Tool: `list_capabilities`

```
Output:
  server          string
  version         string
  input_formats   list[string]   ["png", "jpeg"]
  output_formats  list[string]   ["musicxml"]
  tools           list[string]
  engine          string         "oemer"
  engine_version  string
```

### IR-6 — Error response format

All error responses MUST follow this structure:

```json
{"error": "<human-readable message>", "error_code": "<CODE>"}
```

| Code | Condition |
|------|-----------|
| `FILE_NOT_FOUND` | Input file does not exist |
| `INVALID_FORMAT` | Unsupported file format |
| `INVALID_INPUT` | Image cannot be decoded or opened |
| `PROCESSING_FAILED` | OMR engine error |

---

## Constraints

- Language: Python 3.11+
- Package manager: uv
- OMR engine: oemer (primary); Audiveris is a future option, not required for Phase 1
- No subprocess calls to system tools; oemer runs in-process
- No shared state between tool calls; each call is independent

---

## Testing Requirements

### TR-1 — Unit tests

Unit tests MUST cover:

- Input validation (invalid path, bad format, bad base64, missing required fields)
- Error response format and error codes
- `list_capabilities` response schema
- MusicXML string return path vs file write path

Unit tests MUST mock the oemer engine and MUST NOT perform real OMR.

### TR-2 — Integration tests

Integration tests MUST:

- Be marked `@pytest.mark.integration`
- Be skipped by default (`pytest tests/ -v` skips them)
- Run a real oemer recognition on at least one fixture PNG from `test_samples/pdmx_satb_samples/png/`
- Assert that the returned MusicXML contains `<score-partwise>`
- Assert that music21 can parse the returned MusicXML without error

Integration tests MAY be slow (up to 10 minutes per page on CPU). This is acceptable.

### TR-3 — Test fixtures

Test fixtures MUST be committed to the repository. The primary fixture source is `test_samples/pdmx_satb_samples/` (SATB a cappella scores from the PDMX dataset).
