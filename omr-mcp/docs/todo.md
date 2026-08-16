# omr-mcp — Functional Gaps TODO

Found during a full six-server assessment pass (2026-08-16), reading `docs/requirements.md` and
source against actual behavior/test results. See `docs/HANDOVER.md` for the fuller narrative on the
SATB bug specifically; this file is the actionable checklist.

---

## Critical

- [ ] **SATB voice-loss in oemer output.** oemer reads multi-staff choir systems (4–5 simultaneous
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
      Options to investigate: pre-split the input image into per-staff-system strips before calling
      oemer; post-process the flat output to reconstruct `<part>`s from clef-alternation patterns;
      or evaluate Audiveris as a real fallback engine (currently deferred in PLAN.md Phase 4).

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
- [ ] Progress reporting (Phase 2, low priority per PLAN.md) — unimplemented.
- [ ] Audiveris fallback (Phase 4) — deferred; would also address the SATB item above if pursued.
