# Sources & References

Useful references organised by topic.

---

## ABC Notation

| Resource | Description |
|----------|-------------|
| [ABC Notation (Wikipedia)](https://en.wikipedia.org/wiki/ABC_notation) | Overview and history |
| [abcnotation.com](https://abcnotation.com/) | Community hub, tutorials, and links |
| [ABC Standard v2.1](https://abcnotation.com/wiki/abc:standard:v2.1) | The standard used by most tools |
| [ABC Standard v2.2](https://abcnotation.com/wiki/abc:standard:v2.2) | Latest draft standard |
| [abcjs documentation](https://docs.abcjs.net/) | JavaScript ABC renderer/player |
| [ABC Tools (Michael Eskin)](https://michaeleskin.com/abctools/abctools.html) | Online editor, player, and converter |
| [VSCode ABC Music extension](https://marketplace.visualstudio.com/items?itemName=softaware.abc-music) | Syntax highlighting and preview in VSCode |

---

## MusicXML

| Resource | Description |
|----------|-------------|
| [MusicXML specification](https://www.musicxml.com/for-developers/) | Official spec and schema |
| [music21 documentation](https://web.mit.edu/music21/doc/) | Python toolkit used for MusicXML parsing and manipulation |

---

## Optical Music Recognition (omr-mcp)

| Resource | Description |
|----------|-------------|
| [oemer on GitHub](https://github.com/BreezeWhite/oemer) | OMR library used for sheet music recognition |
| [ONNX Runtime](https://onnxruntime.ai/) | Inference runtime for oemer's neural network models |

---

## Rendering (render-mcp)

| Resource | Description |
|----------|-------------|
| [Verovio](https://www.verovio.org/) | MusicXML/MEI → SVG engraving library |
| [verovio Python bindings](https://github.com/rism-digital/verovio/tree/develop/bindings/python) | Python interface to Verovio |
| [cairosvg](https://cairosvg.org/) | SVG → PDF/PNG conversion using libcairo |
| [pypdf](https://pypdf.readthedocs.io/) | PDF merging for multi-page output |

---

## Synthesis (synth-mcp)

| Resource | Description |
|----------|-------------|
| [FluidSynth](https://www.fluidsynth.org/) | Software MIDI synthesizer |
| [pyfluidsynth](https://github.com/nwhitehead/pyfluidsynth) | Python bindings for libfluidsynth |
| [GeneralUser GS / TimGM6mb soundfonts](https://musescore.org/en/handbook/3/soundfonts-and-sfz-files) | GM soundfonts available at `/usr/share/sounds/sf2/` |

---

## Pitch Detection (pitch-mcp)

| Resource | Description |
|----------|-------------|
| [librosa](https://librosa.org/doc/latest/index.html) | Audio analysis library; pYIN used for pitch tracking |
| [pYIN algorithm](https://doi.org/10.1109/ICASSP.2014.6853678) | Probabilistic YIN for pitch estimation (Mauch & Dixon, 2014) |
| [sounddevice](https://python-sounddevice.readthedocs.io/) | Real-time audio I/O (Phase B) |
| [YIN algorithm](http://audition.ens.fr/adc/pdf/2002_JASA_YIN.pdf) | Original YIN pitch detection paper (de Cheveigné & Kawahara, 2002) |

---

## MCP Framework

| Resource | Description |
|----------|-------------|
| [Model Context Protocol](https://modelcontextprotocol.io/) | MCP specification |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | Official Python SDK used by all servers |

---

## Tooling

| Resource | Description |
|----------|-------------|
| [uv](https://github.com/astral-sh/uv) | Fast Python package manager and venv tool |
| [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | Async test support for pytest |
