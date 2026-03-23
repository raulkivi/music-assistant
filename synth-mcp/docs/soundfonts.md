# Soundfonts

A soundfont is a file that contains recorded instrument samples — it tells the synthesiser what each note should sound like.

---

## Recommended free soundfonts

| Soundfont | Size | Quality | Notes |
|-----------|------|---------|-------|
| **TimGM6mb.sf2** | ~6 MB | Good enough for practice | Downloaded automatically by `install.sh` |
| **GeneralUser GS** | ~30 MB | Noticeably better | Free download, great balance of size and quality |
| **MuseScore General** | ~200 MB | Highest quality free option | Used by MuseScore; best for final-quality audio |

### TimGM6mb.sf2

Already on your system after running `install.sh`. No action needed.

### GeneralUser GS

Search for **"GeneralUser GS soundfont"** to find the download page, or look for `GeneralUser GS v1.471.sf2` (the filename may vary by version).

### MuseScore General

Search for **"MuseScore General soundfont"** or visit the MuseScore download page and look for the soundfont under Resources.

---

## Where to put the file

Place your soundfont in:

```
~/.local/share/sounds/sf2/
```

Create the directory if it doesn't exist:

```bash
mkdir -p ~/.local/share/sounds/sf2/
```

Then move or copy the `.sf2` file there, for example:

```bash
cp ~/Downloads/GeneralUser\ GS\ v1.471.sf2 ~/.local/share/sounds/sf2/
```

---

## How to configure synth-mcp

Open your LLM client config file and change the `SYNTH_SOUNDFONT_PATH` value to the full path of your new soundfont.

**Example — Claude Desktop** (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "synth": {
      "command": "uvx",
      "args": ["synth-mcp"],
      "env": {
        "SYNTH_SOUNDFONT_PATH": "~/.local/share/sounds/sf2/GeneralUser GS v1.471.sf2"
      }
    }
  }
}
```

The `SYNTH_SOUNDFONT_PATH` line is the only one you need to change — update it to match the exact filename you downloaded, then restart your LLM client.

For other clients (Cursor, Windsurf, VS Code + Continue, Zed) the same `SYNTH_SOUNDFONT_PATH` key applies — see [../SETUP.md](../SETUP.md) for the full config snippets.
