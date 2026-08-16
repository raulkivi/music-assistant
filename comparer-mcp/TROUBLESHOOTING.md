# comparer-mcp — Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `uvx: command not found` | `uv` not installed | Re-run `install.sh` |
| Server not appearing in LLM client | Config JSON has a syntax error | Validate the JSON file (e.g. paste into jsonlint.com) |
| LLM client says "server disconnected" | Server crashed at startup | Open a terminal, run `uvx comparer-mcp` manually and read the error |
| `error_code: INVALID_INPUT` on `compare_musicxml` | Input string is not MusicXML | Confirm the string contains a `<score-partwise>` or `<score-timewise>` root element |
| `error_code: FILE_NOT_FOUND` on `compare_musicxml_files` | Path doesn't exist or is relative to the wrong directory | Use an absolute path |
| `similarity_score` lower than expected | Parts matched positionally instead of by name, or measure numbers don't line up | Check `part_diffs[].measures_missing` / `measures_extra` first — a structural mismatch skews the score more than any single wrong note |
| `list_changes` returns nothing but you expect differences | The `part` filter is case-sensitive to spelling but not case; check it matches `part_diffs[].part_name` exactly, and that `measure_range` covers the right measures | Call `compare_musicxml` first and inspect `part_diffs[].part_name` |
| Comparison is slow on a large orchestral score | No hard timeout is enforced (see `docs/requirements.md` NFR-3) | Expected for large scores; consider `quick_similarity` first if you don't need note-level detail |
