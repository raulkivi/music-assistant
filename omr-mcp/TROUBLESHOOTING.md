# omr-mcp — Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `uvx: command not found` | `uv` not installed | Re-run `install.sh` |
| Server not appearing in LLM client | Config JSON has a syntax error | Validate the JSON file (e.g. paste into [jsonlint.com](https://jsonlint.com)) |
| LLM client says "server disconnected" | Server crashed at startup | Open a terminal, run `uvx omr-mcp` manually and read the error |
| Server appears to hang on first use | Downloading ~100 MB of AI models on first run | Wait ~5 minutes; subsequent runs are fast |
| Output MusicXML looks wrong or empty | Low-quality or low-contrast input image | Use a high-contrast scan at ≥300 DPI |
| `oemer` not found at startup | Package not installed in venv | Re-run `install.sh` |
