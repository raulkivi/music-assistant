# render-mcp — Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `uvx: command not found` | `uv` not installed | Re-run `bash install.sh` |
| Server not appearing in LLM client | Config JSON has a syntax error | Validate the JSON file (e.g. paste into [jsonlint.com](https://jsonlint.com)) |
| LLM client says "server disconnected" | Server crashed at startup | Open a terminal, run `uvx render-mcp` and read the error |
| `libcairo` not found | System library missing | Run `sudo apt install libcairo2` |
| PDF is blank or corrupted | Invalid MusicXML input | Validate the MusicXML with another tool first |
| Only first page rendered | Multi-page rendering issue | Check server logs for errors |
