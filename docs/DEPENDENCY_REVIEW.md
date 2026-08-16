# Dependency Review

Direct application dependencies for each MCP server, grouped by server. **Current** = version
resolved in that server's `uv.lock`. **Latest stable** = current PyPI release as of 2026-08-15.

## omr-mcp (v0.1.1)

| Package | Constraint | Current | Latest stable | Note |
|---|---|---|---|---|
| mcp | `>=1.28.1,<2.0.0` | 1.29.0 | 2.0.0 | Capped below 2.0 intentionally |
| oemer | `>=0.1.0` | 0.1.8 | 0.1.8 | up to date |
| onnxruntime | `==1.18.1` (pinned, CPU build) | 1.18.1 | 1.28.0 | Deliberately pinned — see below |
| opencv-python-headless | `==4.10.0.84` (pinned) | 4.10.0.84 | 5.0.0.93 | Deliberately pinned — opencv 5.x changed `cv2.HoughLinesP()` return shape, crashing oemer's staffline extraction |
| Pillow | `>=10.0.0` | 12.3.0 | 12.3.0 | up to date |
| defusedxml | `>=0.7.0` | 0.7.1 | 0.7.1 | up to date |

`onnxruntime-gpu` is explicitly excluded via `[tool.uv] override-dependencies` (an "impossible marker") so oemer's own unpinned dependency on it can't silently shadow the pinned CPU build.

## render-mcp (v0.1.1)

| Package | Constraint | Current | Latest stable | Note |
|---|---|---|---|---|
| mcp | `>=1.28.1,<2.0.0` | 1.29.0 | 2.0.0 | Capped below 2.0 |
| verovio | `>=3.0.0` | 6.2.1 | 6.2.1 | up to date |
| cairosvg | `>=2.7.0` | 2.9.0 | 2.9.0 | up to date |
| pypdf | `>=4.0.0` | 6.16.1 | 6.16.1 | up to date |
| Pillow | `>=10.0.0` | 12.3.0 | 12.3.0 | up to date |

## synth-mcp (v0.1.1)

| Package | Constraint | Current | Latest stable | Note |
|---|---|---|---|---|
| mcp | `>=1.28.1,<2.0.0` | 1.29.0 | 2.0.0 | Capped below 2.0 |
| music21 | `>=9.0.0` | 10.5.0 | 10.5.0 | up to date |
| pyfluidsynth | `>=1.3.0` | 1.4.0 | 1.4.0 | up to date |

## musicxml-abc-mcp (v0.1.1)

| Package | Constraint | Current | Latest stable | Note |
|---|---|---|---|---|
| mcp | `>=1.28.1,<2.0.0` | 1.29.0 | 2.0.0 | Capped below 2.0 |
| music21 | `>=9.0.0` | 10.5.0 | 10.5.0 | up to date |

## pitch-mcp (v0.1.1)

| Package | Constraint | Current | Latest stable | Note |
|---|---|---|---|---|
| mcp | `>=1.28.1,<2.0.0` | 1.29.0 | 2.0.0 | Capped below 2.0 |
| music21 | `>=9.0.0` | 10.5.0 | 10.5.0 | up to date |
| librosa | `>=1.0.0` | 1.0.0 | 1.0.0 | upgraded 2026-08-15 — see below |
| numpy | `>=1.24.0` | 2.4.6 / 2.5.2* | 2.5.2 | up to date |
| scipy | `>=1.10.0` | 1.17.1 / 1.18.0* | 1.18.0 | up to date |
| sounddevice | `>=0.4.0` | 0.5.5 | 0.5.5 | up to date |

\* two resolved versions in the lock — Python 3.11 vs 3.12 platform markers.

## comparer-mcp (v0.1.0)

| Package | Constraint | Current | Latest stable | Note |
|---|---|---|---|---|
| mcp | `>=1.28.1,<2.0.0` | 1.29.0 | 2.0.0 | Capped below 2.0 |
| music21 | `>=9.0.0` | 10.5.0 | 10.5.0 | up to date |

## Dev dependencies (shared across all six)

| Package | Constraint | Current | Latest stable | Note |
|---|---|---|---|---|
| pytest | `>=8.0.0` | 9.1.1 | 9.1.1 | up to date |
| pytest-asyncio | `>=0.23.0` | 1.4.0 | 1.4.0 | up to date |

## Release-note findings for updatable packages

