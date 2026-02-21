# pitch-mcp Test Fixtures

## Fixture Files

This directory is intentionally sparse for Phase A. Unit and engine tests use:
- Synthetic sine wave WAV files generated in-memory (via numpy/scipy)
- Inline MusicXML defined directly in test files

## Phase A Integration Tests

Integration tests (`@pytest.mark.integration`) use synthetic WAV fixtures generated
at test time and do not require a pre-recorded vocal file.

## Phase B Integration Tests (Future)

Phase B real-time monitoring tests require a microphone or audio loopback device.
These are marked `@pytest.mark.manual` and are not run in CI.

When a real vocal fixture is recorded, add:
- `soprano_phrase.wav` — a 10–20 second recording of the Soprano part from
  one of the SATB fixtures in `../omr-mcp/test_samples/pdmx_satb_samples/mxl/`
- `reference.musicxml` — the matching full MusicXML score (unzipped)
- Update this README with which specific piece was recorded

## Running Tests

```bash
# Unit tests only (default, fast)
VIRTUAL_ENV= .venv/bin/pytest tests/ -v

# Include integration tests
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration
```
