# musicxml-abc-mcp — Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `uvx: command not found` | `uv` not installed | Re-run `install.sh` |
| Server not appearing in LLM client | Config JSON has a syntax error | Validate the JSON file (e.g. paste into jsonlint.com) |
| LLM client says "server disconnected" | Server crashed at startup | Open a terminal, run `uvx musicxml-abc-mcp` manually and read the error |
| Conversion loses dynamics or articulations | Expected — ABC format has limited expressive range | Check the `warnings` field in the tool response |
| ABC output fails to parse in other tools | Missing required ABC header | The `X:` field is required; report the exact error as a bug |
