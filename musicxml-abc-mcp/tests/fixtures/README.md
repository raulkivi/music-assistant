# musicxml-abc-mcp Test Fixtures

## Fixture Files

This directory is intentionally sparse. The unit and protocol tests use inline
MusicXML/ABC strings defined directly in the test files.

Integration tests reuse the SATB MXL fixtures from `../omr-mcp/test_samples/pdmx_satb_samples/mxl/`.

## Running Integration Tests

```bash
cd musicxml-abc-mcp
VIRTUAL_ENV= .venv/bin/pytest tests/ -v -m integration
```

Integration tests require the omr-mcp fixture directory to exist at
`../omr-mcp/test_samples/pdmx_satb_samples/mxl/`. These files are part of the
omr-mcp development setup.
