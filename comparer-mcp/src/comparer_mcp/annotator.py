"""Colored MusicXML diff export for comparer-mcp (docs/PLAN.md Phase 4).

Colors the actual note objects compared by engine.compare_with_annotations()
via music21's note_obj.style.color (serialized as the standard MusicXML
`color` attribute on <note>), then re-exports both scores to MusicXML
strings. Two documents are produced — reference_annotated_musicxml shows
deletions and pre-change values, target_annotated_musicxml shows insertions
and post-change values — mirroring a standard two-pane diff.

Structural-only diffs (missing/extra parts or measures) have no note to
attach a color to and are not annotated here; see report.py for those.

Output is plain MusicXML with no MCP/rendering logic — an MCP client
chains export_annotated_musicxml straight into render-mcp's
render_to_pdf/render_to_image (both take a raw musicxml string) to actually
visualize the diff. comparer-mcp does not call render-mcp directly; the six
servers are independent (docs/architecture.md §2).
"""

from typing import Optional

from music21.musicxml.m21ToXml import GeneralObjectExporter

from comparer_mcp.engine import compare_with_annotations

COLORS = {
    "PITCH_CHANGE": "#FF8800",
    "DURATION_CHANGE": "#2266CC",
    "SUBSTITUTION": "#AA22AA",
    "INSERTION": "#22AA22",
    "DELETION": "#CC2222",
}


def _to_musicxml_string(score) -> str:
    return GeneralObjectExporter(score).parse().decode("utf-8")


def annotate(reference_xml: str, target_xml: str, options: Optional[dict] = None) -> dict:
    """Compare two MusicXML strings and return colored MusicXML for both.

    Returns:
        {
            "reference_annotated_musicxml": str,
            "target_annotated_musicxml": str,
            "similarity_score": float,
            "legend": {operation: "#RRGGBB", ...},
        }
    """
    result, reference_score, target_score, aligned_pairs = compare_with_annotations(
        reference_xml, target_xml, options
    )

    for _note_diff, aligned in aligned_pairs:
        color = COLORS.get(aligned.operation)
        if color is None:
            continue
        if aligned.reference is not None:
            aligned.reference.style.color = color
        if aligned.target is not None:
            aligned.target.style.color = color

    return {
        "reference_annotated_musicxml": _to_musicxml_string(reference_score),
        "target_annotated_musicxml": _to_musicxml_string(target_score),
        "similarity_score": result.similarity_score,
        "legend": dict(COLORS),
    }
