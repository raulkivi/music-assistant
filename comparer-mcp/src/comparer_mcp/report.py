"""Human-readable comparison report generation for comparer-mcp.

Pure function of ComparisonResult (docs/PLAN.md Phase 4): no MCP SDK
imports, no music21 imports — same isolation level as models.py. Groups
consecutive same-operation NoteDiffs per part into measure-range runs and
describes each run in plain English. When every PITCH_CHANGE in a run
shares the same interval_error (already computed per-note by engine.py),
it's reported as a transposition by N semitones rather than a generic
count — a claim grounded in data already on the NoteDiff, not inferred.

Deliberately does not attempt deeper semantic analysis (e.g. detecting
"added a descant") — see docs/PLAN.md "Changed decisions".
"""

from comparer_mcp.models import ComparisonResult, PartDiff

_OP_LABELS = {
    "DURATION_CHANGE": "rhythm change",
    "SUBSTITUTION": "note substituted",
    "INSERTION": "note added",
    "DELETION": "note removed",
}


def _headline(result: ComparisonResult) -> str:
    pct = round(result.similarity_score * 100)
    if pct >= 98:
        verdict = "nearly identical"
    elif pct >= 85:
        verdict = "minor differences"
    elif pct >= 60:
        verdict = "moderate differences"
    else:
        verdict = "substantial differences"
    return f"Overall similarity: {pct}% ({verdict})"


def _span(start: int, end: int) -> str:
    return f"measure {start}" if start == end else f"measures {start}–{end}"


def _plural(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"


def _describe_run(operation: str, items: list, start: int, end: int) -> str:
    count = len(items)
    span = _span(start, end)

    if operation == "PITCH_CHANGE":
        errors = {nd.interval_error for nd in items if nd.interval_error is not None}
        if len(errors) == 1:
            (semitones,) = errors
            if semitones:
                return f"transposed by {semitones} {_plural(semitones, 'semitone')} in {span}"
        return f"{count} {_plural(count, 'pitch change')} in {span}"

    label = _OP_LABELS.get(operation, "change")
    return f"{count} {_plural(count, label)} in {span}"


def _group_runs(note_diffs: list) -> list:
    non_match = sorted(
        (nd for nd in note_diffs if nd.operation != "MATCH"),
        key=lambda nd: (nd.measure_number, nd.beat),
    )
    runs = []
    for nd in non_match:
        if (
            runs
            and runs[-1]["operation"] == nd.operation
            and nd.measure_number - runs[-1]["end"] <= 1
        ):
            runs[-1]["end"] = nd.measure_number
            runs[-1]["items"].append(nd)
        else:
            runs.append(
                {"operation": nd.operation, "start": nd.measure_number, "end": nd.measure_number, "items": [nd]}
            )
    return runs


def _describe_part(part_diff: PartDiff) -> list:
    lines = []

    for number in part_diff.measures_missing:
        lines.append(f"measure {number} missing from target")
    for number in part_diff.measures_extra:
        lines.append(f"measure {number} added in target (not in reference)")

    for diff in part_diff.key_sig_diffs:
        target = diff.target_value if diff.target_value is not None else "(missing)"
        lines.append(f"key signature at measure {diff.measure_number}: {diff.reference_value} → {target}")

    for diff in part_diff.time_sig_diffs:
        target = diff.target_value if diff.target_value is not None else "(missing)"
        lines.append(f"time signature at measure {diff.measure_number}: {diff.reference_value} → {target}")

    all_note_diffs = [nd for md in part_diff.measure_diffs for nd in md.note_diffs]
    for run in _group_runs(all_note_diffs):
        lines.append(_describe_run(run["operation"], run["items"], run["start"], run["end"]))

    return lines


def generate_report(result: ComparisonResult) -> str:
    """Build a human-readable multi-line summary of a ComparisonResult."""
    lines = [_headline(result)]

    if result.summary.parts_missing:
        lines.append(f"Missing from target: {', '.join(result.summary.parts_missing)}")
    if result.summary.parts_extra:
        lines.append(f"Added in target: {', '.join(result.summary.parts_extra)}")

    for part_diff in result.part_diffs:
        part_lines = _describe_part(part_diff)
        if part_lines:
            lines.append(f"\n{part_diff.part_name}:")
            lines.extend(f"  - {line}" for line in part_lines)

    return "\n".join(lines)
