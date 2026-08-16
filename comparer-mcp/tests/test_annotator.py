"""Tests for comparer_mcp.annotator — colored MusicXML diff export."""

import pytest
from music21 import converter
from music21.musicxml.m21ToXml import GeneralObjectExporter
from music21 import meter, note, stream

from comparer_mcp.annotator import COLORS, annotate

_SATB_NOTES = [("C4", 1.0), ("D4", 1.0), ("E4", 1.0), ("F4", 1.0)]


def _score_xml(parts: dict) -> str:
    score = stream.Score()
    for part_name, notes in parts.items():
        part = stream.Part(id=part_name)
        part.partName = part_name
        part.append(meter.TimeSignature("4/4"))
        for pitch_name, ql in notes:
            part.append(note.Note(pitch_name, quarterLength=ql))
        score.insert(0, part)
    score.makeMeasures(inPlace=True)
    return GeneralObjectExporter(score).parse().decode("utf-8")


class TestAnnotate:
    def test_identical_scores_have_no_colored_notes(self):
        xml = _score_xml({"Soprano": _SATB_NOTES})

        result = annotate(xml, xml)

        ref_reparsed = converter.parseData(result["reference_annotated_musicxml"], format="musicxml")
        tgt_reparsed = converter.parseData(result["target_annotated_musicxml"], format="musicxml")
        assert all(n.style.color is None for n in ref_reparsed.recurse().notes)
        assert all(n.style.color is None for n in tgt_reparsed.recurse().notes)
        assert result["similarity_score"] == pytest.approx(1.0)

    def test_pitch_change_colors_both_sides(self):
        ref = _score_xml({"Soprano": _SATB_NOTES})
        changed = list(_SATB_NOTES)
        changed[0] = ("G4", 1.0)  # was C4
        tgt = _score_xml({"Soprano": changed})

        result = annotate(ref, tgt)

        ref_reparsed = converter.parseData(result["reference_annotated_musicxml"], format="musicxml")
        tgt_reparsed = converter.parseData(result["target_annotated_musicxml"], format="musicxml")

        ref_notes = list(ref_reparsed.recurse().notes)
        tgt_notes = list(tgt_reparsed.recurse().notes)

        assert ref_notes[0].style.color == COLORS["PITCH_CHANGE"]
        assert tgt_notes[0].style.color == COLORS["PITCH_CHANGE"]
        assert all(n.style.color is None for n in ref_notes[1:])
        assert all(n.style.color is None for n in tgt_notes[1:])

    def test_insertion_colors_only_target(self):
        # Split the last note into two within the same measure so the extra
        # note is an in-measure INSERTION, not a whole extra measure.
        ref = _score_xml({"Soprano": _SATB_NOTES})
        tgt_notes = _SATB_NOTES[:3] + [("F4", 0.5), ("G4", 0.5)]
        tgt = _score_xml({"Soprano": tgt_notes})

        result = annotate(ref, tgt)

        tgt_reparsed = converter.parseData(result["target_annotated_musicxml"], format="musicxml")
        notes = list(tgt_reparsed.recurse().notes)
        colors = {n.style.color for n in notes}
        assert COLORS["INSERTION"] in colors

    def test_deletion_colors_only_reference(self):
        ref_notes = _SATB_NOTES[:3] + [("F4", 0.5), ("G4", 0.5)]
        ref = _score_xml({"Soprano": ref_notes})
        tgt = _score_xml({"Soprano": _SATB_NOTES})

        result = annotate(ref, tgt)

        ref_reparsed = converter.parseData(result["reference_annotated_musicxml"], format="musicxml")
        notes = list(ref_reparsed.recurse().notes)
        colors = {n.style.color for n in notes}
        assert COLORS["DELETION"] in colors

    def test_legend_matches_colors(self):
        xml = _score_xml({"Soprano": _SATB_NOTES})
        result = annotate(xml, xml)
        assert result["legend"] == COLORS

    def test_options_are_applied_before_annotating(self):
        ref = _score_xml({"Soprano": _SATB_NOTES, "Alto": _SATB_NOTES})
        changed_alto = list(_SATB_NOTES)
        changed_alto[0] = ("G4", 1.0)
        tgt = _score_xml({"Soprano": _SATB_NOTES, "Alto": changed_alto})

        result = annotate(ref, tgt, options={"part_filter": ["Soprano"]})

        assert result["similarity_score"] == pytest.approx(1.0)
        ref_reparsed = converter.parseData(result["reference_annotated_musicxml"], format="musicxml")
        assert all(n.style.color is None for n in ref_reparsed.recurse().notes)


@pytest.mark.integration
class TestAnnotateRealFixtures:
    from pathlib import Path

    _SATB_MXL_DIR = (
        Path(__file__).parents[2] / "omr-mcp" / "test_samples" / "pdmx_satb_samples" / "mxl"
    )

    def test_annotates_real_score_diff(self):
        mxl_files = sorted(self._SATB_MXL_DIR.glob("*.mxl"))
        assert len(mxl_files) >= 2, f"Need at least 2 .mxl fixtures under {self._SATB_MXL_DIR}"

        ref_xml = converter.parse(str(mxl_files[0])).write("musicxml")
        ref_text = open(ref_xml, encoding="utf-8").read()
        tgt_xml = converter.parse(str(mxl_files[1])).write("musicxml")
        tgt_text = open(tgt_xml, encoding="utf-8").read()

        result = annotate(ref_text, tgt_text)

        assert "reference_annotated_musicxml" in result
        assert "target_annotated_musicxml" in result
        converter.parseData(result["reference_annotated_musicxml"], format="musicxml")
        converter.parseData(result["target_annotated_musicxml"], format="musicxml")
