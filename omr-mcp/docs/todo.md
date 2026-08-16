# omr-mcp — Functional Gaps TODO

Found during a full six-server assessment pass (2026-08-16), reading `docs/requirements.md` and
source against actual behavior/test results. See `docs/HANDOVER.md` for the fuller narrative on the
SATB bug specifically; this file is the actionable checklist.

---

## Critical

- [x] **SATB voice-loss in oemer output.** oemer reads multi-staff choir systems (4–5 simultaneous
      staves) as one *sequential* melodic line instead of bracketing them into separate simultaneous
      `<part>`s. Confirmed via inspecting generated MusicXML: single `<part>`, single `<staff>`,
      single `<voice>` for the whole piece, with `<clef>` alternating `F4`↔`G2` repeatedly. This is
      real data loss (harmonic/vertical relationship between voices is gone), not a benign modeling
      difference, and it's an **upstream oemer limitation**, not a bug in this repo's wrapper
      (`src/omr_mcp/omr_engine.py`). Every ground-truth-accuracy integration test fails because of
      this. Blocks the actual "digitize a choir score" use case and anything downstream that needs
      multi-voice structure (comparer-mcp comparisons, per-voice synth-mcp audio).
      **Root cause confirmed 2026-08-16** (see the `Ave_verum_corpus_-_William_Byrd` crash below):
      `oemer/build_system.py::MeasureContainer.align_symbols()` hard-asserts `track_nums == 2` —
      its rhythm-alignment logic only supports 1 or 2 simultaneous tracks per staff-group. Scores
      that resolve to >2 tracks either crash (Byrd, 5 tracks) or — for pieces that don't crash —
      presumably get force-resolved to 1 track upstream in `further_infer_track_nums()`, which is
      exactly how they end up flattened into one sequential part. This is architectural, not a
      pinnable dependency issue: oemer's own pipeline assumes "at most a piano grand staff."
      **Test-fixture image quality ruled out as a contributing factor** (2026-08-16): the sample
      PNGs are generated at 150 DPI (below `requirements.md` NFR-1's 300+ floor), but re-rendering
      and re-running at 300 DPI produced an identical crash — oemer normalizes every input to a
      fixed internal pixel budget (`inference.py::resize_image()`) regardless of source resolution,
      so this is not an input-quality problem; see `docs/HANDOVER.md` for the full test.
      **Fixed 2026-08-16 via the Audiveris engine option** (`engine="audiveris"`), the third of the
      three options previously listed here (pre-split input, post-process flat output, or
      Audiveris) — see `docs/HANDOVER.md` "Audiveris engine option" for the full implementation and
      validation writeup. **Important nuance: `oemer` itself is unchanged and remains the default
      engine** — a caller that doesn't explicitly pass `engine="audiveris"` still gets the old
      flattened/crashing behavior. Checked off because the underlying capability gap (this server
      can correctly digitize a multi-staff choir score) is now closed, not because oemer's own bug
      was patched. Whether to flip the default or add auto-fallback detection is the next open
      question — see `docs/HANDOVER.md` "What You Need to Do".

## Hard-rule violation

- [x] **Missing `error_code` on primary tool error paths.** `recognize_sheet` /
      `recognize_sheet_to_file` error paths (in `omr_engine.py::recognize_image`,
      `recognize_image_to_file`, and the `except Exception` / base64-decode-failure branches in
      `server.py::call_tool`) returned bare `{"error": "..."}` without `error_code`. Fixed
      2026-08-16: all error returns now attach the appropriate code
      (`FILE_NOT_FOUND`, `UNSUPPORTED_FORMAT`, `INVALID_INPUT`, `PROCESSING_FAILED`), including the
      previously-unflagged `recognize_sheets` base64-resolution error branch.

## Docs/implementation drift

- [x] **`requirements.md` IR-2 vs. actual tool schema.** Docs described `recognize_sheet` inputs as
      `image_path` / `image_base64` / `mime_type` / `output_path`. The actual schema
      (`server.py::list_tools`) exposes `image` (auto-detected path-or-base64) / `format`
      (`"path"|"base64"` hint) — no `mime_type`, no `output_path` on this tool. Fixed 2026-08-16:
      reconciled IR-2 and IR-3 (which had the same `image_path`→`input_path` drift) to match the
      implementation, and corrected IR-6's error-code table (`INVALID_FORMAT` → `UNSUPPORTED_FORMAT`,
      added the `FILE_TOO_LARGE`/`INVALID_PARAMETER` codes that were already in use but undocumented).

## Known but lower priority

- [x] **2 of 4 CPDL fixtures crash inside oemer's own code** on this specific input data
      (`Ave_verum_corpus_-_William_Byrd`, `Locus_iste_-_Bruckner`). Same class of issue as the
      `bbox.py::find_lines()` crash already documented in `docs/HANDOVER.md` — oemer's own
      extraction code not handling a degenerate case, not fixable by a dependency pin.
      **Root-caused 2026-08-16** (see `docs/HANDOVER.md` for the full writeup):
      - Byrd's `AssertionError: 5` is the Critical SATB item above manifesting as a hard crash
        (`build_system.py::align_symbols()` asserts `track_nums == 2`; this piece has 5) — no
        separate fix needed, whatever fixes the Critical item fixes this too.
      - Bruckner's `IndexError: index 0 is out of bounds for axis 0 with size 0` is a distinct,
        narrower bug (`staffline_extraction.py::filter_line_peaks()` crashes on an empty-peaks
        zone after dewarping). Judged not worth a fragile monkeypatch of internal oemer functions
        for one fixture — left unfixed, reported here for whoever wants to file it upstream.
- [x] **Progress reporting (Phase 2, low priority per PLAN.md) — implemented 2026-08-16.**
      `server.py::_run_with_progress()` runs `recognize_image`/`recognize_image_to_file`/
      `recognize_images` off the event loop via `asyncio.to_thread`, and — when the client supplied
      an MCP `progressToken` — sends periodic `session.send_progress_notification()` heartbeats
      (elapsed-time based; oemer exposes no real percentage-complete callback) every 5s until the
      call finishes. As a side effect, the multi-minute oemer call no longer blocks the whole event
      loop synchronously (a latent issue, not previously flagged). Caught and fixed one regression
      this introduced along the way: `app.request_context` raises `LookupError` when there's no
      live MCP request (e.g. unit tests calling `call_tool()` directly) — guarded with try/except.
      A pre-existing test (`test_recognize_sheets_empty_list_returns_error`) had a weak
      `assert "error" in data` that silently passed even after that regression changed the actual
      error from `INVALID_PARAMETER`/"No images provided" to `PROCESSING_FAILED`/a `LookupError`
      message — tightened to assert the real `error_code` and message. 4 new tests in
      `TestRunWithProgress` (`tests/test_server.py`) cover the no-context, no-token,
      token-sends-heartbeats, and exception-propagation paths.
- [x] Audiveris fallback (Phase 4) — implemented 2026-08-16 as the fix for the Critical SATB item
      above (same change, not a separate one — see that item for the full writeup).
