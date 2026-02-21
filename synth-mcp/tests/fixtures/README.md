# Test Fixtures

## Static fixtures

No committed fixtures yet. Integration tests use MXL files from the shared sample set:

```
../../omr-mcp/test_samples/pdmx_satb_samples/mxl/   # 10 SATB MusicXML files
```

## Generated fixtures

If a WAV fixture is needed for future tests, generate it from a sample MXL and commit it here.
Run integration tests first to produce one:

```bash
uv run pytest tests/ -v -m integration
```