Deep-dived the three packages with a real version gap, to see what upgrading would actually buy
each server.

### `mcp` 1.29.0 → 2.0.0 (all six servers) — **don't upgrade yet**

2.0.0 (released 2026-07-28) is a genuine breaking rewrite for the new stateless 2026-07-28 MCP
spec revision, not an additive bump:

- The decorator API (`@server.list_tools()`, `@server.call_tool()`) is **removed** for the
  low-level `Server` these six servers use — handlers move to constructor kwargs
  (`Server(on_list_tools=..., on_call_tool=...)`), all keyword-only.
- Implicit bare-dict/list return wrapping is gone — the `{"error": "...", "error_code": "..."}`
  convention used across all servers likely needs explicit wrapping.
- Tool exceptions now propagate as JSON-RPC errors instead of becoming
  `CallToolResult(is_error=True)` — changes error-handling semantics.
- `stdio_server()` uses private descriptors and changed POSIX child-process shutdown semantics.
- `mcp.types` split into a standalone `mcp-types` package; camelCase→snake_case field renames
  (`inputSchema`→`input_schema`, etc.).

Worth it eventually for: structured JSON-RPC errors, tool output-schema validation, progress
notifications, real request cancellation, elicitation/sampling, built-in OpenTelemetry tracing —
but that's a coordinated migration across all six servers, not a version-pin bump. v1.x is still
in maintenance with security fixes, so staying on `<2.0.0` is safe for now.
(Sources: [migration guide](https://py.sdk.modelcontextprotocol.io/migration/),
[v2.0.0 release notes](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0))

### `librosa` 0.11.0 → 1.0.0 (pitch-mcp) — **already at 1.0.0, verified working**

1.0.0 (2026-08-11) is explicitly an API-stabilization release, not a rewrite. Breaking changes are
all expired deprecations pitch-mcp doesn't touch: removed `audioread` backend (soundfile already
default), removed `filename=` kwarg on `librosa.stream` (not used — the real-time loop uses a
custom autocorrelation-YIN, not `librosa.stream`), removed `win_length` on `yin`/`pyin` (not passed
in `pitch_detector.py`). `librosa.pyin(...)` and `librosa.load(audio_path, sr=None, mono=True)` —
the two calls this server actually makes — are unaffected.

Relevant improvements: "improved accuracy for yin/pyin implementations," Viterbi-decoder
acceleration (pYIN's decode step), NumPy 2.0 and Python 3.14 support.

Turned out `pyproject.toml` already declares `librosa>=1.0.0` (committed in `45cd0b4`, the
pitch-mcp v0.2.0 release) — this predates this review and wasn't something done as part of it.
Verified directly: `uv sync --all-extras` installs librosa 1.0.0 into `.venv`, and the full
non-manual suite passes — **112 unit + 4 integration = 116 passed, 0 failed**. `requires-python`
is currently `>=3.12` in this file; whether that was changed specifically for librosa 1.0's Python
floor wasn't established here — treat that as unverified, not as a fact.

### `onnxruntime` (formerly pinned as `onnxruntime-gpu`) 1.18.1 → 1.28.0 (omr-mcp) — **stay pinned**

No evidence the ConvTranspose negative-pad strictness was ever relaxed — if anything it's gotten
*stricter* since. It isn't documented as an intentional validation change; v1.19.0's changelog
("expanded op support including ConvTranspose 3d") suggests it was a side effect of a bundled
shape-checker bump. v1.28.0's release notes show further hardening of the same code path
("Guarded `MlasConvPrepare`... and `ConvTranspose` pad computation with SafeInt", "Recovered
Conv/ConvTranspose rank from weights when input shape is unknown") — the opposite of a fix. No
session option was found to disable strict shape validation for this case.

Upgrades since 1.18.1 (cuDNN 8→9 support, optional cuDNN/cuFFT at runtime, quantization/prepacking
gains) mostly target transformer workloads and GPU inference — moot here since the server already
forces CPU-only execution. The only realistic path to unpinning is graph surgery: rewrite the
negative-pad ConvTranspose nodes in oemer's exported ONNX models (pad+slice equivalent), then
re-pin to a current release. Absent that work, keep the pin indefinitely.
(Sources: [v1.19.0](https://github.com/microsoft/onnxruntime/releases/tag/v1.19.0),
[v1.28.0](https://github.com/microsoft/onnxruntime/releases/tag/v1.28.0) release notes)
