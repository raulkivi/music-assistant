# synth-mcp — Troubleshooting

Quick reference for the most common problems. If your issue isn't listed here, open a terminal, run `uvx synth-mcp` manually, and read the error message it prints.

---

## Common problems (all servers)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `uvx: command not found` | `uv` not installed | Re-run `install.sh` |
| Server not appearing in LLM client | Config JSON has a syntax error | Validate the JSON file (e.g. paste into [jsonlint.com](https://jsonlint.com)) |
| LLM client says "server disconnected" | Server crashed at startup | Open a terminal, run `uvx synth-mcp` manually and read the error |

---

## synth-mcp specific problems

| Symptom | Cause | Fix |
|---------|-------|-----|
| No audio file produced | `SYNTH_SOUNDFONT_PATH` not set | Add the env var to the LLM client config (see [SETUP.md](SETUP.md)) |
| `libfluidsynth` not found | System library missing | Run `sudo apt install libfluidsynth-dev` |
| Synthesised audio sounds wrong | Wrong part selected or poor soundfont | Check part names in the MusicXML; see [docs/soundfonts.md](docs/soundfonts.md) |
